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
import pkg_resources
import shutil
import tempfile
import unittest
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from aybu.manager.models import Base, import_from_json
from aybu.manager.activity_log import ActivityLog

class BaseTests(unittest.TestCase):

    def import_data(self):
        session = self.Session()
        session.configure(bind=self.engine)
        try:
            import_from_json(session,
                            pkg_resources.resource_stream('aybu.manager.data',
                                                        'manager_themes.json'))
            session.flush()

        except:
            self.log.exception("Error while importing data")
            session.rollback()
            raise

        else:
            session.commit()

        finally:
            session.close()

    def setUp(self):
        self.log = logging.getLogger("{}.{}".format(self.__class__.__module__,
                                                    self.__class__.__name__))
        ini = os.path.realpath(
                os.path.join(os.path.dirname(__file__), "..", 'tests.ini'))

        self.config = configobj.ConfigObj(ini, file_error=True)
        self.engine = engine_from_config(self.config['manager'],
                                            'sqlalchemy.')
        Base.metadata.bind = self.engine
        Base.metadata.create_all()

        self.Session = sessionmaker()
        self.session = self.Session()
        self.session.configure(bind=self.engine)
        ActivityLog.attach_to(self.session)

        self.tempdir = tempfile.mkdtemp()
        self.config['paths']['root'] = self.tempdir
        self.config['paths']['cgroups'] = '%(root)s/cgroups'
        self.config['paths']['sites'] = '%(root)s/sites'
        self.config['paths']['configs'] = '%(root)s/configs'
        self.config['paths']['archives'] = '%(root)s/archives'
        self.config['paths']['run'] = '%(root)s/run'
        self.config['paths']['virtualenv'] = \
                            os.path.dirname(os.environ['VIRTUAL_ENV'])
        self.config['virtualenv_name'] = \
                            os.path.basename(os.environ['VIRTUAL_ENV'])
        self.config['paths']['logs'] = '%(root)s/logs'

    def tearDown(self):
        self.session.close()
        self.Session.close_all()
        Base.metadata.drop_all()
        shutil.rmtree(self.tempdir)
