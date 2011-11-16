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

from . instance import Instance
from . redirect import Redirect
from . environment import Environment
from . user import User, Group
from . theme import Theme
from . base import Base
import logging
from aybu.manager.utils import FileSystemSession
from sqlalchemy.event import listen


__all__ = ['Instance', 'Environment', 'Redirect', 'User', 'Group', 'Theme',
           'Base', 'add_session_events']
log = logging.getLogger(__name__)


def before_session_commit(session):
    session.fs.commit()


def after_session_rollback(session):
    session.fs.rollback()


def add_session_events(session):
    session.fs = FileSystemSession()
    listen(session, 'before_commit', before_session_commit)
    listen(session, 'after_rollback', after_session_rollback)
