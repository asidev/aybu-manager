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

__all__ = ['create_database', 'drop_database',
           'dump_database', 'restore_database']

from . sqlaction import SQLAction
from . dump import (dump_database,
                    restore_database)


def create_database(session, config):
    return [SQLAction(config.type, "user", init="create", rollback='drop'),
            SQLAction(config.type, "database", init="create", rollback='drop'),
            SQLAction(config.type, "privileges", init="grant",
                      rollback='revoke')]


def drop_database(session, config, skip_if_not_exists=True):
    exists = SQLAction(config.type, 'database', config=config, session=session)
    if skip_if_not_exists and not exists.exists():
        return []

    return [SQLAction(config.type, "privileges", init="revoke",
                      rollback='grant'),
            SQLAction(config.type, "database", init="rename",
                      commit='drop', rollback='restore'),
            SQLAction(config.type, "user", init="rename", commit='drop',
                      rollback='restore')]
