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
import pkg_resources
from sqlalchemy import (Column,
                        Integer,
                        Unicode,
                        event,
                        func)
from sqlalchemy.orm import (Session,
                            validates)
from aybu.manager.activity_log.fs import mkdir
from aybu.manager.activity_log.command import command
from aybu.manager.activity_log.template import render
from aybu.manager.exc import NotSupported
from . base import Base
from . validators import validate_name

Paths = collections.namedtuple('Paths', ['root', 'configs', 'sites',
                                         'archives', 'cgroups', 'logs', 'run',
                                         'themes', 'virtualenv'])
LogPaths = collections.namedtuple('Logs', ['dir', 'emperor'])
SmtpConfig = collections.namedtuple('SmtpConfig', ['host', 'port'])
OsConf = collections.namedtuple('OsConf', ['user', 'group'])
ConfigDirs = collections.namedtuple('ConfigDirs',
                                    ['dir', 'uwsgi', 'nginx',
                                     'supervisor_dir', 'supervisor_conf'])
UWSGIConf = collections.namedtuple('UWSGIConf', ['subscription_server',
                                                 'fastrouter', 'bin'])
Address = collections.namedtuple('Address', ['address', 'port'])

__all__ = ['Environment']


class Environment(Base):

    __tablename__ = u'environments'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    name = Column(Unicode(64), primary_key=True)
    venv_name = Column(Unicode(64))
    id = Column(Integer, unique=True)

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
        return validate_name(name)

    @classmethod
    def initialize(cls, settings, section=None):
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
            if venv_name is None:
                venv_name = cls.settings['paths.virtualenv.default']

            max_id = session.query(func.max(cls.id)).one()[0]
            id_ = max_id + 1 if max_id else 1

            # create the environment
            env = cls(name=name, venv_name=venv_name, id=id_)
            session.add(env)
            root = env.paths.root

            paths = [p for k, p in env.paths._asdict().iteritems()
                           if k != 'root' and k != 'virtualenv' and root in p
                           and k != 'configs']
            paths.append(env.paths.configs.dir)
            paths.append(os.path.dirname(env.paths.configs.uwsgi))
            paths.append(env.paths.configs.uwsgi)
            paths.append(env.paths.configs.nginx)
            paths.append(env.paths.configs.supervisor_dir)
            paths.append(env.paths.logs.dir)
            cls.log.error("paths: %s", paths)
            for path in sorted(paths):
                session.activity_log.add(mkdir, path, error_on_exists=False)

            session.activity_log.add(render, 'supervisor.conf.mako',
                                     env.paths.configs.supervisor_conf,
                                     env=env, uwsgi=env.uwsgi_config)
            sup_update_cmd = cls.settings.get('supervisor.update.cmd', None)
            if sup_update_cmd:
                session.activity_log.add(command, sup_update_cmd,
                                         oncommit=True, on_rollback=True)

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
    def uwsgi_config(self):
        self.check_initialized()
        frp = int(self.settings['uwsgi.fastrouter.base_port']) + self.id
        sp = int(self.settings['uwsgi.subscription_server.base_port']) + self.id

        fr = Address(address=self.settings['uwsgi.fastrouter.address'],
                     port=frp)
        ss = Address(address=self.settings['uwsgi.subscription_server.address'],
                     port=sp)
        bin_ = self.settings.get('uwsgi.bin', 'uwsgi')
        return UWSGIConf(fastrouter=fr, subscription_server=ss, bin=bin_)

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
        virtualenv = join(c['virtualenv.base'], self.venv_name)

        cgroups_base_path = c['cgroups']
        cgroups_rel_path = c['cgroups.relative_path']
        if cgroups_rel_path.startswith('/'):
            cgroups_rel_path = cgroups_rel_path[1:]

        cgroups_controllers = c.get('cgroups.controllers', None)

        if cgroups_controllers:
            cgroups_controller = [ctrl.strip() for ctrl in
                                  cgroups_controllers.split(',')]
            cgroups = [join(cgroups_base_path, ctrl, cgroups_rel_path)
                    for ctrl in cgroups_controller]

        else:
            cgroups = [join(cgroups_base_path, cgroups_rel_path)]

        themes = os.path.realpath(
            pkg_resources.resource_filename(
                'aybu.themes.base', 'static'
            )).replace('/base/static', '')

        configs = ConfigDirs(uwsgi=join(c['configs.uwsgi'], self.name),
                             nginx=c['configs.nginx'],
                             supervisor_dir=c['configs.supervisor'],
                             supervisor_conf=join(c['configs.supervisor'],
                                                  "{}.conf".format(self.name)),
                             dir=c['configs'])

        log = join(c['logs'], "{}_emperor.log".format(self.name))
        self._paths = Paths(root=c['root'],
                            configs=configs,
                            sites=c['sites'],
                            themes=themes,
                            archives=c['archives'],
                            cgroups=cgroups,
                            logs=LogPaths(dir=c['logs'],
                                      emperor=log),
                            run=c['run'],
                            virtualenv=virtualenv)

        return self._paths

    def to_dict(self, paths=False, instances=False):
        res = super(Environment, self).to_dict()
        if paths:
            for k, v in self.paths._asdict().iteritems():
                key = 'paths.{}'.format(k)
                if not isinstance(v, basestring):
                    v = ', '.join(v)
                res[key] = v
        if instances:
            res['instances'] = [i.domain for i in self.instances]
        return res

    def restart_services(self):
        try:
            restart_cmd = self.settings['nginx.restart.cmd']
            session = Session.object_session(self)
            session.activity_log.add(command, restart_cmd, on_commit=True,
                                     on_rollback=True)

        except KeyError:
            pass

    def __repr__(self):
        return '<Environment {self.name}>'.format(self=self)


event.listen(Environment.name, 'set', Environment._on_name_update)
event.listen(Environment.venv_name, 'set', Environment._on_venv_update)
