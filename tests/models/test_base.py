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

import ConfigParser
import logging
import os
import shutil
import tempfile
import unittest
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from aybu.manager.activity_log import ActivityLog

from .. import (import_data,
                setup_metadata,
                create_tables,
                drop_tables)

class BaseTests(unittest.TestCase):

    def import_data(self):
        import_data(self.engine, self.Session)

    def new_session(self):
        if hasattr(self, 'session') and self.session:
            self.session.close()
            self.Session.close_all()
        self.session = self.Session()
        ActivityLog.attach_to(self.session)
        return self.session

    def setUp(self):
        self.log = logging.getLogger("{}.{}".format(self.__class__.__module__,
                                                    self.__class__.__name__))
        ini = os.path.realpath(
                os.path.join(os.path.dirname(__file__), "..", "..",
                             'tests.ini'))

        config = ConfigParser.ConfigParser()
        with open(ini) as f:
            config.readfp(f)
        self.config = {k: v for k,v in config.items('app:aybu-manager')}
        self.engine = engine_from_config(self.config,
                                        'sqlalchemy.')
        self.Session = sessionmaker(bind=self.engine)
        self.new_session()
        setup_metadata(self.engine)
        create_tables()

        self.tempdir = tempfile.mkdtemp()
        self.config['paths.root'] = self.tempdir
        self.config['paths.cgroups'] = '{}/cgroups'.format(self.tempdir)
        self.config['paths.sites'] = '{}/sites'.format(self.tempdir)
        self.config['paths.configs'] = '{}/configs'.format(self.tempdir)
        self.config['paths.archives'] = '{}/archives'.format(self.tempdir)
        self.config['paths.run'] = '{}/run'.format(self.tempdir)
        self.config['paths.virtualenv'] = \
                            os.path.dirname(os.environ['VIRTUAL_ENV'])
        self.config['virtualenv_name'] = \
                            os.path.basename(os.environ['VIRTUAL_ENV'])
        self.config['paths.logs'] = '{}/logs'.format(self.tempdir)

    def tearDown(self):
        self.session.close()
        self.Session.close_all()
        drop_tables()
        shutil.rmtree(self.tempdir)
