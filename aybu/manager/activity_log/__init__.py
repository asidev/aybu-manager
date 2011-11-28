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

import collections
import logging
from sqlalchemy.event import listen

from . exc import (TransactionError,
                   NOOP)

__all__ = ['ActivityLog']


class ActivityLog(object):

    def __init__(self, autobegin=True):
        self.log = logging.getLogger("{}.ActivityLog".format(__name__))
        self._actions = collections.deque()
        self.active = False
        self.autobegin = autobegin
        if autobegin:
            self.begin()

    @classmethod
    def attach_to(cls, session, autobegin=True):
        session.activity_log = ActivityLog(autobegin)
        listen(session, 'before_commit',
            lambda session: session.activity_log.commit())
        listen(session, 'after_rollback',
            lambda session: session.activity_log.rollback())

    def add_group(self, group, *args, **kwargs):
        try:
            actions = group(*args, **kwargs)
        except Exception as e:
            self.log.exception(e)
            self.rollback(exc=e)

        for action in actions:
            self.add(action, *args, **kwargs)

    def add(self, action, *args, **kwargs):
        try:
            a = action(*args, **kwargs)

        except NOOP:
            # the action has no opts to do in
            # commit or rollback
            pass

        except Exception as e:
            self.log.exception(e)
            self.rollback(exc=e)

        else:
            self._actions.append(a)

    def begin(self):
        self.active = True
        self._actions.clear()

    def rollback(self, exc=None):
        if not self.active:
            raise TransactionError("Transaction has not been started")
        self.log.error("Executing ROLLBACK")

        self.active = False
        try:
            while True:
                try:
                    action = self._actions.pop()
                except IndexError:
                    break

                try:
                    action.rollback()

                except Exception as e:
                    self.log.exception("Error in rollback")
                    if not exc:
                        exc = e

            if exc:
                raise exc

        finally:
            if self.autobegin:
                self.begin()

    def commit(self):
        if not self.active:
            raise TransactionError("Transaction has not been started")
        self.log.info("Executing COMMIT")

        exc = None
        self.active = False

        try:
            while True:
                try:
                    action = self._actions.popleft()
                except IndexError:
                    break

                try:
                    action.commit()

                except Exception as exc:
                    self.log.exception("Error in commit")
                    self.rollback(exc=exc)

        finally:
            if self.autobegin:
                self.begin()
