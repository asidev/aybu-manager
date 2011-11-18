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

from aybu.manager.models import (Environment,
                                 Instance,
                                 User)
from . test_base import BaseTests
import os
import shlex
import subprocess
import time
import urllib2


class InstanceTests(BaseTests):

    def test_deploy(self):

        owner = User(email='info@example.com', password='changeme',
                     name='Example', surname='Com')
        env = Environment.create(self.session, 'testenv', config=self.config,
                                venv_name=self.config['virtualenv_name'])
        instance = Instance.deploy(self.session, 'www.example.com', owner,
                                   env, owner)

        self.session.rollback()

        """
        self.session.commit()
        venv = os.environ['VIRTUAL_ENV']
        bin_ = os.path.join(venv, 'bin')
        cmd = "{}/uwsgi --http 0.0.0.0:9876 --ini {}"\
                .format(bin_, instance.paths.vassal_config)

        uwsgi = subprocess.Popen(shlex.split(cmd))
        time.sleep(3)
        res = urllib2.urlopen("http://127.0.0.1:9876/")
        self.assertEqual(res.code, 200)
        uwsgi.kill()
        """