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
                                Alias)
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound


@view_config(route_name='aliases', request_method=('HEAD', 'GET'))
def list(context, request):
    return {a.domain: a.to_dict() for a in Alias.all(request.db_session)}


@view_config(route_name='aliases', request_method='POST',
             renderer='taskresponse')
def create(context, request):
    try:
        domain = request.params['domain']
        instance = Instance.get_by_domain(request.db_session,
                                          request.params['destination'])
        check_domain_not_used(request, domain)

    except KeyError as e:
        raise ParamsError(e)

    except NoResultFound:
        raise ParamsError('No instance for domain {}'\
                        .format(request.params['destination']))

    else:
        params = dict(domain=domain, instance_id=instance.id)
        return request.submit_task('alias.create', **params)


@view_config(route_name='alias', request_method=('HEAD', 'GET'))
def info(context, request):
    return Alias.get(request.db_session,
                        request.matchdict['domain']).to_dict()


@view_config(route_name='alias', request_method='DELETE',
             renderer='taskresponse')
def delete(context, request):
    domain = request.matchdict['domain']
    Alias.get(request.db_session, domain)
    return request.submit_task('alias.delete', domain=domain)


@view_config(route_name='alias', request_method='PUT',
             renderer='taskresponse')
def update(context, request):

    params = dict()
    domain = request.matchdict['domain']
    Alias.get(request.db_session, domain)

    try:
        if "destination" in request.params:
            params['instance_id'] = Instance.get_by_domain(
                                            request.db_session,
                                            request.params['destination']).id
        if "new_domain" in request.params:
            check_domain_not_used(request, request.params['new_domain'])
            params['new_domain'] = validate_hostname(
                                             request.params['new_domain'])

    except NoResultFound:
        raise ParamsError("No instance for domain {}"\
                          .format(request.params['destination']))

    if not params:
        raise ParamsError("Missing update fields")

    params['domain'] = domain
    return request.submit_task('alias.update', **params)
