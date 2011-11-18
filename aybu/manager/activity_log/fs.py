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

__all__ = ['mkdir', 'create', 'copy']


class FSAction(Action):

    def __init__(self, path):
        super(FSAction, self).__init__()
        self.path = path
        self.log.debug("init: %s %s", self.name, self.path)

    def commit(self):
        self.log.debug("COMMIT (noop): %s %s", self.name, self.path)

    def rollback(self):
        self.log.debug("ROLLBACK (noop): %s %s", self.name, self.path)


class mkdir(FSAction):

    def __init__(self, path, mode=0777, error_on_exists=True,
                 recursive_delete=False):
        super(mkdir, self).__init__(path)
        self.recursive_delete=recursive_delete
        if not error_on_exists:
            if not os.path.exists(path):
                os.mkdir(path, mode)
            else:
                raise NOOP()
        else:
            os.mkdir(path, mode)

    def rollback(self):
        if not self.recursive_delete:
            self.log.error("ROLLBACK: rmdir %s", self.path)
            os.rmdir(self.path)
        else:
            self.log.error("ROLLBACK: rmtree %s", self.path)
            shutil.rmtree(self.path)


class create(FSAction):

    def __init__(self, path, content=''):
        super(create, self).__init__(path)
        if os.path.exists(path):
            raise OSError(errno.EEXIST, "File exists: {}".format(path))
        with open(path, 'w') as f:
            f.write(content)

    def rollback(self):
        self.log.error("ROLLBACK: unlink %s", self.path)
        os.unlink(self.path)


class copy(create):

    def __init__(self, source, destination):
        # not that destination and source are swapped
        # w.r.t shutil function, as we care about destination
        super(copy, self).__init__(destination)
        shutil.copy(source, destination)
