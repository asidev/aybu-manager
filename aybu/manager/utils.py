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
import errno
import logging
import os
import shutil
__all__ = ['classproperty', 'FileSystemSession', 'TransactionError']


class classproperty(property):
    """ a property decorator for classmethods """
    def __get__(self, obj, type_):
        return self.fget.__get__(None, type_)()

    def __set__(self, obj, value):
        cls = type(obj)
        return self.fset.__get__(None, cls)(value)


class FSAction(object):

    def __init__(self, path, *args, **kwargs):
        self.path = path
        self.name = self.__class__.__name__
        self.log = logging.getLogger("{}.{}".format(self.__class__.__module__,
                                                  self.name))
        self.log.debug("BEGIN: %s %s", self.name, path)
        self.begin(path, *args, **kwargs)

    def commit(self):
        self.log.debug("COMMIT (noop): %s %s", self.name, self.path)

    def begin(self, *args, **kwargs):  # pragma: nocover
        raise NotImplementedError

    def rollback(self):  # pragma: nocover
        # this must be redefined by subclasses
        raise NotImplementedError


class mkdir(FSAction):

    def begin(self, path, mode=0777, error_on_exists=True):
        if not error_on_exists:
            if not os.path.exists(path):
                os.mkdir(path, mode)
            else:
                raise NOOP()
        else:
            os.mkdir(path, mode)

    def rollback(self):
        self.log.error("ROLLBACK: rmdir %s", self.path)
        os.rmdir(self.path)


class create(FSAction):

    def begin(self, path, content=''):
        if os.path.exists(path):
            raise OSError(errno.EEXIST, "File exists: {}".format(path))
        with open(path, 'w') as f:
            f.write(content)

    def rollback(self):
        self.log.error("ROLLBACK: unlink %s", self.path)
        os.unlink(self.path)


class copy(create):

    def begin(self, destination, source):
        # not that destination and source are swapped
        # w.r.t shutil function, as we care about destination
        shutil.copy(source, destination)


class TransactionError(Exception):
    pass


class NOOP(Exception):
    pass


class FileSystemSession(object):

    def __init__(self, autobegin=True):
        self.log = logging.getLogger(__name__)
        self.log.debug("Creating new FileSystemSession")
        self._steps = collections.deque()
        self.active = False
        self.autobegin = autobegin
        if autobegin:
            self.begin()

    def perform(self, action, *args, **kwargs):
        try:
            a = action(*args, **kwargs)

        except NOOP:
            # the action has no opts to do in
            # commit or rollback
            pass

        except Exception as e:
            self.rollback(exc=e)

        else:
            self._steps.append(a)

    def create(self, path, content=''):
        self.perform(create, path, content)

    def copy(self, source, destination):
        self.perform(copy, destination, source)

    def mkdir(self, path, mode=0777, error_on_exists=True):
        self.perform(mkdir, path, mode, error_on_exists)

    def begin(self):
        self.active = True
        self._steps.clear()

    def rollback(self, exc=None):
        if not self.active:
            raise TransactionError("Transaction has not been started")

        self.active = False
        try:
            for step in reversed(self._steps):
                try:
                    step.rollback()
                except Exception as e:
                    self.log.exception("Error in rollback")
                    exc = e

            if exc:
                raise exc

        finally:
            if self.autobegin:
                self.begin()

    def commit(self):
        if not self.active:
            raise TransactionError("Transaction has not been started")
        exc = None
        self.active = False

        try:
            for step in self._steps:
                try:
                    step.commit()
                except Exception as exc:
                    self.log.exception("Error in commit")
                    self.rollback(exc=exc)
        finally:
            if self.autobegin:
                self.begin()
