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

from sqlalchemy import (UniqueConstraint,
                        ForeignKey,
                        Column,
                        Boolean,
                        DateTime,
                        Integer,
                        Unicode)
from sqlalchemy.orm import (relationship,
                            backref)
import pwgen

from aybu.manager.activity_log.template import render
from aybu.manager.activity_log.fs import mkdir, create
from aybu.manager.activity_log.packages import install
from . base import Base


__all__ = ['Instance']
Paths = collections.namedtuple('Paths', ['config', 'vassal_config', 'dir',
                                         'cgroup', 'logs', 'socket', 'session',
                                         'data', 'mako_tmp_dir', 'cache',
                                         'instance_dir', 'wsgi_script',
                                         'virtualenv'])
LogPaths = collections.namedtuple('LogPaths', ['dir', 'vassal', 'application'])
DataPaths = collections.namedtuple('DataPaths', ['dir', 'default'])
SessionConf = collections.namedtuple('SessionConf', ['data_dir', 'lock_dir',
                                                      'key', 'secret'])
DBConf = collections.namedtuple('DBConf', ['type', 'driver', 'user',
                                           'password', 'name', 'options'])


class Instance(Base):

    __tablename__ = u'instances'
    __table_args__ = (UniqueConstraint(u'domain'),
                      {'mysql_engine': 'InnoDB'})

    id = Column(Integer, primary_key=True)
    domain = Column(Unicode(255), nullable=False)
    enabled = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.datetime.now)
    owner_email = Column(Unicode(255), ForeignKey('users.email',
                                            onupdate='cascade',
                                            ondelete='restrict'),
                         nullable=False)
    owner = relationship('User',
                         backref=backref('instances'),
                         primaryjoin='User.email == Instance.owner_email')

    environment_name = Column(Unicode(64), ForeignKey('environments.name',
                                                       onupdate='cascade',
                                                       ondelete='restrict'),
                              nullable=False)
    environment = relationship('Environment', backref='instances')

    theme_name = Column(Unicode(128), ForeignKey('themes.name',
                                                 onupdate='cascade',
                                                 ondelete='restrict'),
                        nullable=False)
    theme = relationship('Theme', backref='instances')

    technical_contact_email = Column(Unicode(255),
                                        ForeignKey('users.email',
                                                   onupdate='cascade',
                                                   ondelete='restrict'),
                                     nullable=False)
    technical_contact = relationship('User',
                                     backref=backref('technical_contact_for'),
                primaryjoin='Instance.technical_contact_email == User.email')

    default_language = Column(Unicode(2), default=u'it')
    database_password = Column(Unicode(32))

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
            wsgi_script=join(dir_, 'main.py'),
            logs=LogPaths(
                      dir=join(env.logs.dir, self.domain),
                      vassal=join(env.logs.dir, self.domain, 'uwsgi_vassal.log'),
                      application=join(env.logs.dir, self.domain,
                                       'application.log')),
            cache=cache,
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
    def database_user(self):
        if self.id is None:
            raise ValueError('instance id does not exist yet.')
        return "{}{}".format(self.environment.config['database']['prefix'],
                             self.id)

    @property
    def database_name(self):
        return self.database_user


    @property
    def database(self):
        if hasattr(self, '_database'):
            return self._database

        c = self.environment.config
        if not c:
            raise TypeError('Environment has not been configured')

        type_ = c['database']['type']
        driver = type_
        if 'driver' in c['database']:
            driver = "{}+{}".format(driver, c['database']['driver'])

        self._database = DBConf(
            driver=driver,
            type=type_,
            user=self.database_user,
            password=self.database_password,
            name=self.database_name
        )
        return self._database

    def create_package(self, session):
        base = self.paths.dir
        join = os.path.join
        session.activity_log.add(mkdir, join(base, 'aybu'))
        session.activity_log.add(mkdir, join(base, 'instances'))
        inst_dir = join(base, 'instances', 'self.name')
        session.activity_log.add(mkdir, inst_dir)
        session.activity_log.add(mkdir, join(inst_dir, "public"))
        session.activity_log.add(mkdir, join(inst_dir, "templates"))
        uploads = join(inst_dir, "public", "uploads")
        session.activity_log.add(mkdir, uploads)
        for dir_ in ('banners', 'files', 'logo', 'images'):
            session.activity_log.add(mkdir, join(uploads, dir_))

        session.activity_log.add(render, 'setup.py.mako', join(base,
                                                               'setup.py'))
        session.activity_log.add(render, 'namespace_init.py.mako',
                                 join(base, 'aybu', '__init__.py'))
        session.activity_log.add(render, 'namespace_init.py.mako',
                                 join(base, 'aybu', 'instances',
                                      '__init__.py'))
        session.activity_log.add(create, join(inst_dir, '__init__.py'),
                                 content="#")

    def create_structure(self, session):
        paths = self.paths
        dirs = sorted(paths.dir,
            paths.cgroup,
            paths.cache,
            paths.logs.dir,
            paths.mako_tmp_dir)
        for dir_ in dirs:
            session.activity_log.add(mkdir, dir_)

        session.activity_log.add(render, 'aybu.ini.mako', paths.config)
        session.activity_log.add(render, 'vassal.ini.mako',
                                 paths.vassal_config, perms=0644, deferred=True)
        session.activity_log.add(render, 'main.py.mako', paths.wsgi_script,
                                 perms=0644)

    def install_package(self, session):
        session.activity_log.add(install, self.paths.virtualenv,
                                 self.domain, self.paths.dir)

    def create_database(self, session, password):
        pass

    def populate_database(self, session):
        pass

    @classmethod
    def deploy(cls, session, name, owner, environment, theme,
               technical_contact, default_language=u'it',
               database_password=None):

        if not database_password:
            database_password = pwgen(16, no_symbols=True)

        instance = cls(name=name, owner=owner, environment=environment,
                       theme=theme, technical_contact=technical_contact,
                       default_language=default_language,
                       database_password=database_password)
        session.add(instance)
        session.flush()

        instance.create_structure(session)
        instance.create_package(session)
        instance.install_package(session)
        instance.create_database(session, database_password)
        instance.populate_database(session)
        return instance
