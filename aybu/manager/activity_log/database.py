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
    return [DatabaseAction("create_database", config.type),
            DatabaseAction("create_user", config.type),
            DatabaseAction("flush_privileges", config.type)]


class DatabaseAction(object):

    def __new__(cls, action, type_):

        action = action.replace("_", " ").title().replace(" ", "")
        clsname = "{}{}Action".format(type_.title(), action)
        targetcls = globals()[clsname]
        obj = object.__new__(targetcls)
        obj.log = logging.getLogger("{}.{}".format(__name__,
                                                   targetcls.__name__))
        return obj

    def __call__(self, session, config):
        self.config = config
        self.session = session
        self.init()
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
        pass

    def rollback(self):
        pass


class MysqlCreateDatabaseAction(DatabaseAction):

    def init(self):
        self.log.debug("BEGIN: Creating MySQL database")
        stmt = "CREATE DATABASE {config.name} "\
               "DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;"\
               .format(config=self.config)
        self.execute(stmt)

    def rollback(self):
        self.log.debug("ROLLBACK: removing MySQL database")
        stmt = "DROP DATABASE {config.name};".format(config=self.config)
        self.execute(stmt)

class MysqlCreateUserAction(DatabaseAction):

    def init(self):
        self.log.debug("BEGIN: Creating MySQL user")
        statements = ("CREATE USER {config.user}@localhost  IDENTIFIED BY "
                        "'{config.password}';",
                      "GRANT USAGE ON *.* TO {config.user}@localhost;",
                      "GRANT ALL PRIVILEGES ON `{config.name}`.* "
                         "TO {config.user}@localhost;"
        )
        statements = (stmt.format(config=self.config) for stmt in statements)
        self.execute(statements)

    def rollback(self):
        self.log.debug("ROLLBACK: removing MySQL user")
        stmt = "DROP USER {config.user}@localhost;"\
                .format(config=self.config)
        self.execute(stmt)


class MysqlFlushPrivilegesAction(DatabaseAction):

    def init(self):
        self.execute("FLUSH PRIVILEGES;")
