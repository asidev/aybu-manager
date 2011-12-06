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


from aybu.manager.exc import (ParamsError,
                              TaskExistsError,
                              TaskNotFoundError,
                              ValidationError)
from pyramid.view import view_config
from pyramid.httpexceptions import (HTTPBadRequest,
                                    HTTPNoContent,
                                    HTTPCreated,
                                    HTTPNotFound,
                                    HTTPConflict,
                                    HTTPPreconditionFailed,
                                    HTTPNotImplemented)

from sqlalchemy.orm.exc import NoResultFound


def generate_empty_response(context, request, status, add_headers={}):
    response = request.response
    response.status_int = status
    if hasattr(context, 'headers') and context.headers:
        response.headers = context.headers
    response.headers.update({'Content-Length': 0,
                             'Content-Type': 'application/json; charset=UTF-8'})
    response.headers.update(add_headers)
    return response


DISABLED_METH_COLL = ('DELETE', 'PUT', 'OPTIONS', 'TRACE', 'CONNECT')
DISABLED_METH_OBJ = ('POST', 'OPTIONS', 'TRACE', 'CONNECT')
ALL_BUT_GET = ('DELETE', 'PUT', 'OPTIONS', 'TRACE', 'CONNECT', 'PUT')


@view_config(route_name='archives', request_method=DISABLED_METH_COLL)
@view_config(route_name='archive', request_method=DISABLED_METH_OBJ)
@view_config(route_name='instances', request_method=DISABLED_METH_COLL)
@view_config(route_name='instance', request_method=DISABLED_METH_COLL)
@view_config(route_name='themes', request_method=DISABLED_METH_COLL)
@view_config(route_name='theme', request_method=DISABLED_METH_OBJ)
@view_config(route_name='redirects', request_method=DISABLED_METH_COLL)
@view_config(route_name='redirect', request_method=DISABLED_METH_OBJ)
@view_config(route_name='users', request_method=DISABLED_METH_COLL)
@view_config(route_name='user', request_method=DISABLED_METH_OBJ)
@view_config(route_name='tasks',
             request_method=('POST', 'PUT', 'OPTIONS', 'TRACE', 'CONNECT'))
@view_config(route_name='task',
             request_method=('POST', 'PUT', 'OPTIONS', 'TRACE', 'CONNECT'))
@view_config(route_name='tasklogs',
             request_method=('POST', 'PUT', 'OPTIONS', 'TRACE', 'CONNECT'))
@view_config(route_name='environments', request_method=DISABLED_METH_COLL)
@view_config(route_name='environment', request_method=DISABLED_METH_OBJ)
@view_config(route_name='groups', request_method=DISABLED_METH_COLL)
@view_config(route_name='group', request_method=DISABLED_METH_OBJ)
def method_not_allowed(context, request):
    return generate_empty_response(context, request, 405)


@view_config(context=HTTPCreated)
@view_config(context=HTTPNoContent)
@view_config(context=HTTPNotFound)
@view_config(context=HTTPBadRequest)
@view_config(context=HTTPConflict)
@view_config(context=HTTPPreconditionFailed)
def created(context, request):
    return generate_empty_response(context, request, context.code)


@view_config(context=TaskNotFoundError)
@view_config(context=NoResultFound)
def not_found(context, request):
    return generate_empty_response(context, request, 404)


@view_config(context=ParamsError)
@view_config(context=ValidationError)
def bad_request(context, request):
    return generate_empty_response(context, request, 400,
                                   {'X-Request-Error': str(context)})


@view_config(context=TaskExistsError)
def conflict(context, request):
    return generate_empty_response(context, request, 409)


@view_config(context=NotImplementedError)
@view_config(context=HTTPNotImplemented)
def not_implemented(context, request):
    return generate_empty_response(context, request, 501)
