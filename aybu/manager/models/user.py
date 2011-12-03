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

from . base import Base
from . types import Crypt
import crypt
from logging import getLogger
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Unicode
from sqlalchemy import Table
from sqlalchemy.orm import (relationship,
                            object_session,
                            validates,
                            joinedload)

from . validators import (validate_email,
                          validate_password,
                          validate_web_address,
                          validate_twitter,
                          validate_name)

__all__ = []

log = getLogger(__name__)


users_groups = Table('users_groups',
                     Base.metadata,
                     Column('users_email',
                            Unicode(255),
                            ForeignKey('users.email',
                                       onupdate="cascade",
                                       ondelete="cascade")),
                            Column('groups_name',
                                   Unicode(32),
                                   ForeignKey('groups.name',
                                              onupdate="cascade",
                                              ondelete="cascade")))


class User(Base):

    __tablename__ = 'users'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    email = Column(Unicode(255), primary_key=True)
    password = Column(Crypt(), nullable=False)
    name = Column(Unicode(128), nullable=False)
    surname = Column(Unicode(128), nullable=False)
    organization = Column(Unicode(128))
    web = Column(Unicode(128))
    twitter = Column(Unicode(128))

    groups = relationship('Group', secondary=users_groups, backref='users')

    @validates('email')
    def validate_email(self, key, email):
        return validate_email(email)

    @validates('password')
    def validate_password(self, key, password):
        return validate_password(password)

    @validates('web')
    def validate_web(self, key, web_address):
        return validate_web_address(web_address)

    @validates('twitter')
    def validate_twitter(self, key, twitter):
        return validate_twitter(twitter)

    @classmethod
    def get(cls, session, pkey):
        return session.query(cls).options(joinedload('groups')).get(pkey)

    @classmethod
    def check(cls, session, email, password):
        try:
            user = cls.get(session, email)
            enc_password = crypt.crypt(password, user.password[0:2])
            assert user.password == enc_password

        except:
            log.error('Invalid login: %s != %s', password, enc_password)
            raise ValueError('invalid username or password')

        else:
            return True

    def check_password(self, password):
        return self.__class__.check(object_session(self), self.username,
                                    password)

    def has_permission(self, perm):
        return bool(set((perm, 'admin')) & set(g.name for g in self.groups))

    def __repr__(self):
        return "<User {} ({} {}) [{}]>".format(self.email, self.name,
                                               self.surname, self.organization)


class Group(Base):

    __tablename__ = 'groups'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    name = Column(Unicode(32), primary_key=True)

    @validates('name')
    def validate_name(self, key, name):
        return validate_name(name)

    def __repr__(self):
        return "<Group {}>".format(self.name)

