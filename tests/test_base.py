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
                os.path.join(os.path.dirname(__file__), "..", 'tests.ini'))

        self.config = configobj.ConfigObj(ini, file_error=True)
        self.engine = engine_from_config(self.config['app:aybu-manager'],
                                        'sqlalchemy.')
        Base.metadata.bind = self.engine
        Base.metadata.create_all()
        self.Session = sessionmaker(bind=self.engine)
        self.new_session()

        self.tempdir = tempfile.mkdtemp()
        self.config['app:aybu-manager']['paths.root'] = self.tempdir
        self.config['app:aybu-manager']['paths.cgroups'] = '%(paths.root)s/cgroups'
        self.config['app:aybu-manager']['paths.sites'] = '%(paths.root)s/sites'
        self.config['app:aybu-manager']['paths.configs'] = '%(paths.root)s/configs'
        self.config['app:aybu-manager']['paths.archives'] = '%(paths.root)s/archives'
        self.config['app:aybu-manager']['paths.run'] = '%(paths.root)s/run'
        self.config['app:aybu-manager']['paths.virtualenv'] = \
                            os.path.dirname(os.environ['VIRTUAL_ENV'])
        self.config['app:aybu-manager']['virtualenv_name'] = \
                            os.path.basename(os.environ['VIRTUAL_ENV'])
        self.config['app:aybu-manager']['paths.logs'] = '%(paths.root)s/logs'

    def tearDown(self):
        self.session.close()
        self.Session.close_all()
        Base.metadata.drop_all()
        shutil.rmtree(self.tempdir)
