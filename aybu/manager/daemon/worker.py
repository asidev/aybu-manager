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
import threading
import zmq


class AybuManagerDaemonWorker(threading.Thread):

    def __init__(self, context, config):
        super(AybuManagerDaemonWorker, self).__init__(name='worker')
        self.config = config
        self.log = logging.getLogger(__name__)
        self.context = context
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

    def run(self):

        self.log.debug("Worker starting ... ")
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, "")  # subscribe to all
        self.socket.connect('inproc://tasks')

        while True:
            message = self.socket.recv_pyobj()
            self.log.info("Received task %s", message)

        self.socket.close()
