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
import crypt
import re
from logging import getLogger
from sqlalchemy import (Column,
                        ForeignKey,
                        Unicode,
                        Table,
                        Integer)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (relationship,
                            object_session,
                            validates,
                            joinedload)
from sqlalchemy.orm.exc import NoResultFound

from . validators import (validate_email,
                          validate_password,
                          validate_web_address,
                          validate_twitter,
                          validate_name)

__all__ = []

log = getLogger(__name__)


users_groups = Table(u'users_groups',
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
                                       ondelete="cascade")),
                     mysql_engine='InnoDB')


class User(Base):

    __tablename__ = u'users'
    __table_args__ = ({'mysql_engine': u'InnoDB'})

    hash_re = re.compile(r'(\$[1,5-6]\$|\$2a\$)')
    salt = "$6$"

    email = Column(Unicode(255), primary_key=True)
    crypted_password = Column("password", Unicode(128), nullable=False)
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

    @hybrid_property
    def password(self):
        return self.crypted_password

    @password.setter
    def password(self, value):
        self.crypted_password = crypt.crypt(value, self.salt)

    @classmethod
    def get(cls, session, pkey):
        user = session.query(cls).options(joinedload('groups')).get(pkey)
        if user is None:
            raise NoResultFound("No obj with key {} in class {}"\
                                .format(pkey, cls.__name__))
        return user

    @classmethod
    def check(cls, session, email, password):
        try:
            user = cls.get(session, email)
            length = len(cls.hash_re.match(user.password).group())
            enc_password = crypt.crypt(password, user.password[0:length])
            assert user.password == enc_password

        except (AssertionError, NoResultFound):
            log.error('Invalid login for %s', email)
            raise ValueError('invalid username or password')

        else:
            return user

    def to_dict(self):
        res = super(User, self).to_dict()
        res.update(dict(groups=[g.name for g in self.groups]))
        return res

    def check_password(self, password):
        return self.__class__.check(object_session(self), self.username,
                                    password)

    def has_permission(self, perm):
        return bool(set((perm, 'admin')) & set(g.name for g in self.groups))

    def __repr__(self):
        return "<User {} ({} {}) [{}]>".format(self.email, self.name,
                                               self.surname, self.organization)


class Group(Base):

    __tablename__ = u'groups'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    name = Column(Unicode(255), primary_key=True)
    instance_id = Column(Integer,
                         ForeignKey('instances.id',
                                    onupdate='cascade',
                                    ondelete='cascade'),
                         nullable=True
    )
    instance = relationship('Instance', backref='groups')

    @validates('name')
    def validate_name(self, key, name):
        return validate_name(name)

    def to_dict(self):
        return {'name': self.name,
                'users': [u.email for u in self.users],
                'instance': self.instance.domain if self.instance else None}

    def __repr__(self):
        res = "<Group {}".format(self.name)
        if self.instance:
            return "{} [instance: {}]>".format(res, self.instance)
        else:
            return "{}>".format(res)
