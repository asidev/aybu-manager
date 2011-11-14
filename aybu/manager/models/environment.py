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
from . base import Base
from sqlalchemy import (Column, Unicode)


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
    config = None

    @classmethod
    def init(cls, config):
        cls.config = config

    def os_config(self):
        try:
            return OsConf(user=self.config['os']['user'],
                        group=self.config['os']['group'])
        except AttributeError:
            raise TypeError('Environment class ha not been initialized')


    @property
    def smtp_config(self):
        return SmtpConfig(host=self.config['os']['smtp_host'],
                          port=self.config['os']['smtp_port'])


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
                            logs=Logs(dir=c['logs'],
                                      emperor=join(c['logs'],
                                                   'uwsgi_emperor.log')),
                            run=c['run'],
                            virtualenv=c['virtualenv'])
        return self._paths


    def __repr__(self):
        return '<Environment «{self.name}»>'.format(self=self)
