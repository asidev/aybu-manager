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
import datetime
import os
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
Paths = collections.namedtuple('Paths', ['config', 'dir', 'cgroup', 'logs',
                                         'socket'])
Logs = collections.namedtuple('Logs', ['vassal', 'application'])


class Instance(Base):

    __tablename__ = u'instances'
    __table_args__ = (UniqueConstraint(u'domain'),
                      {'mysql_engine': 'InnoDB'})

    id = Column(Integer, primary_key=True)
    domain = Column(Unicode(255))
    enabled = Column(Boolean, default=True)
    created = Column(DateTime, default=datetime.datetime.now)
    owner_username = Column(Unicode(255), ForeignKey('users.username',
                                            onupdate='cascade',
                                            ondelete='restrict'))
    owner = relationship('User', backref='instances')
    environment_name = Column(Unicode(64), ForeignKey('environments.name',
                                                       onupdate='cascade',
                                                       ondelete='restrict'))
    environment = relationship('Environment', backref='instances')
    theme_name = Column(Unicode(128), ForeignKey('theme.name',
                                                 onupdate='cascade',
                                                 ondelete='restrict'))
    theme = relationship('Theme', backref='instances')

    def __repr__(self):
        return "<Instance [{self.id}] {self.domain} (enabled: {self.enabled})>"\
                .format(self=self)

    @property
    def paths(self):
        if hasattr(self, '_paths'):
            return self._paths

        join = os.path.join
        env = self.environment.paths
        self._paths = Paths(
            config=join(env.configs, "{}.ini".format(self.domain)),
            dir=join(env.sites, self.domain),
            cgroup=join(env.cgroups, self.domain),
            logs=Logs(vassal=join(env.logs.dir, self.domain, 'uwsgi_vassal.log'),
                      application=join(env.logs.dir, self.domain,
                                       'application.log')),
            socket=join(env.run, "{}.socket".format(self.domain)))
        return self._paths



