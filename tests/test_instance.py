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
from aybu.manager.exc import OperationalError
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

        # vassal config is created only upon session commit
        self.assertFalse(os.path.exists(instance.paths.vassal_config))
        self.session.commit()
        self.assertTrue(os.path.exists(instance.paths.vassal_config))

        # test reload
        os.unlink(instance.paths.vassal_config)
        instance.reload()
        self.assertFalse(os.path.exists(instance.paths.vassal_config))
        self.session.commit()
        self.assertTrue(os.path.exists(instance.paths.vassal_config))
        self.assertTrue(instance.enabled)

        # test disable
        instance.disable()
        self.session.commit()
        self.assertFalse(os.path.exists(instance.paths.vassal_config))
        with self.assertRaises(OperationalError):
            instance.reload()

        # disable an already disable instance is a no-op
        self.assertFalse(instance.enabled)
        instance.disable()
        self.session.rollback()
        self.assertFalse(instance.enabled)

        # test enable
        instance.enable()
        self.assertFalse(os.path.exists(instance.paths.vassal_config))
        self.session.commit()
        self.assertTrue(os.path.exists(instance.paths.vassal_config))

        # enabling an already enabled instance is a no-op
        self.assertTrue(instance.enabled)
        instance.enable()
        self.session.rollback()
        self.assertTrue(instance.enabled)

        # test delete
        with self.assertRaises(OperationalError):
            instance.delete()
        instance.disable()
        self.session.commit()
        instance.delete()
        self.assertFalse(os.path.exists(instance.paths.dir))
        self.session.commit()
        self.assertFalse(os.path.exists(instance.paths.dir))

        # todo assert database is not present

        raise Exception("finish")
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
