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

import collections
import os
import re
from sqlalchemy import (Column, Unicode)
from sqlalchemy import event
from sqlalchemy.orm import validates
from aybu.manager.activity_log.fs import mkdir
from aybu.manager.exc import NotSupported
from . base import Base

Paths = collections.namedtuple('Paths', ['root', 'configs', 'sites',
                                         'archives', 'cgroups', 'logs', 'run',
                                         'virtualenv'])
LogPaths = collections.namedtuple('Logs', ['dir', 'emperor'])
SmtpConfig = collections.namedtuple('SmtpConfig', ['host', 'port'])
OsConf = collections.namedtuple('OsConf', ['user', 'group'])
__all__ = ['Environment']


class Environment(Base):

    __tablename__ = u'environments'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    name = Column(Unicode(64), primary_key=True)
    venv_name = Column(Unicode(64))
    name_re = re.compile(r'^[A-Za-z_][\w]*$')

    def _on_attr_update(self, value, oldvalue, attr, operation, error_msg):
        if not self.attribute_changed(value, oldvalue, attr):
            return

        raise NotSupported(operation, error_msg)

    def _on_name_update(self, value, oldvalue, initiator):
        self._on_attr_update(value, oldvalue, initiator,
                             'environment_change_name',
                             "Cannot change Environment name")

    def _on_venv_update(self, value, oldvalue, initiator):
        self._on_attr_update(value, oldvalue, initiator,
                             'environment_change_venv',
                             "Cannot change Environment virtualenv")
    @validates('name')
    def validate_name(self, key, name):
        if self.name_re.match(name) is None:
            raise ValueError("Invalid name {} for environmet".format(name))
        return name

    @classmethod
    def initialize(cls, settings, section='app:aybu-manager'):
        if section is None:
            cls.settings = settings
        else:
            cls.settings = settings[section]
        cls.log.debug("Initialized environment with config %s", settings)

    @classmethod
    def create(cls, session, name, venv_name=None, config=None):
        cls.log.debug("Creating environment %s", name)
        if not config is None:
            cls.initialize(config)

        try:
            # create the environment
            env = cls(name=name, venv_name=venv_name)
            session.add(env)
            root = env.paths.root

            paths = [p for k, p in env.paths._asdict().iteritems()
                           if k != 'root' and k != 'virtualenv' and root in p]
            paths.append(os.path.dirname(env.paths.configs))
            paths.append(env.paths.logs.dir)
            for path in sorted(paths):
                session.activity_log.add(mkdir, path, error_on_exists=False)

        except:
            session.rollback()
            raise
        else:
            return env

    def check_initialized(self):
        if not hasattr(self, 'settings') or not self.settings:
            self.log.error('%s has not been initialized', self)
            raise TypeError('%s class has not been initialized' % (self))

    @property
    def os_config(self):
        self.check_initialized()
        return OsConf(user=self.settings['os.user'],
                    group=self.settings['os.group'])

    @property
    def smtp_config(self):
        self.check_initialized()
        return SmtpConfig(host=self.settings['os.smtp_host'],
                            port=self.settings['os.smtp_port'])

    @property
    def paths(self):
        if hasattr(self, '_paths'):
            return self._paths

        self.check_initialized()
        join = os.path.join
        c = {k.replace('paths.', ''): self.settings[k]
             for k in self.settings if k.startswith('paths.')}
        configs = join(c['configs'], self.name)
        if self.venv_name:
            virtualenv = join(c['virtualenv'], self.venv_name)
        else:
            virtualenv = join(c['virtualenv'], self.name)


        self._paths = Paths(root=c['root'],
                            configs=configs,
                            sites=c['sites'],
                            archives=c['archives'],
                            cgroups=c['cgroups'],
                            logs=LogPaths(dir=c['logs'],
                                      emperor=join(c['logs'],
                                                   'uwsgi_emperor.log')),
                            run=c['run'],
                            virtualenv=virtualenv)

        return self._paths


    def __repr__(self):
        return '<Environment {self.name}>'.format(self=self)


event.listen(Environment.name, 'set', Environment._on_name_update)
event.listen(Environment.venv_name, 'set', Environment._on_venv_update)
