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

from sqlalchemy import (Column,
                        ForeignKey,
                        Integer,
                        Unicode)
from sqlalchemy.orm import backref
from sqlalchemy.orm import (relationship,
                            validates)

from . base import Base
from . validators import (validate_name,
                          validate_version,
                          validate_positive_int)


class Theme(Base):

    __tablename__ = 'themes'
    __table_args__ = ({'mysql_engine': 'InnoDB'})

    name = Column(Unicode(128), primary_key=True)
    parent_name = Column(Unicode(128), ForeignKey('themes.name',
                                                  onupdate='cascade',
                                                  ondelete='restrict'))
    children = relationship('Theme',
                            backref=backref('parent', remote_side=name))
    version = Column(Unicode(16))
    author_email = Column(Unicode(255), ForeignKey('users.email',
                                                      onupdate='cascade',
                                                      ondelete='restrict'))
    author = relationship('User', backref=backref('authored_themes'),
                          primaryjoin='User.email == Theme.author_email')


    owner_email = Column(Unicode(255), ForeignKey('users.email',
                                                     onupdate='cascade',
                                                     ondelete='restrict'),
                            nullable=False)
    owner = relationship('User', backref=backref('themes'),
                         primaryjoin="User.email == Theme.owner_email")



    banner_width = Column(Integer, nullable=False)
    banner_height = Column(Integer, nullable=False)
    logo_width = Column(Integer, nullable=False)
    logo_height = Column(Integer, nullable=False)
    main_menu_levels = Column(Integer, nullable=False)
    template_levels = Column(Integer, nullable=False)
    image_full_size = Column(Integer, nullable=False)

    @validates('name')
    def validates_name(self, key, name):
        return validate_name(name)

    @validates('version')
    def validates_version(self, key, version):
        return validate_version(version)

    @validates('banner_width', 'banner_height', 'logo_width', 'logo_height',
               'main_menu_levels', 'template_levels', 'image_full_size')
    def validate_sizes(self, key, size):
        return validate_positive_int(size)

    def __repr__(self):
        return "<Theme {t.name} (parent: {t.parent_name}) by {t.author}>"\
                .format(t=self)
