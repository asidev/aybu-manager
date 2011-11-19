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

__all__ = ['create_database']

import logging
from sqlalchemy.orm import class_mapper


def create_database(session, config):
    return [SQLAction(config.type, "database", init="create", rollback='drop'),
            SQLAction(config.type, "user", init="create", rollback='drop'),
            SQLAction(config.type, "privileges", commit="flush")]

def drop_database(session, config):
    return [SQLAction(config.type, "user", init="drop", rollback='create'),
            SQLAction(config.type, "database", init="rename",
                      commit='drop', rollback='restore'),
            SQLAction(config.type, "privileges", commit="flush")]


class SQLAction(object):

    def __new__(cls, type_, what, init=None, commit=None, rollback=None):

        what = what.replace("_", " ").title().replace(" ", "")
        clsname = "{}{}Action".format(type_.title(), what)
        targetcls = globals()[clsname]
        obj = object.__new__(targetcls)
        obj.log = logging.getLogger("{}.{}".format(__name__,
                                                   targetcls.__name__))
        obj.on_init = init
        obj.on_commit = commit
        obj.on_rollback = rollback
        return obj

    def __call__(self, session, config):
        self.config = config
        self.session = session
        if self.on_init:
            getattr(self, self.on_init)()
        return self

    def get_connection(self):
        from aybu.manager.models import Instance
        mapper = class_mapper(Instance)
        return self.session.get_bind(mapper=mapper).connect()

    def execute(self, statements):
        if isinstance(statements, basestring):
            statements=(statements, )
        connection = self.get_connection()
        for statement in statements:
            self.log.info(statement)
            connection.execute(statement)
        connection.close()

    def commit(self):
        if self.on_commit:
            getattr(self, self.on_commit)()

    def rollback(self):
        if self.on_rollback:
            getattr(self, self.on_rollback)()


class MysqlDatabaseAction(SQLAction):

    def create(self):
        stmt = "CREATE DATABASE {config.name} "\
               "DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;"\
               .format(config=self.config)
        self.execute(stmt)

    def drop(self):
        stmt = "DROP DATABASE {name};".format(name=self.config.name)
        self.execute(stmt)

    def rename(self):
        """ MySQL does not support RENAME DATABASE (which indeed was
            supported between 5.1.7 and 5.1.23), so we do ... nothing.

            a workaround can be:
                - create the new database
                - issue N querys like: RENAME TABLE old.xxx TO new.xxx
                - drop the old database
            but it can be tricky w.r.t indexes and constraint
        """
        self.log.debug("Renaming MySQL database (NoOP)")

    def restore(self):
        self.log.debug("Restoring MySQL database (NoOP)")


class MysqlUserAction(SQLAction):

    def create(self):
        statements = ("CREATE USER {config.user}@localhost  IDENTIFIED BY "
                        "'{config.password}';",
                      "GRANT USAGE ON *.* TO {config.user}@localhost;",
                      "GRANT ALL PRIVILEGES ON `{config.name}`.* "
                         "TO {config.user}@localhost;"
        )
        statements = (stmt.format(config=self.config) for stmt in statements)
        self.execute(statements)

    def drop(self):
        stmt = "DROP USER {config.user}@localhost;"\
                .format(config=self.config)
        self.execute(stmt)


class MysqlPrivilegesAction(SQLAction):

    def flush(self):
        self.execute("FLUSH PRIVILEGES;")
