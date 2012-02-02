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
from sqlalchemy import event

from . base import Base
from . validators import (validate_hostname,
                          validate_redirect_http_code,
                          validate_redirect_target_path)
from . instance import Instance


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

    @classmethod
    def after_init(cls, self, args, kwargs):
        if self.instance:
            self.instance.rewrite_nginx_conf()
            self.log.debug("Created redirect %s: rewriting nginx conf for %s",
                          self, self.instance)
        else:
            self.log.debug("redirect has not instance attached")

    def _on_attr_update(self, value, oldvalue, attr):
        if not self.attribute_changed(value, oldvalue, attr):
            return

        if self.instance:
            self.log.debug("Attribute %s changed (%s => %s) on %s: "
                           "rewriting nginx conf for %s",
                           attr, oldvalue, value, self, self.instance)
            self.instance.rewrite_nginx_conf()

    def _on_instance_update(self, instance, oldinstance, attr):
        if not self.attribute_changed(instance, oldinstance, attr):
            return

        self.log.debug("Instance changed, rewriting both nginx conf")
        if instance:
            instance.rewrite_nginx_conf()
        if oldinstance and isinstance(oldinstance, Instance):
            oldinstance.rewrite_nginx_conf()

    def delete(self, session=None):
        instance = self.instance
        super(Redirect, self).delete(session)
        instance.rewrite_nginx_conf()

    def __repr__(self):
        target = "{}{}".format(self.instance.domain, self.target_path)
        return '<Redirect {self.source} => {target} (code: {self.http_code})>'\
                .format(target=target, self=self)


event.listen(Redirect, 'init', Redirect.after_init)
event.listen(Redirect.source, 'set', Redirect._on_attr_update)
event.listen(Redirect.instance, 'set', Redirect._on_instance_update)
event.listen(Redirect.http_code, 'set', Redirect._on_attr_update)
event.listen(Redirect.target_path, 'set', Redirect._on_attr_update)


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
