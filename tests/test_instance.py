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
from aybu.manager.models import (Environment,
                                 Instance,
                                 User)
from . test_base import BaseTests


class InstanceTests(BaseTests):

    def test_deploy(self):

        owner = User(email='info@example.com', password='changeme',
                     name='Example', surname='Com')
        env = Environment.create(self.session, 'testenv', config=self.config)
        # create a fake python to make pip install work
        os.mkdir(os.path.dirname(env.paths.virtualenv))
        os.mkdir(env.paths.virtualenv)
        os.mkdir(os.path.join(env.paths.virtualenv, 'bin'))
        with open(os.path.join(env.paths.virtualenv, 'bin', 'python'), 'w') as f:
            f.write('#!/bin/bash')
        os.chmod(os.path.join(env.paths.virtualenv, 'bin', 'python'), 0777)

        instance = Instance.deploy(self.session, 'www.example.com', owner,
                                   env, owner)
        self.session.commit()

