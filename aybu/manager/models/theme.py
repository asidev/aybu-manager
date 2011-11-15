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
from sqlalchemy.orm import relationship

from . base import Base


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
    author = relationship('User', backref=backref('authored_themes',
                                                  remote_side=author_email))

    owner_email = Column(Unicode(255), ForeignKey('users.email',
                                                     onupdate='cascade',
                                                     ondelete='restrict'),
                            nullable=False)
    owner = relationship('User', backref=backref('themes',
                                                 remote_side=owner_email))

    banner_width = Column(Integer, nullable=False)
    banner_height = Column(Integer, nullable=False)
    logo_width = Column(Integer, nullable=False)
    logo_height = Column(Integer, nullable=False)
    main_menu_levels = Column(Integer, nullable=False)
    template_levels = Column(Integer, nullable=False)
    image_full_size = Column(Integer, nullable=False)

    def __repr__(self):
        return "<Theme {t.name} (parent: {t.parent_name}) by {t.author}>"\
                .format(t=self)
