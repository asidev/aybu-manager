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
import zmq
from aybu.manager.utils.decorators import classproperty
from aybu.manager.task import ERROR, QUEUED, TaskResponse


class ZmqTaskSender(object):

    @classproperty
    @classmethod
    def log(cls):
        if hasattr(cls, "_log"):
            return cls._log

        cls._log = logging.getLogger("{}.{}".format(cls.__module__,
                                                    cls.__name__))
        return cls._log

    def __init__(self, request):
        self.context = request.zmq_context
        self.remote_addr = request.registry.settings['zmq.queue_addr']
        self.timeout = int(request.registry.settings['zmq.timeout'])
        self.socket = self.context.socket(zmq.REQ)
        self.log.info("Created zmq socket, connecting to %s", self.remote_addr)
        self.socket.connect(self.remote_addr)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    def submit(self, task, flags=0):
        try:
            data = task.to_dict()
            self.log.debug("Sending message: %s (flags=%s)", data, flags)
            self.socket.send_json(data, flags)
        except:
            self.log.exception('Error sending message to zmq')

        else:
            try:
                self.log.debug("Awaiting response from daemon")
                if self.poller.poll(self.timeout):
                    response = self.socket.recv_json()
                    self.log.debug("Received response from daemon: %s", response)
                    return TaskResponse(task, response)

                self.log.error("%s: Timeout while reading from daemon", task)
                return TaskResponse(
                        task,
                        dict(success=True,
                             message='Message enququed to be delivered'),
                        status=QUEUED,
                )

            except Exception as e:
                self.log.exception('Error reading response from zmq')
                return TaskResponse(task, dict(success=False, message=str(e)),
                                    status=ERROR)
