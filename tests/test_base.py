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

import configobj
import logging
import os
import shutil
import tempfile
import unittest
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from aybu.manager.models import Base
from aybu.manager.models import add_session_events

class BaseTests(unittest.TestCase):

    def setUp(self):
        self.log = logging.getLogger("{}.{}".format(self.__class__.__module__,
                                                    self.__class__.__name__))
        ini = os.path.realpath(
                os.path.join(os.path.dirname(__file__), "..", 'tests.ini'))

        self.config = configobj.ConfigObj(ini, file_error=True)
        self.engine = engine_from_config(self.config['manager'],
                                            'sqlalchemy.')
        self.Session = sessionmaker()
        self.session = self.Session()
        self.session.configure(bind=self.engine)
        add_session_events(self.session)
        Base.metadata.bind = self.engine
        Base.metadata.create_all()

        self.tempdir = tempfile.mkdtemp()
        self.config['paths']['root'] = self.tempdir
        self.config['paths']['cgroups'] = '%(root)s/cgroups'
        self.config['paths']['sites'] = '%(root)s/sites'
        self.config['paths']['configs'] = '%(root)s/configs'
        self.config['paths']['archives'] = '%(root)s/archives'
        self.config['paths']['run'] = '%(root)s/run'
        self.config['paths']['virtualenv'] = '%(root)s/virtualenv'
        self.config['paths']['logs'] = '%(root)s/logs'

    def tearDown(self):
        self.session.close()
        self.Session.close_all()
        Base.metadata.drop_all()
        shutil.rmtree(self.tempdir)
