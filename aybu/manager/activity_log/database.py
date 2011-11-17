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


class create_database(object):

   def __new__(self, session, config):
       return DatabaseAction("create_database", session, config)


class DatabaseAction(object):

    def __new__(cls, action, session, config):

        type_= config.type
        action = action.replace("_", " ").title().replace(" ", "")
        clsname = "{}{}Action".format(type_.title(), action)
        targetcls = globals()[clsname]
        obj = object.__new__(targetcls)
        obj.log = logging.getLogger("{}.{}".format(__name__,
                                                   targetcls.__name__))
        obj.config = config
        obj.session = session
        obj.init()

        return obj

    def get_connection(self):
        from aybu.manager.models import Instance
        mapper = class_mapper(Instance)
        return self.session.get_bind(mapper=mapper).connect()

    def execute(self, statements):
        if isinstance(statements, basestring):
            statements = (statements,)
        connection = self.get_connection()
        for stmt in statements:
            stmt.format(conf=self.config)
            self.log.info(stmt)
            connection.execute(stmt)
        connection.close()

    def commit(self):
        pass

    def rollback(self):
        pass


class MysqlCreateDatabaseAction(DatabaseAction):

    def init(self):
        self.log.debug("BEGIN: Creating MySQL database and user")
        stmt = (
            "CREATE DATABASE '{conf.name}' "
              "DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;",
            "CREATE USER '{conf.user}'@'localhost' "
              "IDENTIFIED BY '{conf.password}';",
            "GRANT USAGE ON *.* TO {conf.user}'@'localhost' "
             "IDENTIFIED BY '{conf.password}';",
            "GRANT ALL PRIVILEGES ON `{conf.name}`.* "
             "TO '{conf.user}'@'localhost';",
            "FLUSH PRIVILEGES;"
        )
        self.execute(stmt)

    def rollback(self):
        self.log.debug("ROLLBACK: removing MySQL user and database")
        stmt = ("DROP USER '{conf.user'}@'localhost';",
                "FLUSH PRIVILEGES;",
                "ALTER TABLE instances AUTO_INCREMENT=1;")
        self.execute(stmt)





