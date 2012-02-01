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
from aybu.manager.exc import (ParamsError,
                              TaskExistsError,
                              TaskNotFoundError,
                              ValidationError)
from pyramid.view import view_config
from pyramid.httpexceptions import (HTTPBadRequest,
                                    HTTPNoContent,
                                    HTTPCreated,
                                    HTTPUnauthorized,
                                    HTTPForbidden,
                                    HTTPNotFound,
                                    HTTPConflict,
                                    HTTPPreconditionFailed,
                                    HTTPNotImplemented)
from pyramid.security import (NO_PERMISSION_REQUIRED,
                              authenticated_userid)

from sqlalchemy.orm.exc import NoResultFound


DISABLED_METH_COLL = ('DELETE', 'PUT', 'OPTIONS', 'TRACE', 'CONNECT')
DISABLED_METH_OBJ = ('POST', 'OPTIONS', 'TRACE', 'CONNECT')
log = logging.getLogger(__name__)


def generate_empty_response(context, request, status, add_headers={}):
    response = request.response
    response.status_int = status
    if hasattr(context, 'headers') and context.headers:
        response.headers = context.headers
    response.headers.update(
        {'Content-Length': 0,
         'Content-Type': 'application/json; charset=UTF-8'}
    )
    response.body = ''
    response.headers.update(add_headers)
    # TODO add logging with ip/user/agent etc etc
    log.info("Generating empty response [status: %s, headers:%s]",
              status, response.headers)
    log.debug("request: %s", request)
    log.debug("response: %s", response)
    return response


@view_config(route_name='archives', request_method=DISABLED_METH_COLL)
@view_config(route_name='archive', request_method=DISABLED_METH_OBJ)
@view_config(route_name='instances', request_method=('DELETE', 'OPTIONS',
                                                     'TRACE', 'CONNECT'))
@view_config(route_name='instance', request_method=DISABLED_METH_OBJ)
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


@view_config(context=HTTPCreated, permission=NO_PERMISSION_REQUIRED)
@view_config(context=HTTPNoContent, permission=NO_PERMISSION_REQUIRED)
@view_config(context=HTTPUnauthorized, permission=NO_PERMISSION_REQUIRED)
@view_config(context=HTTPForbidden, permission=NO_PERMISSION_REQUIRED)
@view_config(context=HTTPNotFound, permission=NO_PERMISSION_REQUIRED)
@view_config(context=HTTPBadRequest, permission=NO_PERMISSION_REQUIRED)
@view_config(context=HTTPConflict, permission=NO_PERMISSION_REQUIRED)
@view_config(context=HTTPPreconditionFailed, permission=NO_PERMISSION_REQUIRED)
def created(context, request):
    if isinstance(context, HTTPForbidden) and \
       not authenticated_userid(request):
        code = 401
        context = HTTPUnauthorized()
    else:
        code = context.code
    return generate_empty_response(context, request, code)


@view_config(context=TaskNotFoundError, permission=NO_PERMISSION_REQUIRED)
@view_config(context=NoResultFound, permission=NO_PERMISSION_REQUIRED)
def not_found(context, request):
    return generate_empty_response(context, request, 404)


@view_config(context=ParamsError, permission=NO_PERMISSION_REQUIRED)
@view_config(context=ValidationError, permission=NO_PERMISSION_REQUIRED)
def bad_request(context, request):
    return generate_empty_response(context, request, 400,
                                   {'X-Request-Error': str(context)})


@view_config(context=TaskExistsError, permission=NO_PERMISSION_REQUIRED)
def conflict(context, request):
    return generate_empty_response(context, request, 409)


@view_config(context=NotImplementedError, permission=NO_PERMISSION_REQUIRED)
@view_config(context=HTTPNotImplemented, permission=NO_PERMISSION_REQUIRED)
def not_implemented(context, request):
    return generate_empty_response(context, request, 501)


def unauthorized(context, request):
    return generate_empty_response(context, request, 401)
