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

import os
import collections
import logging
import sqlalchemy.ext.declarative
from sqlalchemy import (UniqueConstraint,
                        ForeignKey,
                        Column,
                        Boolean,
                        Integer,
                        Unicode)
from sqlalchemy.orm import relationship



Paths = collections.namedtuple('Paths', ['root', 'configs', 'sites',
                                         'archives', 'cgroups', 'logs', 'run'])
__all__ = ['Base', 'Instance', 'Environment', 'Redirect']


class AybuManagerBase(object):

    @property
    def log(self):
        if hasattr(self, '_log'):
            return self._log

        self._log = logging.getLogger("{}.{}".format(self.__module__,
                                                     self.__class__.__name__))
        return self._log


Base = sqlalchemy.ext.declarative.declarative_base(cls=AybuManagerBase)


class Instance(Base):

    __tablename__ = u'instances'
    __table_args__ = (UniqueConstraint(u'domain'),
                      {'mysql_engine': 'InnoDB'})

    id = Column(Integer, primary_key=True)
    domain = Column(Unicode(255))
    enabled = Column(Boolean, default=True)
    environment_name = Column(Unicode(256), ForeignKey('environments.name',
                                                       onupdate='cascade',
                                                       ondelete='restrict'))
    environment = relationship('Environment', backref='instances')

    def __repr__(self):
        return "<Instance [{self.id}] {self.domain} (enabled: {self.enabled})>"\
                .format(self=self)


class Environment(Base):

    __tablename__ = u'environments'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    name = Column(Unicode(64), primary_key=True)
    config = None

    @classmethod
    def init(cls, config):
        cls.config = config

    @property
    def paths(self):
        if hasattr(self, '_paths'):
            return self._paths

        if not self.config:
            raise TypeError('Environment class has not been initialized')

        join = os.path.join
        c = self.config['paths']
        configs = join(c['configs'], self.name)


        self._paths = Paths(root=c['root'],
                            configs=configs,
                            sites=c['sites'],
                            archives=c['archives'],
                            cgroups=c['cgroups'],
                            logs=c['logs'],
                            run=c['run'])
        return self._paths


    def __repr__(self):
        return '<Environment «{self.name}»>'.format(self=self)


class Redirect(Base):

    __tablename__ = u'redirects'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    source = Column(Unicode(256), primary_key=True)
    instance_id = Column(Integer, ForeignKey('instances.id',
                                             onupdate='cascade',
                                             ondelete='cascade'))
    instance = relationship('Instance', backref='redirects')
    target_path = Column(Unicode(256))
    http_code = Column(Integer, default=301)

    def __repr__(self):
        target = "{}{}".format(self.instance.domain, self.target_path)
        return '<Redirect {self.source} => {target} (code: {self.http_code})>'\
                .format(target=target, self=self)
