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

import collections
import logging
import redis
import uuid as uuid_module
from aybu.manager.exc import TaskExistsError, TaskNotFoundError

TaskStatus = collections.namedtuple('TaskStatus', ['ERROR', 'UNDEF', 'DEFERRED',
                                                   'QUEUED', 'STARTED',
                                                   'FINISHED', 'FAILED'])
taskstatus = TaskStatus(
                ERROR="ERROR",
                UNDEF="UNDEF",
                DEFERRED="DEFERRED",
                QUEUED="QUEUED",
                STARTED="STARTED",
                FINISHED="FINISHED",
                FAILED="FAILED"
)
__all__ = ['Task', 'taskstatus', 'TaskResponse']


class Task(collections.MutableMapping):
    """ A dict mapped on redis that models a task.
        tasks are referred by uuid
    """
    def __init__(self, redis_client=None, redis_conf=None, new=False,
                 uuid=None, **kwargs):

        self.redis = self.redis_client_from_params(redis_conf, redis_client)
        uuid = uuid or uuid_module.uuid4().hex

        object.__setattr__(self, 'uuid', uuid)
        self.key = "task:{uuid}".format(uuid=uuid)
        self.logs_key = "{key}:logs".format(key=self.key)
        self.logs_counter_key = "{key}:index".format(key=self.logs_key)
        self.logs_levels_key = "logs:levels"

        if new and self.redis_client.exists(self.key):
            raise TaskExistsError('a task with uuid %s already exists' % (uuid))
        else:
            self.redis.sadd("tasks", self.uuid)

        for k, v in kwargs.items():
            self[k] = v

    def to_dict(self):
        return {k: v for k, v in self.iteritems()}

    @classmethod
    def redis_client_from_params(cls, redis_conf=None, redis_client=None):
        if not redis_conf and not redis_client:
            raise TypeError("redis_conf and redis_client cannot be both empty")

        elif not redis_client:
            redis_client = redis.StrictRedis(**redis_conf)

        return redis_client

    @classmethod
    def retrieve(cls, uuid, redis_conf=None, redis_client=None):
        redis_client = cls.redis_client_from_params(redis_conf, redis_client)
        if not redis_client.sismember('tasks', uuid):
            raise TaskNotFoundError(uuid)
        return cls(uuid=uuid, redis_client=redis_client)

    @classmethod
    def all(cls, redis_conf=None, redis_client=None):
        redis_client = cls.redis_client_from_params(redis_conf, redis_client)
        return (cls.retrieve(redis_client=redis_client, uuid=uuid)
                for uuid in redis_client.smembers('tasks'))

    @property
    def status(self):
        try:
            return self['status']
        except KeyError:
            return taskstatus.UNDEF

    @status.setter
    def status(self, st):
        self['status'] = st

    @property
    def command(self):
        return self['command']

    @command.setter
    def command(self, cmd):
        self['command'] = cmd

    @property
    def result(self):
        return self['result']

    @result.setter
    def result(self, value):
        self['result'] = value

    @property
    def command_name(self):
        return self['command'].split('.')[1]

    @property
    def command_module(self):
        return self['command'].split('.')[0]

    @property
    def command_args(self):
        return {k.replace('_arg.', ''): v for k, v in self.iteritems()
                if k.startswith('_arg.')}

    def __getattr__(self, attr):
        if attr.startswith("is_"):
            attr = attr.replace("is_", "")
            return self.status == getattr(taskstatus, attr.upper())
        raise AttributeError(attr)

    def __setattr__(self, attr, value):
        if attr == 'uuid':
            raise TypeError('Cannot reset uuid of an existing task')
        super(Task, self).__setattr__(attr, value)

    def keys(self):
        return self.redis.hkeys(self.key)

    def values(self):
        return self.redis.hvals(self.key)

    def items(self):
        return self.redis.hgetall(self.key).items()

    def __iter__(self):
        return iter(self.redis.hkeys(self.key))

    def __len__(self):
        return self.redis.hlen(self.key)

    def __contains__(self, item):
        return self.redis.hexists(self.key, item)

    def __getitem__(self, item):
        value = self.redis.hget(self.key, item)
        if not value:
            raise KeyError(item)
        return value

    def __delitem__(self, item):
        if item not in self:
            raise KeyError(item)
        self.redis.hdel(self.key, item)

    def __setitem__(self, item, value):
        self.redis.hset(self.key, item, value)

    def remove(self):
        """ remove the task and all its logs from redis """
        self.redis.srem('tasks', self.uuid)
        for key in self.redis.keys("{}*".format(self.key)):
            self.redis.delete(key)

    def flush_logs(self):
        """ remove all logs for the task """
        for key in self.redis.keys("{}*".format(self.logs_key)):
            self.redis.delete(key)

    def log_level_list_key(self, levelname):
        return "{key}:{level}".format(key=self.logs_key, level=levelname)

    def log(self, msg, levelname, ttl=None, levelno=None):
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
        try:
            lno = getattr(logging, levelname) if levelno is None else levelno
        except AttributeError:
            raise ValueError("Invalid levelname {}".format(levelname))

        index = self.redis.incr(self.logs_counter_key)
        level_key = self.log_level_list_key(levelname)
        self.redis.hset(self.logs_key, index, msg)
        self.redis.rpush(level_key, index)
        self.redis.zadd(self.logs_levels_key, lno, levelname)
        if ttl:
            self.redis.expire(self.logs_counter_key, ttl)
            self.redis.expire(level_key, ttl)
            self.redis.expire(self.logs_key, ttl)

    def get_logs(self, level):
        if not isinstance(level, int):
            level = getattr(logging, level)

        # use the levelno as score to get the wanted levels.
        # if we ask for DEBUG, we get all levels
        # if we ask for WARN, we get WARN, ERROR and CRITICAL
        levels = self.redis.zrangebyscore(self.logs_levels_key,
                                     float(level),
                                     float(logging.CRITICAL))

        # get all hash keys in the selected log levels
        msg_ids = []
        for level in levels:
            key = self.log_level_list_key(level)
            msg_ids.extend([int(k) for k in self.redis.lrange(key, 0, -1)])

        # now we have all the keys we are interested in so we can
        # return the log levels in the right order.
        if not msg_ids:
            return []
        return self.redis.hmget(self.logs_key, sorted(msg_ids))

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<Task uuid='{}' status='{}'>".format(self.uuid, self.status)


class TaskResponse(object):

    def __init__(self, task, values):
        self.success = values['success']
        self.message = values['message']
        self.task = task

    @property
    def status(self):
        return self.task.status

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<TaskResponse ({}) {}: {}>".format(self.task.uuid,
                                                   self.status,
                                                   self.message)

