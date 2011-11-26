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

import logging
import redis
import zmq
from aybu.manager.task import Task, taskstatus
from . worker import AybuManagerDaemonWorker


class AybuManagerDaemon(object):

    def __init__(self, config):

        self.config = config
        self.log = logging.getLogger(__name__)
        self.context = zmq.Context()
        self.worker = AybuManagerDaemonWorker(self.context, self.config)
        redis_opts = {k.replace('redis.', ''): self.config[k]
                      for k in self.config
                      if k.startswith('redis.')}
        if 'port' in redis_opts:
            redis_opts['port'] = int(redis_opts['port'])

        self.redis = redis.StrictRedis(**redis_opts)

    def start(self):
        self.log.info("Starting daemon")

        self.client_socket = self.context.socket(zmq.REP)
        self.worker_socket = self.context.socket(zmq.PUB)
        self.worker_socket.setsockopt(zmq.LINGER, 0)
        self.client_socket.bind(self.config['zmq.daemon_addr'])
        self.worker_socket.bind('inproc://tasks')

        self.log.debug("Starting worker")
        self.worker.start()

        self.log.info("Listening on %s", self.config['zmq.daemon_addr'])

        while True:
            try:
                message = self.client_socket.recv()
                self.worker_socket.send(message)
                task = Task(uuid=message, redis_client=self.redis)
                task.status = taskstatus.QUEUED

            except Exception as e:
                self.log.exception(e)
                success = False
                response = str(e)

            else:
                self.log.debug("received message: %s", message)
                success = True
                response = 'Task enqueued'

                try:
                    self.client_socket.send_json(dict(success=success,
                                                      message=response))
                except:
                    self.log.exception("Error sending reply")

        # we never get here...
        self.worker_socket.close()
        self.client_socket.close()
        self.context.term()

