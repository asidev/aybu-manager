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
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPNoContent
from aybu.manager.task import Task


log = logging.getLogger(__name__)

def get_task(request):
    return Task.retrieve(uuid=request.matchdict['uuid'],
                    redis_client=request.redis)

@view_config(route_name='tasks', request_method='GET')
def list(context, request):
    return [task.uuid for task in Task.all(redis_client=request.redis)]


@view_config(route_name='tasks', request_method='DELETE')
def flush(context, request):
    for task in Task.all(redis_client=request.redis):
        task.remove()
    return HTTPNoContent()


@view_config(route_name='task', request_method=('HEAD', 'GET'))
def info(context, request):
    return get_task(request).to_dict()


@view_config(route_name='task', request_method='DELETE')
def remove(context, request):
    get_task(request).remove()


@view_config(route_name='tasklogs', request_method='GET')
def get_logs(context, request):
    level = request.params.get('level', 'debug').upper()
    return get_task(request).get_logs(level)


@view_config(route_name='tasklogs', request_method='DELETE')
def flush_logs(context, request):
    get_task(request).flush_logs()
    return HTTPNoContent()
