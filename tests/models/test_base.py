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
import shutil
import tempfile
from sqlalchemy.orm import sessionmaker
from aybu.manager.activity_log import ActivityLog
from aybu.core.testing import TestsBase

from .. import (import_data,
                setup_metadata,
                create_tables,
                drop_tables)

class ManagerModelsTestsBase(TestsBase):

    def import_data(self):
        import_data(self.engine, self.Session)

    def new_session(self):
        if hasattr(self, 'session') and self.session:
            self.session.close()
            self.Session.close_all()
        self.session = self.Session()
        ActivityLog.attach_to(self.session)
        return self.session

    @classmethod
    def create_tables(cls, drop=False):
        """ avoid creating core tables """
        pass

    @classmethod
    def drop_tables(cls):
        """ avoid dropping core tables """
        pass

    def setUp(self):
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
        self.config['paths.virtualenv.default'] = \
                            os.path.dirname(os.environ['VIRTUAL_ENV'])
        self.config['paths.virtualenv.base'] = \
                            os.path.dirname(os.path.realpath(os.path.join(
                                os.environ['VIRTUAL_ENV'], '..')))
        self.config['virtualenv_name'] = \
                            os.path.basename(os.environ['VIRTUAL_ENV'])
        self.config['paths.logs'] = '{}/logs'.format(self.tempdir)

        # fake cgroups
        rel = self.config['paths.cgroups.relative_path']
        if rel.startswith('/'):
            rel = rel[1:]

        if not self.config['paths.cgroups.controllers']:
            cgroups = [os.path.join(self.config['paths.cgroups'], rel)]
        else:
            cgroups = [os.path.join(self.config['paths.cgroups'],
                                    ctrl.strip(),
                                    rel)
                       for ctrl in
                       self.config['paths.cgroups.controllers'].split(",")]
        for cgroup in cgroups:
            os.makedirs(cgroup)


    def tearDown(self):
        self.session.close()
        self.Session.close_all()
        drop_tables()
        shutil.rmtree(self.tempdir)
