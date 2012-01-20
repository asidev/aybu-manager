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

import os
import errno
import shutil
from . exc import NOOP
from . action import Action

__all__ = ['mkdir', 'create', 'copy', 'rm', 'rmdir', 'rmtree']


class FSAction(Action):

    def __init__(self, path):
        super(FSAction, self).__init__()
        self.path = path

    def commit(self):
        pass

    def rollback(self):
        pass


class DeleteAction(FSAction):

    def __init__(self, path, error_on_dirs=False, error_on_not_exists=True,
                 deferred=False):
        super(DeleteAction, self).__init__(path)
        self.tmp_name = "._{}".format(os.path.basename(path))
        self.tmp_path = os.path.realpath(
            os.path.join(os.path.dirname(path), self.tmp_name)
        )
        self.deferred = deferred

        if error_on_dirs and os.path.isdir(self.path):
            raise OSError(errno.EISDIR,
                          "Is a directory: '{}'".format(self.path))

        if deferred:
            self.tmp_path = path
            self.skip = False

        elif not error_on_not_exists and not os.path.exists(path):
            self.skip = True

        else:
            self.skip = False
            self.log.info("renaming %s to %s", path, self.tmp_path)
            os.rename(path, self.tmp_path)

    def rollback(self):
        if not self.skip:
            self.log.info("restoring %s", self.path)
            os.rename(self.tmp_path, self.path)


class mkdir(FSAction):

    def __init__(self, path, mode=0777, error_on_exists=True,
                 recursive_delete=False):
        super(mkdir, self).__init__(path)
        self.recursive_delete = recursive_delete
        if not error_on_exists:
            if not os.path.exists(path):
                os.mkdir(path, mode)
            else:
                raise NOOP()
        else:
            os.mkdir(path, mode)

    def rollback(self):
        if not self.recursive_delete:
            self.log.info("rmdir %s", self.path)
            os.rmdir(self.path)
        else:
            self.log.info("rmtree %s", self.path)
            shutil.rmtree(self.path)


class create(FSAction):

    def __init__(self, path, content=''):
        super(create, self).__init__(path)
        self.log.info("create file %s", path)
        if os.path.exists(path):
            raise OSError(errno.EEXIST, "File exists: {}".format(path))

        if content is None:
            return

        with open(path, 'w') as f:
            f.write(content)

    def rollback(self):
        self.log.info("unlink %s", self.path)
        os.unlink(self.path)


class copy(create):

    def __init__(self, source, destination):
        super(copy, self).__init__(destination)
        self.log.info("cp %s => %s", source, destination)
        shutil.copy(source, destination)


class copytree(create):

    def __init__(self, source, destination):
        super(copytree, self).__init__(destination, content=None)
        self.log.info("copytree %s => %s", source, destination)
        shutil.copytree(source, destination)

    def rollback(self):
        self.log.info("rmtree %s", self.path)
        shutil.rmtree(self.path)


class rm(DeleteAction):

    def __init__(self, path, error_on_not_exists=True, deferred=False):
        super(rm, self).__init__(path, True, error_on_not_exists,
                                 deferred=deferred)

    def commit(self):
        if not self.skip:
            self.log.info("unlinking %s (was %s)", self.tmp_path, self.path)
            os.unlink(self.tmp_path)


class rmdir(DeleteAction):

    def commit(self):
        if not self.skip:
            self.log.info("rmdir %s (was %s)", self.tmp_path, self.path)
            os.rmdir(self.tmp_path)


class rmtree(DeleteAction):

    def commit(self):
        if not self.skip:
            self.log.info("rmtree %s (was %s)", self.tmp_path, self.path)
            shutil.rmtree(self.tmp_path)
