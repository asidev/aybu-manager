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
from sqlalchemy.pool import NullPool
from sqlalchemy.sql.expression import not_
from sqlalchemy.orm import (sessionmaker,
                            Session,
                            relationship,
                            backref,
                            validates)
from sqlalchemy.orm.exc import (DetachedInstanceError,
                                NoResultFound)
from sqlalchemy import event

import pwgen

import aybu.core.models
from aybu.core.models import Base as AybuCoreBase
from aybu.core.models import Setting as AybuCoreSetting
from aybu.core.models import Theme as AybuCoreTheme
from aybu.core.models import User as AybuCoreUser
from aybu.core.models import Group as AybuCoreGroup
from aybu.core.models import init_session_events as init_core_session_events
from aybu.core.proxy import Proxy
from aybu.manager.activity_log.template import render
from aybu.manager.activity_log.fs import mkdir, create, rm, rmtree, rmdir
from aybu.manager.activity_log.packages import install, uninstall
from aybu.manager.activity_log.database import create_database, drop_database
from aybu.manager.exc import OperationalError, NotSupported
from . base import Base
from . user import (User,
                    Group)
from . validators import (validate_hostname,
                          validate_language,
                          validate_password)


__all__ = ['Instance']
Paths = collections.namedtuple('Paths', ['config', 'vassal_config', 'dir',
                                         'cgroups', 'logs', 'socket', 'session',
                                         'data', 'mako_tmp_dir', 'cache',
                                         'domains_file', 'instance_dir',
                                         'nginx_config', 'wsgi_script',
                                         'virtualenv'])
