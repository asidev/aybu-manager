#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright 2010 Asidev s.r.l.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


import ConfigParser
import httplib2
import json
import os
import plac
import platform
import urllib
import zmq

DEF_CONFIGFILE="~/.aybu_manager_cli.conf"

class AybuManagerCliInterface(object):

    commands = ('instances', 'deploy', 'remove', 'enable', 'disable', 'flush',
                'reload', 'quit')

    @plac.annotations(
        configfile=('Path to the config file', 'option'),
        host=('HTTP ReST API address', 'option'),
        username=('username to use for authentication', 'option'),
        password=('password to use for authentication', 'option')
    )
    def __init__(self, configfile, host, username, password):
        self.configfile = configfile or '~/.aybu_manager_cli.conf'
        self.configfile = os.path.expanduser(self.configfile)
        self.username = username
        self.password = password
        self.host = host
        self.zmq_context = zmq.Context()
        self.zmq_response_socket = self.zmq_context.socket(zmq.SUB)
        self.zmq_response_socket.connect('tcp://localhost:8999')
        self.counter = 0
        self.__doc__ = "\nUse help to see subcommands"

    def __enter__(self):
        self.config = ConfigParser.ConfigParser()
        try:
            with open(self.configfile) as f:
                self.config.readfp(f)

        except IOError:
            pass

        if "http" not in self.config.sections():
            http_opts = dict()
        else:
            items = self.config.items('http')
            http_opts = dict(
              cache=items['cache'] if 'cache' in items else None,
              timeout=items['timeout'] if 'timeout' in items else None,
              disable_ssl_certificate_validation=\
                not items['verify_ssl'] if 'verify_ssl' in items else False
            )

        override = {}
        if self.username:
            override['username'] = self.username

        if self.password:
            override['password'] = self.password

        if self.host:
            override['host'] = self.host

        if 'remote' not in self.config.sections():
            try:
                self.username = self.config.get('remote', 'username', vars=override)
            except:
                pass

            try:
                self.password = self.config.get('remote', 'password', vars=override)
            except:
                pass

            try:
                self.host = self.config.get('remote', 'host',
                                                   vars=override)
            except:
                pass

        self.api = httplib2.Http(**http_opts)
        if self.username and self.password:
            self.api.add_credentials(self.username, self.password)

        print 'Connecting to {} as {}:{}'.format(self.host, self.username,
                                                 self.password)

        return self

    def __exit__(self, etype, exc, tb):
        "Will be called automatically at the end of the intepreter loop"
        if etype in (None, GeneratorExit):  # success
            print('quitting..')

    def quit(self):
        raise plac.Interpreter.Exit

    def request(self, url, method='GET', *args, **kwargs):
        if not self.host:
            raise ValueError("Remote host cannot be None")

        url = "{}{}".format(self.host, url)
        response, content = self.api.request(url, method, *args, **kwargs)
        try:
            content = json.loads(content)
        except:
            pass
        return response, content

    def post(self, url, data, method='POST', **kwargs):
        data = urllib.urlencode(data)
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        headers.update(kwargs.pop('headers', {}))
        return self.request(url, method='POST', body=data, headers=headers,
                            **kwargs)

    def put(self, url, data, **kwargs):
        return self.post(url, data, method='PUT', **kwargs)

    def delete(self, url, **kwargs):
        return self.request(url, method='DELETE', **kwargs)

    def head(self, url, **kwargs):
        return self.request(url, method='HEAD', **kwargs)

    def get(self, url, **kwargs):
        return self.request(url, method='GET', **kwargs)

    def instances(self):
        res, instances = self.get('/instances')
        yield instances

    def sync_command(self, action, *args, **kwargs):
        try:
            uuid = '{}.{}-{}'.format(platform.uname()[1], os.getpid(),
                                     self.counter)
            headers = {'X-Task-UUID': uuid}
            self.zmq_response_socket.setsockopt(zmq.SUBSCRIBE, uuid)
            res, content = action(*args, headers=headers, **kwargs)
            if res.status >= 300:
                raise Exception(res.status)


            print "Task {}: {}".format(res['x-task-uuid'], res['x-task-status'])

            if res['x-task-status'] == 'DEFERRED':
                return

            while True:
                print self.zmq_response_socket.recv_multipart()[1],

        except KeyboardInterrupt:
            pass

        except Exception as e:
            import logging
            logging.getLogger(__name__)
            logging.basicConfig(level=logging.DEBUG)
            logging.exception(e)

        finally:
            self.counter = self.counter + 1

    def deploy(self, domain, environment, owner, technical_contact,
               theme='', default_language='it', disabled=0):
        data=dict(
            domain=domain,
            environment_name=environment,
            owner_email=owner,
            technical_contact_email=technical_contact,
            theme=theme,
            default_language=default_language,
            enabled='true' if not disabled else '')
        self.sync_command(self.post, '/instances', data=data)

    def remove(self, domain):
        pass

    def enable(self, domain):
        pass

    def disable(self, domain):
        pass

    def flush(self, domain):
        pass

    def reload(self, domain):
        pass


def main():
    try:
        plac.Interpreter.call(AybuManagerCliInterface,
                            verbose=True, prompt='aybu> ')
    except KeyboardInterrupt:
        print "interrupted"


