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

from . sqlaction import SQLAction

class PostgresAction(SQLAction):

    def get_connection(self):
        """ On postgres you cannot create database within a transaction
            Since SQLA method Engine.connect() returns a connection which
            is within a transaction, we ROLLBACK that transaction before
            returning the connection to be used with execute
        """
        conn = super(PostgresAction, self).get_connection()
        conn.execute("ROLLBACK")
        return conn


class PostgresqlDatabaseAction(PostgresAction):

    def create(self):
        return "CREATE DATABASE {config.name} WITH ENCODING = 'UTF8';"\
               .format(config=self.config)

    def drop(self):
        if hasattr(self, '_renamed'):
            name = self._renamed
        else:
            name = self.config.name
        return "DROP DATABASE {};".format(name)

    def rename(self):
        self._renamed = "{}_tmp_".format(self.config.name)
        return "ALTER DATABASE {config.name} RENAME TO {renamed};"\
                .format(config=self.config, renamed=self._renamed)

    def restore(self):
        return "ALTER DATABASE {renamed} RENAME TO {original};"\
                .format(renamed=self._renamed, original=self.config.name)


class PostgresqlUserAction(PostgresAction):

    def create(self):
        return "CREATE ROLE {config.user} NOSUPERUSER LOGIN "\
               "ENCRYPTED PASSWORD '{config.password}';"\
                .format(config=self.config)

    def drop(self):
        return "DROP ROLE {role};".format(role=self.config.user)


class PostgresqlPrivilegesAction(PostgresAction):

    def grant(self):
        return "GRANT ALL PRIVILEGES ON DATABASE {config.name} "\
               "TO {config.user};".format(config=self.config)

    def revoke(self):
        return "REVOKE ALL PRIVILEGES ON DATABASE {config.name} "\
                "FROM {config.user};".format(config=self.config)


