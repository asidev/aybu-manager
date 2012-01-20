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

    def get_database_connections(self, dbname=None):
        dbname = dbname or self.config.name
        res = self.execute("SELECT procpid from pg_stat_activity WHERE "
                           "datname='{}';".format(dbname))[0]
        return (row[0] for row in res.fetchall())

    def kill_database_connections(self, dbname=None):
        dbname = dbname or self.config.name
        stmts = []
        for connpid in self.get_database_connections(dbname):
            stmts.append("SELECT pg_terminate_backend({pid}) "
                         "FROM pg_stat_activity WHERE datname='{db}';"\
                         .format(pid=connpid, db=self.config.name))
        self.execute(stmts)


class PostgresqlDatabaseAction(PostgresAction):

    def create(self):
        return "CREATE DATABASE {config.name} WITH ENCODING = 'UTF8';"\
               .format(config=self.config)

    def drop(self):
        if hasattr(self, '_renamed'):
            name = self._renamed
        else:
            name = self.config.name
        self.kill_database_connections()
        return "DROP DATABASE {};".format(name)

    def exists(self):
        res = self.execute(
            "SELECT datname FROM pg_catalog.pg_database "\
            "WHERE datname='{config.name}'".format(config=self.config))
        return True if res[0].fetchall() else False

    def rename(self):
        self._renamed = "{}_tmp_".format(self.config.name)
        self.kill_database_connections()
        return "ALTER DATABASE {config.name} RENAME TO {renamed};"\
                .format(config=self.config, renamed=self._renamed)

    def restore(self):
        self.kill_database_connections(self._renamed)
        return "ALTER DATABASE {renamed} RENAME TO {original};"\
                .format(renamed=self._renamed, original=self.config.name)


class PostgresqlUserAction(PostgresAction):

    def create(self):
        return "CREATE ROLE {config.user} NOSUPERUSER LOGIN "\
               "ENCRYPTED PASSWORD '{config.password}';"\
                .format(config=self.config)

    def drop(self):
        role = self.config.user if not hasattr(self, "_renamed") \
                else self._renamed
        return "DROP ROLE {role};".format(role=role)

    def rename(self):
        self._renamed = "{}_tmp_".format(self.config.user)
        return "ALTER ROLE {name} RENAME TO {renamed};"\
                .format(name=self.config.user, renamed=self._renamed)

    def restore(self):
        return "ALTER ROLE {renamed} RENAME TO {name};"\
                .format(renamed=self._renamed, name=self.config.user)


class PostgresqlPrivilegesAction(PostgresAction):

    def grant(self):
        return "GRANT ALL PRIVILEGES ON DATABASE {config.name} "\
               "TO {config.user};".format(config=self.config)

    def revoke(self):
        return "REVOKE ALL PRIVILEGES ON DATABASE {config.name} "\
                "FROM {config.user};".format(config=self.config)
