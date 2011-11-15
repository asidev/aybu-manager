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
import unittest
import os
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from aybu.manager.models import Base

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
        Base.metadata.bind = self.engine
        Base.metadata.create_all()


    def tearDown(self):
        self.session.close()
        self.Session.close_all()
        Base.metadata.drop_all()

