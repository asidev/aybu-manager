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

    def __init__(self, instance, template_name, target, deferred=False):
        super(render, self).__init__()
        self.instance = instance
        self.template_name = template_name
        self.template = Template(
            pkg_resources.resource_stream('aybu.manager.templates',
                                          template_name).read()
        )
        self.target = target
        self.written = False
        if not deferred:
            self.write()

    def render(self):
        return self.template.render(instance=self.instance,
                                    os=self.instance.os_config,
                                    smtp=self.instance.environment.smtp_config)

    def write(self):
        self.written = True
        self.log.debug("RENDERING %s to %s", self.template_name, self.target)
        with open(self.target, "w") as target:
            target.write(self.render())

    def commit(self):
        if not self.written:
            self.write()

    def rollback(self):
        if self.written:
            self.log.error("ROLLBACK: unlink %s", self.target)
            os.unlink(self.target)
