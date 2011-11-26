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

from redis import WatchError
import logging
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

        # these are not in kwargs, so they will not serialized
        self.logs_key = "task:{uuid}:logs".format(uuid=self.uuid)
        self.logs_counter_key = "{key}:index".format(key=self.logs_key)
        self.logs_levels_key = "logs:levels"

    def log_level_list_key(self, levelname):
        return "{key}:{level}".format(key=self.logs_key, level=levelname)

    def log(self, redis, msg, levelname, ttl=None, levelno=None):
        """ Logs a message into redis.
            logs are organized inside redis as multiple keys

            'task:$uuid:logs' is an hash with auto-incr integer keys (the index
            is stored in 'task:$uuid:logs:index') and whose values is the log
            message itself. For every loglevel, a list 'task:$uuid:logs:$level'
            is created, storing hash indexes for the loglevel.
            This way we preserve messages' order, and we have a nice way to get
            all "DEBUG" message or "INFO" message by looking into the level lists.
            We keep another sorted set in which we keep the mapping between
            levelname and levelno to ease retrieving

            Note: we can't store log messages in the sorted set directly as we
            lost replicate messages with the same score (members in sorted sets
            are unique while score can be replicated)
        """

        lno = levelno if not levelno is None else getattr(logging, levelname)


        index = redis.incr(self.logs_counter_key)
        level_key = self.log_level_list_key(levelname)
        redis.hset(self.logs_key, index, msg)
        redis.rpush(level_key, index)
        redis.zadd(self.logs_levels_key, lno, levelname)
        if ttl:
            redis.expire(self.logs_counter_key, ttl)
            redis.expire(level_key, ttl)
            redis.expire(self.logs_key, ttl)

    def get_logs(self, redis, level):
        if not isinstance(level, int):
            level = getattr(logging, level)

        # use the levelno as score to get the wanted levels.
        # if we ask for DEBUG, we get all levels
        # if we ask for WARN, we get WARN, ERROR and CRITICAL
        levels = redis.zrangebyscore(self.logs_levels_key,
                                     float(level),
                                     float(logging.CRITICAL))

        # get all hash keys in the selected log levels
        msg_ids = []
        for level in levels:
            key = self.log_level_key(level)
            msg_ids.extend([int(k) for k in redis.lrange(key, 0, -1)])

        # now we have all the keys we are interested in so we can
        # return the log levels in the right order.
        return redis.hmget(self.logs_key, sorted(msg_ids))

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

