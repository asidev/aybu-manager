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
from mako.template import Template
from . action import Action

__all__ = ['render']


class render(Action):

    def __init__(self, template_name, target, deferred=False,
                 skip_rollback=False, perms=None, **params):
        super(render, self).__init__()
        self.params = params
        self.template_name = template_name
        self.perms = perms
        self.template = Template(
            pkg_resources.resource_stream('aybu.manager.templates',
                                          template_name).read()
        )
        self.skip_rollback = skip_rollback
        self.target = target
        self.written = False
        if not deferred:
            self.write()
        else:
            self.log.debug("rendering of %s has been deferred", self.target)

    def render(self):
        if "instance" in self.params:
            settings = self.params['instance'].environment.settings
        else:
            from aybu.manager.models import Environment
            settings = Environment.settings

        return self.template.render(
                        settings=settings,
                        **self.params
        )

    def write(self):
        self.written = True
        self.log.debug("RENDERING %s to %s", self.template_name, self.target)
        try:
            with open(self.target, "w") as target:
                target.write(self.render())
            if self.perms:
                os.chmod(self.target, self.perms)
        except:
            self.rollback()
            raise

    def commit(self):
        if not self.written:
            self.write()

    def rollback(self):
        if self.skip_rollback:
            self.log.debug("Skipping rollback on %s", self.target)
            return

        if self.written:
            self.log.info("ROLLBACK: unlink %s", self.target)
            os.unlink(self.target)
