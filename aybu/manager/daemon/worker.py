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
from aybu.manager.models import Base, Environment
from aybu.manager.activity_log import ActivityLog
from aybu.manager.task import Task, taskstatus
from . handlers import RedisPUBHandler
import datetime
import logging
import redis
import threading
import zmq


class AybuManagerDaemonWorker(threading.Thread):

    def __init__(self, context, config):
        super(AybuManagerDaemonWorker, self).__init__(name='worker')
        self.config = config
        self.log = logging.getLogger(__name__)
        self.context = context
        self.engine = engine_from_config(self.config, 'sqlalchemy.')
        self.Session = scoped_session(sessionmaker(bind=self.engine,
                                                   autocommit=True))
        Base.metadata.bind = self.engine
        Base.metadata.create_all()
        redis_opts = {k.replace('redis.', ''): self.config[k]
                      for k in self.config
                      if k.startswith('redis.')}
        if 'port' in redis_opts:
            redis_opts['port'] = int(redis_opts['port'])

        self.redis = redis.StrictRedis(**redis_opts)
        self.pub_socket = self.context.socket(zmq.PUB)
        self.pub_socket.bind(self.config['zmq.status_pub_addr'])
        Environment.initialize(self.config, section=None)

    def run(self):

        self.log.debug("Worker starting ... ")
        self.socket = self.context.socket(zmq.SUB)
        self.socket.setsockopt(zmq.SUBSCRIBE, "")  # subscribe to all
        self.socket.connect('inproc://tasks')
        handler = RedisPUBHandler(self.config, self.pub_socket, self.context)
        log = logging.getLogger('aybu')
        log.addHandler(handler)

        while True:
            task = Task(uuid=self.socket.recv(),
                        redis_client=self.redis,
                        started=datetime.datetime.now())
            handler.set_task(task)
            db = self.Session()
            db.begin()
            if not hasattr(db, 'activity_log'):
                ActivityLog.attach_to(db)
            log.setLevel(task.get('log_level', logging.DEBUG))

            try:
                module_name = 'aybu.manager.daemon.commands.{}'\
                        .format(task.command_module)
                module = __import__(module_name,
                                    fromlist=[task.command_name])
                function = getattr(module, task.command_name)
                result = function(db, task, **task.command_args)
                db.commit()

            except ImportError as e:
                db.rollback()
                task.status = taskstatus.FAILED
                task.result = "Cannot found resource {}"\
                        .format(task.command_module)
                log.exception(task.result)

            except AttributeError as e:
                db.rollback()
                task.status = taskstatus.FAILED
                task.result = "Cannot found action {} on {}"\
                        .format(task.command_name, task.command_module)
                log.critical(task.result)

            except Exception as e:
                db.rollback()
                log.exception('Error while executing task')
                task.status = taskstatus.FAILED
                task.result = str('Error')

            else:
                task.status = taskstatus.FINISHED
                task.result = result or ''
                log.info("Task completed successfully")

            finally:
                task['finished'] = datetime.datetime.now()
                self.pub_socket.send_multipart(["{}.finished".format(task.uuid),
                                                "task endend"])
                db.close()

        self.socket.close()
