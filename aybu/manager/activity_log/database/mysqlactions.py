#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright 2010-2012 Asidev s.r.l.

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

from . sqlaction import SQLAction


class MysqlDatabaseAction(SQLAction):

    def create(self):
        stmt = "CREATE DATABASE {config.name} "\
               "DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci;"\
               .format(config=self.config)
        return stmt

    def drop(self):
        stmt = "DROP DATABASE {name};".format(name=self.config.name)
        return stmt

    def exists(self):
        res = self.execute(
            "SELECT schema_name FROM information_schema.schemata "\
            "WHERE schema_name = '{name}'".format(name=self.config.name))
        return True if res[0].fetchall() else False

    def rename(self):
        """ MySQL does not support RENAME DATABASE (which indeed was
            supported between 5.1.7 and 5.1.23), so we do ... nothing.

            a workaround can be:
                - create the new database
                - issue N querys like: RENAME TABLE old.xxx TO new.xxx
                - drop the old database
            but it can be tricky w.r.t indexes and constraints
        """
        self.log.debug("Renaming MySQL database (NoOP)")

    def restore(self):
        self.log.debug("Restoring MySQL database (NoOP)")


class MysqlUserAction(SQLAction):

    def create(self):
        stmt = "CREATE USER {config.user}@localhost  IDENTIFIED BY "\
                   "'{config.password}';".format(config=self.config)
        return stmt

    def drop(self):
        role = self.config.user if not hasattr(self, "_renamed")\
                else self._renamed
        stmt = "DROP USER {role}@localhost;"\
                .format(role=role)
        return stmt

    def rename(self):
        self._renamed = "{}_tmp_".format(self.config.user)
        return "RENAME USER {name}@localhost TO {renamed}@localhost;"\
                .format(name=self.config.user, renamed=self._renamed)

    def restore(self):
        return "RENAME USER {renamed}@localhost TO {name}@localhost;"\
                .format(name=self.config.user, renamed=self._renamed)



class MysqlPrivilegesAction(SQLAction):

    def grant(self):
        statements = ("GRANT USAGE ON *.* TO {config.user}@localhost;",
                      "GRANT ALL PRIVILEGES ON `{config.name}`.* "
                         "TO {config.user}@localhost;",
                      "FLUSH PRIVILEGES"
        )
        statements = (stmt.format(config=self.config) for stmt in statements)
        return statements

    def revoke(self):
        stmt = "REVOKE ALL PRIVILEGES, GRANT OPTION FROM {user}@localhost"\
                .format(user=self.config.user)
        return stmt
