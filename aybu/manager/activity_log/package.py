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
import pkg_resources
import shlex
import subprocess
from . action import Action


__all__ = ['install']


class install(Action):

    def __init__(self, virtualenv, name, path):
        self.python = os.path.join(virtualenv, 'bin', 'python')
        self.script = pkg_resources.resource_filename('aybu.manager.utils',
                                                      'pip.py')
        self.path = path
        self.name = name
        self.package_name = 'aybu-instances-{}'.format(self.name)
        self.virtualenv = virtualenv
        command = "{} {} install -e {}".format(self.python, self.script, path)
        self.log.debug("INSTALL: %s", command)
        subprocess.check_call(shlex.split(command))

    def commit(self):
        pass

    def rollback(self):
        cmd = "{} {} uninstall {}".format(self.python, self.script,
                                          self.package_name)
        self.log.error("UNINSTALL: %s", cmd)
        subprocess.check_call(shlex.split(cmd))



