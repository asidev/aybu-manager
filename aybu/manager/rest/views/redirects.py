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
from aybu.manager.models.validators import (validate_hostname,
                                            check_domain_not_used)
from aybu.manager.exc import ParamsError
from aybu.manager.models import (Instance,
                                 Redirect)
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound


@view_config(route_name='redirects', request_method=('HEAD', 'GET'))
def list(context, request):
    return {r.source: r.to_dict() for r in Redirect.all(request.db_session)}


@view_config(route_name='redirects', request_method='POST',
             renderer='taskresponse')
def create(context, request):
    try:
        source = validate_hostname(request.params['source'])
        instance = Instance.get_by_domain(request.db_session,
                                        request.params['destination'])
        http_code = request.params.get('http_code', 301)
        target_path = request.params.get('target_path', '')

        check_domain_not_used(request, source)

    except KeyError as e:
        raise ParamsError(e)

    except NoResultFound:
        raise ParamsError('No instance for domain {}'\
                        .format(request.params['destination']))

    else:
        params = dict(source=source, instance_id=instance.id,
                      http_code=http_code, target_path=target_path)
        return request.submit_task('redirect.create', **params)


@view_config(route_name='redirect', request_method=('HEAD', 'GET'))
def info(context, request):
    return Redirect.get(request.db_session,
                        request.matchdict['source']).to_dict()


@view_config(route_name='redirect', request_method='DELETE',
             renderer='taskresponse')
def delete(context, request):
    source = request.matchdict['source']
    Redirect.get(request.db_session, source)
    return request.submit_task('redirect.delete', source=source)


@view_config(route_name='redirect', request_method='PUT',
             renderer='taskresponse')
def update(context, request):

    params = dict()
    source = request.matchdict['source']
    Redirect.get(request.db_session, source)

    specs = (
       ('new_source', check_domain_not_used, [request]),
       ('destination', Instance.get_by_domain, [request.db_session]),
       ('http_code', None, None),
       ('target_path', None, None)
    )
    try:
        for attr, validate_fun, fun_args in specs:
            if attr in request.params:
                if validate_fun:
                    fun_args.append(request.params[attr])
                    params[attr] = validate_fun(*fun_args)
                else:
                    params[attr] = request.params[attr]

    except NoResultFound:
        raise ParamsError("No instance for domain {}"\
                          .format(request.params['destination']))

    if not params:
        raise ParamsError("Missing update fields")

    params['source'] = source
    if "destination" in params:
        params['instance_id'] = params['destination'].id
        del params['destination']

    if "new_source" in params:
        params['new_source'] = validate_hostname(params['new_source'])

    return request.submit_task('redirect.update', **params)