LogPaths = collections.namedtuple('LogPaths', ['dir',
                                               'vassal',
                                               'application',
                                               'nginx'])
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

    @validates('domain')
    def validates_domain(self, key, domain):
        return validate_hostname(domain)

    @validates('default_language')
    def validates_language(self, key, lang):
        return validate_language(lang)

    @validates('database_password')
    def validates_database_password(self, key, pwd):
        return validate_password(pwd)

    @classmethod
    def get_by_domain(cls, session, domain):
        return cls.search(session,
                   filters=(Instance.domain == domain,),
                   return_query=True).one()

    def to_dict(self, paths=False):
        res = super(Instance, self).to_dict()
        if paths:
            for k, v in self.paths._asdict().iteritems():
                key = 'paths.{}'.format(k)
                if not isinstance(v, basestring):
                    v = ', '.join(v)
                res[key] = v
        res['created'] = str(res['created'])
        return res

    @property
    def python_name(self):
        return self.domain.replace(".","_").replace("-","_")

    @property
    def python_package_name(self):
        return 'aybu-instances-{}'.format(self.python_name).replace("_", "-")

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
            vassal_config=join(env.configs.uwsgi, "{}.ini".format(self.domain)),
            dir=dir_,
            cgroups=[join(ctrl, self.domain) for ctrl in env.cgroups],
            logs=LogPaths(
                      dir=join(env.logs.dir, self.domain),
                      nginx=join(env.logs.dir, self.domain, 'nginx.error.log'),
                      vassal=join(env.logs.dir, self.domain, 'uwsgi_vassal.log'),
                      application=join(env.logs.dir, self.domain,
                                       'application.log')),
            socket=join(env.run, "{}.socket".format(self.domain)),
            session=session_paths,
            data=data,
            mako_tmp_dir=join(cache, 'templates'),
            cache=cache,
            domains_file=join(dir_, 'domains.txt'),
            nginx_config=join(env.configs.nginx, '{}.conf'.format(self.domain)),
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

        settings = self.environment.settings
        if not settings:
            raise TypeError('Environment has not been configured')

        c = {k.replace('instance.database.', ''): settings[k]
             for k in settings if k.startswith('instance.database.')}
        type_ = c['type']
        database_user = "{}{}".format(c['prefix'], self.id)
        database_name = database_user
        database_port = c['port']
        driver = type_
        if 'driver' in c:
            driver = "{}+{}".format(driver, c['driver'])
        options = c['options'] if 'options' in c and c['options'] else None
        url = "{}://{}:{}@localhost:{}/{}".format(driver, database_user,
                                     self.database_password, database_port,
                                     database_name)
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
        self.log.debug("Creating SQLAlchemy engine (%s)",
                       self.database_config.sqlalchemy_url)
        self._database_engine = engine_from_config(
                    {'sqlalchemy.url': self.database_config.sqlalchemy_url,
                     'sqlalchemy.poolclass': NullPool},
                    'sqlalchemy.'
        )
        return self._database_engine

    @property
    def themes_chain(self):
        theme = self.theme
        while theme:
            yield theme
            theme = theme.parent

    def create_database_session(self, *args, **kwargs):
        if hasattr(self, "_database_session"):
            return self._database_session(*args, **kwargs)

        self.log.debug("Creating SQLAlchemy session for %s",
                       self.database_config.sqlalchemy_url)
        self._database_session = sessionmaker(bind=self.database_engine)
        return self._database_session(*args, **kwargs)

    def _write_uwsgi_conf(self, session=None, skip_rollback=False):
        session = session or Session.object_session(self)
        if session is None:
            raise DetachedInstanceError()
        session.activity_log.add(render, self, 'vassal.ini.mako',
                                 self.paths.vassal_config,
                                 deferred=True,
                                 skip_rollback=skip_rollback)
        session.activity_log.add(render, self, 'nginx_vhost.mako',
                                 self.paths.nginx_config,
                                 deferred=True,
                                 skip_rollback=skip_rollback)
        session.activity_log.add(render, self, 'domains.mako',
                                 self.paths.domains_file)
        self.environment.restart_services()

    def _rewrite_configuration(self, session=None):
        session = session or Session.object_session(self)
        if session is None:
            raise DetachedInstanceError()

        session.activity_log.add(rm, self.paths.config)
        session.activity_log.add(render, self, 'aybu.ini.mako',
                                 self.paths.config)
        if self.enabled:
            self.reload()

    def _create_python_package_paths(self, session):
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
                                 join(self.paths.instance_dir, "static"),
                                 recursive_delete=True)
        session.activity_log.add(mkdir,
                                 join(self.paths.instance_dir, "templates"),
                                 recursive_delete=True)
        uploads = join(self.paths.instance_dir, "static", "uploads")
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

    def _create_structure(self, session):
        paths = self.paths
        dirs = [paths.dir,
            paths.cache,
            paths.logs.dir,
            paths.mako_tmp_dir]
        dirs.extend(paths.cgroups)
        for dir_ in sorted(dirs):
            session.activity_log.add(mkdir, dir_)

        session.activity_log.add(render, self, 'aybu.ini.mako', paths.config)
        session.activity_log.add(render, self, 'main.py.mako', paths.wsgi_script,
                                 perms=0644)

    def _install_package(self, session):
        session.activity_log.add(install, self.paths.dir, self.paths.virtualenv,
                                 self.python_package_name)

    def _create_database(self, session):
        session.activity_log.add_group(create_database, session,
                                       self.database_config)
        self.log.info("Creating tables in instance database")
        AybuCoreBase.metadata.bind=self.database_engine
        AybuCoreBase.metadata.create_all(self.database_engine)

    def _populate_database(self, manager_session):
        session = self.create_database_session()
        try:
            init_core_session_events(session)
            source_ = pkg_resources.resource_stream('aybu.core.data',
                                                    'default_data.json')

            data = json.loads(source_.read())
            self.log.debug("Calling add_default_data")
            aybu.core.models.add_default_data(session, data)

            # copy admin users and owner to instance db.
            users = User.search(manager_session,
                                User.groups.any(Group.name == u'admin'))
            if self.owner not in users:
                users.append(self.owner)

            for user in users:
                self.log.debug("Adding user %s", user.email)
                core_user = AybuCoreUser(username=user.email,
                                         password=user.password)
                session.add(core_user)
                core_user.crypted_password = user.password

                for group in user.groups:
                    try:
                        core_group = AybuCoreGroup.get(session, group.name)

                    except NoResultFound:
                        core_group = AybuCoreGroup(name=group.name)
                        session.add(core_group)

                    core_user.groups.append(core_group)

            # modify settings for instance: debug and proxy support
            AybuCoreSetting.get(session, 'debug').raw_value = 'False'

            AybuCoreSetting.get(session, 'proxy_enabled').raw_value = \
                    self.environment.settings['proxy.enabled']
            AybuCoreSetting.get(session, 'proxy_port').raw_value = \
                    self.environment.settings['proxy.port']
            AybuCoreSetting.get(session, 'proxy_address').raw_value = \
                    self.environment.settings['proxy.address']

            # setup theme in aybu instance
            if self.theme:
                self.log.info("Using theme %s for instance", self.theme.name)
                for setting_name in ('banner_width', 'banner_height',
                                     'logo_width', 'logo_height',
                                     'main_menu_levels', 'template_levels',
                                     'image_full_size'):
                    setting = AybuCoreSetting.get(session, setting_name)
                    setting.value = getattr(self.theme, setting_name)
                setting = AybuCoreSetting.get(session, "theme_name")
                setting.value = self.theme.name

                theme = session.query(AybuCoreTheme)\
                        .filter(not_(AybuCoreTheme.children.any())).one()
                while theme:
                    parent = theme.parent
                    self.log.debug("removing theme: %s", theme.name)
                    theme.delete()
                    theme = parent
                session.flush()

                themes = []
                t = AybuCoreTheme(name=self.theme.name,
                          parent_name=self.theme.parent_name)
                themes.insert(0, t)
                parent = self.theme.parent
                while parent:
                    t = AybuCoreTheme(name=parent.name,
                                      parent_name=parent.parent_name)
                    themes.insert(0, t)
                    parent = parent.parent

                for theme in themes:
                    session.add(theme)
            session.flush()

        except:
            session.rollback()
            raise

        else:
            session.commit()

        finally:
            source_.close()
            session.close()

    def _enable(self):
        self.log.info("Enabling instance %s", self)
        session = Session.object_session(self)
        self._install_package(session)
        self._write_uwsgi_conf()

    def _disable(self):
        self.log.info("Disabling %s", self)
        session = Session.object_session(self)
        session.activity_log.add(rm, self.paths.vassal_config, deferred=True)
        session.activity_log.add(rm, self.paths.nginx_config, deferred=True)
        session.activity_log.add(uninstall, self.paths.dir,
                                self.paths.virtualenv,
                                self.python_package_name)
        self.environment.restart_services()

    def _on_environment_update(self, env, oldenv, attr):
        if not self.attribute_changed(env, oldenv, attr):
            return

        if self.enabled:
            raise OperationalError('Cannot change environment: '
                                   ' %s is enabled' % (self))

        self.log.info('Changing environment for instance %s to %s',
                      self, env)

        if hasattr(self, '_paths'):
            del self._paths

    def _on_domain_update(self, domain, olddomain, attr):
        self.log.debug("set on Instance.domain: %s => %s", domain, olddomain)
        if not self.attribute_changed(domain, olddomain, attr):
            return

        raise NotSupported('instance_update_domain',
                           'Cannot change the domain of an instance')

    def _on_theme_update(self, theme, oldtheme, attr):
        if not self.attribute_changed(theme, oldtheme, attr) or oldtheme is None:
            return

        raise NotImplementedError

    def _on_attr_update(self, value, oldvalue, attr):
        if not self.attribute_changed(value, oldvalue, attr) or oldvalue is None:
            return
        self._rewrite_configuration()

    def _on_toggle_status(self, value, oldvalue, attr):
        if not self.attribute_changed(value, oldvalue, attr):
            return

        if value:
            self._enable()
        else:
            self._disable()

    @classmethod
    def deploy(cls, session, domain, owner, environment,
               technical_contact, theme=None, default_language=u'it',
               database_password=None, enabled=True):

        if not database_password:
            database_password = pwgen.pwgen(16, no_symbols=True)

        try:
            cls.log.info("Deploying instance for %s in environment %s",
                         domain, environment)
            instance = cls(domain=domain, owner=owner, environment=environment,
                        theme=theme, technical_contact=technical_contact,
                        default_language=default_language,
                        database_password=database_password,
                        enabled=False)
            session.add(instance)
            session.flush()

            instance._create_structure(session)
            instance._create_python_package_paths(session)
            instance._create_database(session)
            instance._populate_database(session)
            instance.flush_cache()
            if enabled:
                instance.enabled = True

        except:
            session.rollback()
            raise

        else:
            return instance

    def reload(self):
        if not self.enabled:
            raise OperationalError('Cannot reload a disabled instance')
        self.log.info("Reloading %s", self)
        self._write_uwsgi_conf(skip_rollback=True)


    def delete(self, session=None):
        session = session or Session.object_session(self)
        if not session:
            raise DetachedInstanceError()

        self.log.info("Deleting %s", self)
        if self.enabled:
            raise OperationalError('Cannot delete an enabled instance')

        try:
            # TODO: flush
            session.activity_log.add_group(drop_database, session,
                                           self.database_config)

            session.activity_log.add(rm, self.paths.socket,
                                     error_on_not_exists=False)
            session.activity_log.add(rmtree, self.paths.logs.dir,
                                     error_on_not_exists=False)
            session.activity_log.add(rmtree, self.paths.dir,
                                     error_on_not_exists=False)
            for ctrl in self.paths.cgroups:
                session.activity_log.add(rmdir, ctrl,
                                         error_on_not_exists=False)

        except:
            session.rollback()
            raise

        else:
            session.query(self.__class__)\
                   .filter(self.__class__.id == self.id)\
                   .delete()


    def flush_cache(self):
        self.log.info("Flushing cache for %s", self)
        instance_session = self.create_database_session()
        try:
            request = collections.namedtuple('Request', ['db_session', 'host'])(
                db_session=instance_session,
                host="{}:80".format(self.domain)
            )
            proxy = Proxy(request)
            proxy.ban('^/.*')
        finally:
            instance_session.close()


event.listen(Instance.environment, 'set', Instance._on_environment_update)
event.listen(Instance.domain, 'set', Instance._on_domain_update)
event.listen(Instance.theme, 'set', Instance._on_theme_update)
event.listen(Instance.owner, 'set', Instance._on_attr_update)
event.listen(Instance.technical_contact, 'set', Instance._on_attr_update)
event.listen(Instance.default_language, 'set', Instance._on_attr_update)
event.listen(Instance.enabled, 'set', Instance._on_toggle_status)
