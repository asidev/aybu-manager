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

from aybu.manager.exc import ValidationError
from aybu.manager.models import Environment
from . test_base import ManagerModelsTestsBase


class EnvironmentTests(ManagerModelsTestsBase):

    def test_create(self):
        self.config = {'app:aybu-manager': self.config}
        with self.assertRaises(ValidationError):
            env = Environment.create(self.session, 'test-env',
                                        config=self.config)
        env = Environment.create(self.session, 'testenv', config=self.config)
        keys = {k.replace('paths.', ''): self.config['app:aybu-manager'][k]
                          for k in self.config['app:aybu-manager'] if
                          k.startswith('paths.')}

        for key, path in keys.iteritems():
            if key == 'virtualenv':
                continue
            self.log.debug("%s: %s", key, path)
            self.assertTrue(os.path.isdir(path))

        self.session.commit()
        for key, path in env.paths._asdict().iteritems():
            if key == 'logs':
                path = env.paths.logs.dir
            if key == 'virtualenv':
                continue

            self.log.debug("%s: %s", key, path)
            self.assertTrue(os.path.isdir(path))
