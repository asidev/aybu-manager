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

import shlex
import subprocess
from . action import Action

__all__ = ['command']


class command(Action):

    def __init__(self, cmd, *args, **kwargs):
        super(command, self).__init__()
        self.cmd = cmd
        self.args = args
        self.on_commit = kwargs.pop('on_commit', False)
        self.on_rollback = kwargs.pop('on_rollback', False)
        self.on_init = kwargs.pop('on_init', False)
        self.kwargs = kwargs
        if self.on_init:
            self.run()

    def run(self):
        try:
            self.log.info("Executing %s", self.cmd)
            subprocess.check_call(shlex.split(self.cmd),
                                  *self.args, **self.kwargs)

        except subprocess.CalledProcessError as e:
            self.log.error("Error while executing cmd: %s: %s",
                           self.cmd, e.output)
            raise e

    def commit(self):
        if self.on_commit:
            self.run()

    def rollback(self):
        if self.on_rollback:
            self.run()
