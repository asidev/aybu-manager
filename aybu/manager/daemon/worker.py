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

from sqlalchemy import engine_from_config
from sqlalchemy.orm import (sessionmaker,
                            scoped_session)
from aybu.manager.models import Base
from aybu.manager.activity_log import ActivityLog
import logging


class AybuManagerWorker(object):

    def __init__(self, config):
        self.config = config
        self.log = logging.getLogger(__name__)
        self.engine = engine_from_config(self.config, 'sqlalchemy.')
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        Base.metadata.bind = self.engine
        Base.metadata.create_all()

    def _new_database_session(self):
        if hasattr(self, '__db'):
            self.__db.close()
            self.Session.remove()

        db = self.Session()
        ActivityLog.attach_to(db)
        self.__db = db
        return db

    def start(self):
        self.log.info("Starting daemon")
        db = self._new_database_session()
        from aybu.manager.models import Instance
        self.log.info(db.query(Instance).all())
