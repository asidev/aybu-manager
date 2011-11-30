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


from aybu.manager.exc import ParamsError
from aybu.manager.models import Environment
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound
from pyramid.httpexceptions import HTTPConflict


@view_config(route_name='environments', request_method='GET')
def list(context, request):
    return [e.to_dict() for e in Environment.all(request.db_session)]


@view_config(route_name='environments', request_method='POST',
             renderer='taskresponse')
def create(context, request):
    try:
        name = request.params['name']
        virtualenv_name = request.params.get('virtualenv_name')
        # try to get the env from db, as it must not exists
        Environment.get(request.db_session, name)

    except KeyError as e:
        raise ParamsError(e)

    except NoResultFound:
        # no env found, submit the task
        return request.submit_task('environment.create', name=name,
                                   virtualenv_name=virtualenv_name)

    else:
        # found instance, give conflict
        error = 'environment {} already exists'.format(name)
        return HTTPConflict(headers={'X-Request-Error': error})


@view_config(route_name='environment', request_method=('HEAD', 'GET'))
def info(context, request):
    return Environment.get(request.db_session,
                           request.matchdict['name']).to_dict()


@view_config(route_name='environment', request_method='DELETE')
def remove(context, request):
    raise NotImplementedError


@view_config(route_name='environment', request_method='PUT')
def update(context, request):
    raise NotImplementedError


