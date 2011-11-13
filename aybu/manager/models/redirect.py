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

from sqlalchemy import (ForeignKey,
                        Column,
                        Integer,
                        Unicode)
from sqlalchemy.orm import relationship
from . base import Base


__all__ = ['Redirect']


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
