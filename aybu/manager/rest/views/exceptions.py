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
                                    HTTPNotFound,
                                    HTTPMethodNotAllowed,
                                    HTTPConflict,
                                    HTTPNotImplemented)

from sqlalchemy.orm.exc import NoResultFound


@view_config(route_name='archives', request_method=('DELETE', 'HEAD', 'PUT'))
@view_config(route_name='archive', request_method='POST')
@view_config(route_name='instances', request_method=('DELETE', 'HEAD', 'PUT'))
@view_config(route_name='instance', request_method='POST')
@view_config(route_name='themes', request_method=('DELETE', 'HEAD', 'PUT'))
@view_config(route_name='theme', request_method='POST')
@view_config(route_name='redirects', request_method=('DELETE', 'HEAD', 'PUT'))
@view_config(route_name='redirect', request_method='POST')
@view_config(route_name='users', request_method=('DELETE', 'HEAD', 'PUT'))
@view_config(route_name='user', request_method='POST')
@view_config(route_name='tasks', request_method=('POST', 'PUT', 'HEAD'))
@view_config(route_name='task', request_method=('POST', 'PUT'))
@view_config(route_name='tasklogs', request_method=('HEAD', 'POST', 'PUT'))
@view_config(route_name='environments',
             request_method=('DELETE', 'HEAD', 'PUT'))
@view_config(route_name='environment', request_method='POST')
def method_not_allowed(context, request):
    return HTTPMethodNotAllowed()


@view_config(context=TaskNotFoundError)
@view_config(context=NoResultFound)
def not_found(context, request):
    return HTTPNotFound()


@view_config(context=ParamsError)
@view_config(context=ValidationError)
def params_error(context, request):
    return HTTPBadRequest(headers={'X-Request-Error': str(context)})


@view_config(context=TaskExistsError)
def task_exists(context, request):
    return HTTPConflict()


@view_config(context=NotImplementedError)
def not_implemented(contex, request):
    return HTTPNotImplemented()
