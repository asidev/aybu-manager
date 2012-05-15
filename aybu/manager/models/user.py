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
                        Table)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (relationship,
                            backref,
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

# FIXME: missing primary key
users_groups = Table(u'users_groups',
                     Base.metadata,
                     Column('users_email',
                            Unicode(255),
                            ForeignKey('users.email',
                                       onupdate="cascade",
                                       ondelete="cascade"),
                            primary_key=True),
                     Column('groups_name',
                            Unicode(255),
                            ForeignKey('groups.name',
                                       onupdate="cascade",
                                       ondelete="cascade"),
                            primary_key=True),
                     mysql_engine='InnoDB')


instances_groups = Table(u'instances_groups',
                     Base.metadata,
                     Column('instance_domain',
                            Unicode(255),
                            ForeignKey('instances.domain',
                                       onupdate="cascade",
                                       ondelete="cascade"),
                            primary_key=True),
                     Column('group_name',
                            Unicode(255),
                            ForeignKey('groups.name',
                                       onupdate="cascade",
                                       ondelete="cascade"),
                            primary_key=True),
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
    company = Column(Unicode(128))
    web = Column(Unicode(128))
    twitter = Column(Unicode(128))
    organization_name = Column(Unicode(255),
                                ForeignKey('groups.name',
                                       onupdate="cascade",
                                       ondelete="restrict"),
                                nullable=True
                                )
    organization = relationship('Group', lazy='joined', backref='org_users')
    groups = relationship('Group', secondary=users_groups,
                          backref='group_users')

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

    def can_access(self, instance):
        self.log.debug("Cheking access for user %s to instance %s",
                      self, instance)

        user_groups = set([g.name for g in self.groups])
        if self.organization_name:
            user_groups.add(self.organization_name)

        self.log.debug("User groups: %s", user_groups)
        if "admin" in user_groups:
            self.log.debug("User is admin. Access granted")
            return True

        allowed_groups = set()
        for group in instance.groups:
            allowed_groups.add(group.name)
            g = group.parent
            while g:
                if g.name not in allowed_groups:
                    allowed_groups.add(g.name)
                    g = g.parent

                else:
                    # avoid endless loops
                    break

        self.log.debug("Allowed groups for instance %s: %s",
                       instance, allowed_groups)

        if user_groups & allowed_groups:
            self.log.debug("User %s can access instance %s", self, instance)
            return True

        self.log.debug("User %s does not have permissions for %s",
                      self, instance)
        return False

    def to_dict(self):
        res = super(User, self).to_dict()
        res['organization'] = res['organization_name']
        del res['organization_name']
        res.update(dict(groups=[g.name for g in self.groups]))
        return res

    def check_password(self, password):
        return self.__class__.check(object_session(self), self.username,
                                    password)

    def has_permission(self, perm):
        return bool(set((perm, 'admin')) & set(g.name for g in self.groups))

    def __repr__(self):
        return "<User {} ({} {}) [{}]>".format(self.email, self.name,
                                               self.surname, self.company)


class Group(Base):

    __tablename__ = u'groups'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    name = Column(Unicode(255), primary_key=True)
    parent_name = Column(Unicode(255), ForeignKey('groups.name',
                                                  onupdate='cascade',
                                                  ondelete='restrict'),
                         nullable=True)
    children = relationship('Group',
                            backref=backref('parent', remote_side=name))
    instances = relationship('Instance', secondary=instances_groups,
                             backref='groups')

    @hybrid_property
    def users(self):
        res = list(self.org_users)
        res.extend(self.group_users)
        return res

    @hybrid_property
    def is_organization(self):
        return bool(len(self.org_users))

    @validates('name')
    def validate_name(self, key, name):
        return validate_name(name)

    def to_dict(self):
        return {'name': self.name,
                'users': [u.email for u in self.users],
                'parent': self.parent_name,
                'organization': self.is_organization,
                'children': [g.name for g in self.children],
                'instances': [i.domain for i in self.instances]
               }

    def __repr__(self):
        res = "<Group {}".format(self.name)
        if self.instances:
            return "{} [instances: {}]>".format(res, ", ".join(self.instance))
        else:
            return "{}>".format(res)
