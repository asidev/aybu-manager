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
from sqlalchemy.orm import (relationship,
                            validates)

from . base import Base
from . validators import (validate_hostname,
                          validate_redirect_http_code,
                          validate_redirect_target_path)


__all__ = ['Redirect', 'Alias']


class Redirect(Base):

    __tablename__ = u'redirects'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    source = Column(Unicode(256), primary_key=True)
    instance_id = Column(Integer,
                         ForeignKey('instances.id',
                                    onupdate='cascade',
                                    ondelete='cascade'),
                         nullable=False
    )
    instance = relationship('Instance', backref='redirects')
    target_path = Column(Unicode(256), default=u'', nullable=False)
    http_code = Column(Integer, default=301, nullable=False)

    def to_dict(self):
        res = super(Redirect, self).to_dict()
        res['destination'] = self.instance.domain
        return res

    @validates('source')
    def validate_source(self, key, source):
        return validate_hostname(source)

    @validates('target_path')
    def validate_target_path(self, key, target_path):
        return validate_redirect_target_path(target_path)

    @validates('http_code')
    def validates_http_code(self, key, http_code):
        return validate_redirect_http_code(http_code)

    def __repr__(self):
        target = "{}{}".format(self.instance.domain, self.target_path)
        return '<Redirect {self.source} => {target} (code: {self.http_code})>'\
                .format(target=target, self=self)


class Alias(Base):

    __tablename__ = u'aliases'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    domain = Column(Unicode(256), primary_key=True)
    instance_id = Column(Integer,
                         ForeignKey('instances.id',
                                    onupdate='cascade',
                                    ondelete='cascade'),
                         nullable=False
    )
    instance = relationship('Instance', backref='aliases')

    @validates('source')
    def validate_source(self, key, source):
        return validate_hostname(source)

    def __repr__(self):
        return '<Alias {self.domain} for {self.instance.domain}>'\
                .format(self=self)

