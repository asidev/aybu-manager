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
import json
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
from sqlalchemy import engine_from_config
from sqlalchemy.orm import (sessionmaker,
                            Session,
                            relationship,
                            backref)
import pwgen

import aybu.core.models
from aybu.core.models import Base as AybuCoreBase
from aybu.manager.activity_log.template import render
from aybu.manager.activity_log.fs import mkdir, create
from aybu.manager.activity_log.packages import install
from aybu.manager.activity_log.database import create_database
from . base import Base


__all__ = ['Instance']
Paths = collections.namedtuple('Paths', ['config', 'vassal_config', 'dir',
                                         'cgroup', 'logs', 'socket', 'session',
                                         'data', 'mako_tmp_dir', 'cache',
                                         'instance_dir', 'wsgi_script',
                                         'virtualenv'])
LogPaths = collections.namedtuple('LogPaths', ['dir', 'vassal', 'application'])
DataPaths = collections.namedtuple('DataPaths', ['dir', 'default'])
SessionPaths = collections.namedtuple('SessionPaths', ['data_dir', 'lock_dir'])
SessionConfig = collections.namedtuple('SessionConfig', ['paths', 'key',
                                                         'secret'])
DBConf = collections.namedtuple('DBConf', ['type', 'driver', 'user',
                                           'password', 'name', 'options',
                                           'sqlalchemy_url'])


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
                                                 ondelete='restrict'))
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
    def python_name(self):
        return self.domain.replace(".","_").replace("-","_")

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

        session_paths = SessionPaths(data_dir=join(cache, "session_data"),
                                    lock_dir=join(cache, "session_locks"))
        data = DataPaths(
            dir=data_dir,
            default=join(data_dir, 'default_json')
        )
        self._paths = Paths(
            config=join(dir_, 'production.ini'),
            vassal_config=join(env.configs, "{}.ini".format(self.domain)),
            dir=dir_,
            cgroup=join(env.cgroups, self.domain),
            logs=LogPaths(
                      dir=join(env.logs.dir, self.domain),
                      vassal=join(env.logs.dir, self.domain, 'uwsgi_vassal.log'),
                      application=join(env.logs.dir, self.domain,
                                       'application.log')),
            socket=join(env.run, "{}.socket".format(self.domain)),
            session=session_paths,
            data=data,
            mako_tmp_dir=join(cache, 'templates'),
            cache=cache,
            instance_dir=join(dir_, 'aybu', 'instances', self.python_name),
            wsgi_script=join(dir_, 'main.py'),
            virtualenv=env.virtualenv,
        )
        return self._paths

    @property
    def session_config(self):
        if hasattr(self, "_session_config"):
            return self._session_config

        self._session_config = SessionConfig(
                                paths = self.paths.session,
                                key=self.domain,
                                secret=uuid.uuid4().hex
        )
        return self._session_config



    @property
    def database_config(self):
        if hasattr(self, '_database_config'):
            return self._database_config

        c = self.environment.config
        if not c:
            raise TypeError('Environment has not been configured')

        type_ = c['database']['type']
        database_user = "{}{}".format(c['database']['prefix'], self.id)
        database_name = database_user
        driver = type_
        if 'driver' in c['database']:
            driver = "{}+{}".format(driver, c['database']['driver'])
        options = c['database']['options'] if 'options' in c['database'] \
                                           and c['database']['options'] \
                  else None
        url = "{}://{}:{}@localhost:3306/{}".format(driver, database_user,
                                     self.database_password, database_name)
        if options:
            url = "{}?{}".format(url, options)

        self._database_config = DBConf(
            driver=driver,
            type=type_,
            user=database_user,
            password=self.database_password,
            name=database_name,
            options=options,
            sqlalchemy_url=url
        )
        return self._database_config

    @property
    def database_engine(self):
        if hasattr(self, "_database_engine"):
            return self._database_engine
        self._database_engine = engine_from_config(
                    {'sqlalchemy.url': self.database_config.sqlalchemy_url},
                    'sqlalchemy.'
        )
        AybuCoreBase.metadata.bind=self._database_engine
        return self._database_engine


    def get_database_session(self):
        session = sessionmaker()()
        session.configure(bind=self.database_engine)
        return session

    def create_python_package_paths(self, session):
        base = self.paths.dir
        join = os.path.join
        # add recursive delete so that *.pyc files get erased too
        session.activity_log.add(mkdir, join(base, 'aybu'),
                                 recursive_delete=True)
        session.activity_log.add(mkdir, join(base, 'aybu', 'instances'),
                                 recursive_delete=True)
        session.activity_log.add(mkdir, self.paths.instance_dir,
                                 recursive_delete=True)
        session.activity_log.add(mkdir,
                                 join(self.paths.instance_dir, "public"),
                                 recursive_delete=True)
        session.activity_log.add(mkdir,
                                 join(self.paths.instance_dir, "templates"),
                                 recursive_delete=True)
        uploads = join(self.paths.instance_dir, "public", "uploads")
        session.activity_log.add(mkdir, uploads, recursive_delete=True)
        session.activity_log.add(render, self, 'setup.py.mako', join(base,
                                                               'setup.py'))
        session.activity_log.add(render, self, 'namespace_init.py.mako',
                                 join(base, 'aybu', '__init__.py'))
        session.activity_log.add(render, self, 'namespace_init.py.mako',
                                 join(base, 'aybu', 'instances',
                                      '__init__.py'))
        session.activity_log.add(create, join(self.paths.instance_dir,
                                              '__init__.py'), content="#")

    def create_structure(self, session):
        paths = self.paths
        dirs = sorted((paths.dir,
            paths.cgroup,
            paths.cache,
            paths.logs.dir,
            paths.mako_tmp_dir))
        for dir_ in dirs:
            session.activity_log.add(mkdir, dir_)

        session.activity_log.add(render, self, 'aybu.ini.mako', paths.config)
        session.activity_log.add(render, self, 'vassal.ini.mako',
                                 paths.vassal_config, deferred=True)
        session.activity_log.add(render, self, 'main.py.mako', paths.wsgi_script,
                                 perms=0644)
        self.create_python_package_paths(session)

    def install_package(self, session):
        session.activity_log.add(install, self.paths.virtualenv,
                                 self.python_name, self.paths.dir)

    def create_database(self, session):
        session.activity_log.add_group(create_database, session,
                                       self.database_config)
        self.log.info("Creating tables in instance database")
        AybuCoreBase.metadata.create_all(self.database_engine)

    def populate_database(self):
        session = self.get_database_session()
        data = json.loads(pkg_resources.resource_stream('aybu.manager.data',
                                                        'default_data.json')\
                          .read())
        # TODO: manipulate data to adjust settings, themes, user, etc
        aybu.core.models.add_default_data(session, data)
        session.commit()
        session.close()


    @classmethod
    def deploy(cls, session, domain, owner, environment,
               technical_contact, theme=None, default_language=u'it',
               database_password=None):

        if not database_password:
            database_password = pwgen.pwgen(16, no_symbols=True)

        try:
            instance = cls(domain=domain, owner=owner, environment=environment,
                        theme=theme, technical_contact=technical_contact,
                        default_language=default_language,
                        database_password=database_password)
            session.add(instance)
            session.flush()

            instance.create_structure(session)
            instance.install_package(session)
            instance.create_database(session)
            instance.populate_database()

        except:
            session.rollback()
            raise

        else:
            return instance

    def delete(self):
        session = Session.object_session(self)

        # disable instance
        # flush cache
        # drop database and user
        # remove files

