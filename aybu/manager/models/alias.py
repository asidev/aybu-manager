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
from . validators import validate_hostname
from . instance import Instance


__all__ = ['Alias']


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
    instance = relationship('Instance', backref='aliases', lazy="joined")

    @validates('source')
    def validate_source(self, key, source):
        return validate_hostname(source)

    @classmethod
    def after_init(cls, self, args, kwargs):
        if self.instance and self.instance.enabled:
            self.instance.rewrite()
            self.log.debug("Created alias %s: rewriting nginx conf for %s",
                          self, self.instance)
        elif not self.instance:
            self.log.debug("alias has no instance attached")
        else:
            self.log.debug("alias instance is not enabled")

    def _on_domain_update(self, value, oldvalue, attr):
        if not self.attribute_changed(value, oldvalue, attr):
            return

        if self.instance:
            self.log.debug("Attribute %s changed (%s => %s) on %s: "
                           "rewriting nginx conf for %s",
                           attr, oldvalue, value, self, self.instance)
            self.instance.rewrite()

    def _on_instance_update(self, instance, oldinstance, attr):
        if not self.attribute_changed(instance, oldinstance, attr):
            return

        self.log.debug("Instance changed, rewriting both nginx conf")
        if instance and instance.enabled:
            instance.rewrite()
        if oldinstance \
                and isinstance(oldinstance, Instance) \
                and oldinstance.enabled:
            oldinstance.rewrite()

    def delete(self, session=None):
        instance = self.instance
        super(Alias, self).delete(session)
        if instance.enabled:
            instance.rewrite()

    def to_dict(self):
        res = super(Alias, self).to_dict()
        res['destination'] = self.instance.domain
        return res

    def __repr__(self):
        return '<Alias {self.domain} for {self.instance.domain}>'\
                .format(self=self)


event.listen(Alias, 'init', Alias.after_init)
event.listen(Alias.domain, 'set', Alias._on_domain_update)
event.listen(Alias.instance, 'set', Alias._on_instance_update)
