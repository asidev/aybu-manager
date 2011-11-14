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

import atexit
import collections
import datetime
import os
import pkg_resources
import uuid

from mako import Template
from sqlalchemy import (UniqueConstraint,
                        ForeignKey,
                        Column,
                        Boolean,
                        DateTime,
                        Integer,
                        Unicode)
from sqlalchemy.orm import relationship
from . base import Base


__all__ = ['Instance']
Paths = collections.namedtuple('Paths', ['config', 'vassal_config', 'dir',
                                         'cgroup', 'logs', 'socket', 'session',
                                         'data', 'mako_tmp_dir', 'cache',
                                         'virtualenv'])
LogPaths = collections.namedtuple('LogPaths', ['vassal', 'application'])
DataPaths = collections.namedtulple('DataPaths', ['dir', 'default'])
SessionConf = collections.namedtuple('SessionConf', ['data_dir', 'lock_dir',
                                                      'key', 'secret'])
DBConf = collections.namedtuple('DBConf', ['driver', 'user',
                                           'password', 'name', 'options'])


class IniRenderer(object):

    def __init__(self, instance, template_name, target):
        self.instance = instance
        self.template = Template(
            pkg_resources.resource_stream('aybu.manager.templates',
                                          template_name)
        )
        self.target = target

    def render(self):
        return self.template.render(instance=self.instance,
                                    os=self.instance.os_config,
                                    smtp=self.instance.environment.smtp_config)

    def write(self):
        with open(self.target, "w") as target:
            target.write(self.render())


class Instance(Base):

    __tablename__ = u'instances'
    __table_args__ = (UniqueConstraint(u'domain'),
                      {'mysql_engine': 'InnoDB'})

    id = Column(Integer, primary_key=True)
    domain = Column(Unicode(255))
    enabled = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.datetime.now)
    owner_email = Column(Unicode(255), ForeignKey('users.email',
                                            onupdate='cascade',
                                            ondelete='restrict'),
                         nullable=False)
    owner = relationship('User', backref='instances')

    environment_name = Column(Unicode(64), ForeignKey('environments.name',
                                                       onupdate='cascade',
                                                       ondelete='restrict'),
                              nullable=False)
    environment = relationship('Environment', backref='instances')

    theme_name = Column(Unicode(128), ForeignKey('theme.name',
                                                 onupdate='cascade',
                                                 ondelete='restrict'),
                        nullable=False)
    theme = relationship('Theme', backref='instances')

    technical_contact_email = Column(Unicode(255),
                                        ForeignKey('users.email',
                                                   onupdate='cascade',
                                                   ondelete='restrict'),
                                     nullable=False)
    technical_contact = relationship('User', backref='technical_contact_for',
            primaryjoin='User.email == Instance.technical_contact_email')

    default_language = Column(Unicode(2))
    database_password = Column(Unicode(32))


    def __init__(self, *args, **kwargs):
        super(Instance, self).__init__(*args, **kwargs)
        self.application_config = IniRenderer(self, 'aybu.ini.mako',
                                              self.paths.config)
        self.vassal_config = IniRenderer(self, 'vassal.ini.mako',
                                               self.paths.vassal_config)


    def __repr__(self):
        return "<Instance [{self.id}] {self.domain} (enabled: {self.enabled})>"\
                .format(self=self)

    @property
    def paths(self):
        if hasattr(self, '_paths'):
            return self._paths

        # setup atexit function to clean up temporary files
        atexit.register(pkg_resources.cleanup_resources)

        join = os.path.join
        env = self.environment.paths
        dir_= join(env.sites, self.domain)
        cache = join(dir_, 'cache')
        data_dir = join(pkg_resources.resource_filename('aybu.manager', 'data'))
        data = DataPaths(
            dir=data_dir,
            default=join(data_dir, 'default_json')
        )
        self._paths = Paths(
            vassal_config=join(env.configs, "{}.ini".format(self.domain)),
            dir=dir_,
            cgroup=join(env.cgroups, self.domain),
            config=join(dir_, 'production.ini'),
            logs=LogPaths(vassal=join(env.logs.dir, self.domain, 'uwsgi_vassal.log'),
                      application=join(env.logs.dir, self.domain,
                                       'application.log')),
            mako_tmp_dir=join(cache, 'templates'),
            data=data,
            virtualenv=env.virtualenv,
            socket=join(env.run, "{}.socket".format(self.domain)))
        return self._paths

    @property
    def session(self):
        if hasattr(self, '_session'):
            return self._session

        join = os.path.join
        paths = self.paths

        self._session = SessionConf(data_dir=join(paths.cache, "session_data"),
                                    lock_dir=join(paths.cache, "session_locks"),
                                    key=self.domain,
                                    secret=uuid.uuid4().hex)
        return self._session

    @property
    def database(self):
        if hasattr(self, '_database'):
            return self._database

        c = self.environment.config
        dbname = "{}__{}".format(c['database']['prefix'], self.id)
        self._database = DBConf(
            driver=c['database']['driver'],
            user=dbname,
            password=self.database_password,
            name=dbname
        )
        return self._database
