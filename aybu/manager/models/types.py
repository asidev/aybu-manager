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

import crypt
import sqlalchemy.types as types

__all__ = ['Crypt']


class Crypt(types.TypeDecorator):
    """ This class model an encrypted string using UNiX crypt(3). """
    impl = types.CHAR
    default_length = 64
    saltid = "$5$"  # $5$ means SHA-256; see crypt(3)

    def __init__(self, length=default_length, *args, **kwargs):
        super(Crypt, self).__init__(length, *args, **kwargs)

    def process_bind_param(self, value, dialect):
        return crypt.crypt(value, self.saltid)

    def process_result_value(self, value, dialect):
        return value.strip()

    def copy(self):
        return Crypt(self.impl.length)
