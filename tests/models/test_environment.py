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

    def assert_env_paths(self, env):
        for key, path in env.paths._asdict().iteritems():
            if key == 'logs':
                path = env.paths.logs.dir
            elif key == 'configs':
                path = [env.paths.configs.nginx,
                        env.paths.configs.uwsgi,
                        env.paths.configs.supervisor_dir]
            elif key.startswith('virtualenv'):
                continue

            if isinstance(path, list):
                for p in path:
                    self.log.debug("%s: %s", key, p)
                    self.assertTrue(os.path.isdir(p))
            else:
                self.log.debug("%s: %s", key, path)
                self.assertTrue(os.path.isdir(path))

    def test_create(self):
        with self.assertRaises(ValidationError):
            env = Environment.create(self.session, 'test-env',
                                        config=self.config)
        env = Environment.create(self.session, 'testenv', config=self.config)
        keys = {k.replace('paths.', ''): self.config[k]
                          for k in self.config if
                          k.startswith('paths.')}

        for key, path in keys.iteritems():
            if key.startswith('virtualenv'):
                continue

            if key.startswith('cgroups'):
                continue

            self.log.debug("%s: %s", key, path)
            self.assertTrue(os.path.isdir(path))

        self.session.commit()
        self.assert_env_paths(env)

    def test_create_single_cgroup(self):
        controllers =  self.config['paths.cgroups.controllers']
        rel_path = self.config['paths.cgroups.relative_path']

        del self.config['paths.cgroups.controllers']
        self.config['paths.cgroups.relative_path'] = '/'

        env = Environment.create(self.session, 'testenv', config=self.config)
        self.session.commit()
        self.assert_env_paths(env)

        #restore options
        self.config['paths.cgroups.controllers'] = controllers
        self.config['paths.cgroups.realtive_path'] = rel_path
