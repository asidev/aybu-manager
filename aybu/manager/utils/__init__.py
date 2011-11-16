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

import pkg_resources
from mako.template import Template


class IniRenderer(object):

    def __init__(self, instance, template_name, target):
        self.instance = instance
        self.template = Template(
            pkg_resources.resource_stream('aybu.manager.templates',
                                          template_name)
        )
        self.target = target

    def render(self):
        return self.template.render(instance=self.instance,
                                    os=self.instance.os_config,
                                    smtp=self.instance.environment.smtp_config)

    def write(self):
        with open(self.target, "w") as target:
            target.write(self.render())


