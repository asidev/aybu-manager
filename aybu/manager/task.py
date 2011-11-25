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

import uuid

DELIVERED = "DELIVERED"
QUEUED = "QUEUED"
ERROR = "ERROR"


class Task(object):

    def __init__(self, resource, action, **kwargs):
        self.uuid = uuid.uuid4().hex \
                    if 'uuid' not in kwargs \
                    else kwargs['uuid']
        self.resource = resource
        self.action = action
        self.kwargs = kwargs
        self.kwargs.update(dict(uuid=self.uuid,
                                action=action,
                                resource=resource))
        for arg, value in kwargs.iteritems():
            setattr(self, arg, value)

    def to_dict(self):
        return self.kwargs

    @classmethod
    def from_dict(cls, data):
        t = cls(**data)
        t.uuid = str(t.uuid)
        return t

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<Task {} {}.{}({})>"\
            .format(self.uuid, self.resource, self.action, ", ".join(
                ["{}={}".format(k, v)
                 for k, v in self.kwargs.iteritems()
                 if k not in ("uuid", "resource", "action")]))


class TaskResponse(object):

    def __init__(self, task, values, status=DELIVERED):
        self.success = values['success']
        self.message = values['message']
        self.task = task
        self.status = status

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<TaskResponse ({}) {}: {}>".format(self.task.uuid,
                                                   self.status,
                                                   self.message)

