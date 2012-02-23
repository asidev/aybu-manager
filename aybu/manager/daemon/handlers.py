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
from zmq.log.handlers import (TOPIC_DELIM,
                              PUBHandler)


class RedisPUBHandler(PUBHandler):

    def __init__(self, config, socket, context, level=logging.NOTSET):
        self.context = context
        self.config = config

        self.ttl = self.config.get('zmq.result_ttl')
        super(RedisPUBHandler, self).__init__(socket, context)
        self.setLevel(level)
        self.task = None

    def set_task(self, task):
        self.task = task
        self.root_topic = task.uuid

    def emit(self, record):
        """Emit a log message on my socket."""
        try:
            topic, record.msg = record.msg.split(TOPIC_DELIM, 1)
            topic = topic.encode()
        except:
            topic = "".encode()

        try:
            msg = self.format(record).encode()

        except (KeyboardInterrupt, SystemExit):
            raise

        except:
            msg = ""
            self.handleError(record)

        topic_list = []
        if self.root_topic:
            topic_list.append(self.root_topic)

        topic_list.append(record.levelname.encode())

        if topic:
            topic_list.append(topic)

        topic = '.'.encode().join(topic_list)

        # map str, since sometimes we get unicode, and zmq can't deal with it
        self.socket.send_multipart([topic, msg])
        if self.task:
            self.task.log(msg, record.levelname, self.ttl,
                          levelno=record.levelno)
