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
from sqlalchemy.orm import class_mapper


class SQLAction(object):

    def __new__(cls, type_, what, init=None, commit=None, rollback=None,
                config=None, session=None):
        what = what.replace("_", " ").title().replace(" ", "")
        module_name = "{}actions".format(type_)
        clsname = "{}{}Action".format(type_.title(), what)
        module = __import__(module_name, globals(), locals(), [clsname])
        targetcls = getattr(module, clsname)
        obj = object.__new__(targetcls)
        obj.log = logging.getLogger("{}.{}".format(__name__,
                                                   targetcls.__name__))
        obj.on_init = init
        obj.on_commit = commit
        obj.on_rollback = rollback
        if config:
            obj.config = config
        if session:
            obj.session = session
        return obj

    def __call__(self, session, config):
        self.config = config
        self.session = session
        if self.on_init:
            self.execute(getattr(self, self.on_init)())
        return self

    def get_connection(self):
        from aybu.manager.models import Instance
        mapper = class_mapper(Instance)
        return self.session.get_bind(mapper=mapper).connect()

    def execute(self, statements):
        if not statements:
            return

        res = []

        if isinstance(statements, basestring):
            statements=(statements, )
        connection = self.get_connection()
        for statement in statements:
            self.log.info(statement)
            res.append(connection.execute(statement))
        connection.close()
        return res

    def commit(self):
        if self.on_commit:
            self.execute(getattr(self, self.on_commit)())

    def rollback(self):
        if self.on_rollback:
            self.execute(getattr(self, self.on_rollback)())
