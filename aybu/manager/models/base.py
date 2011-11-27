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

import logging
import sqlalchemy.ext.declarative
from sqlalchemy.util.langhelpers import symbol
from aybu.manager.utils.decorators import classproperty
from aybu.core.models.base import AybuBase


__all__ = ['Base']


class AybuManagerBase(AybuBase):

    def attribute_changed(self, value, oldvalue, attr):

        if oldvalue == symbol('NEVER_SET')\
           or value == oldvalue\
           or (oldvalue == symbol('NO_VALUE')
               and getattr(self, attr.key) == None):
            return False

        return True

    @classproperty
    @classmethod
    def log(cls):
        if hasattr(cls, '_log'):
            return cls._log

        cls._log = logging.getLogger("{}.{}".format(cls.__module__,
                                                    cls.__name__))
        return cls._log


Base = sqlalchemy.ext.declarative.declarative_base(cls=AybuManagerBase)
