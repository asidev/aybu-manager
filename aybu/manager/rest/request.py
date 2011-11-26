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

import redis
import zmq
from aybu.core.request import BaseRequest
from aybu.manager.rest.zmq_util import ZmqTaskSender
from aybu.manager.task import Task


class Request(BaseRequest):

    _redis = None

    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        self.zmq_context = zmq.Context()

    @property
    def redis(self):
        if self._redis:
            return self._redis

        redis_opts = {k.replace('redis.', ''): self.registry.settings[k]
                      for k in self.registry.settings
                      if k.startswith('redis.')}
        if 'port' in redis_opts:
            redis_opts['port'] = int(redis_opts['port'])

        self._redis = redis.StrictRedis(**redis_opts)
        return self._redis

    def submit_task(self, resource, action, **data):
        s = ZmqTaskSender(self)
        task = Task(resource=resource, redis_client=self.redis,
                    action=action, **data)
        return s.submit(task)



