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
from aybu.manager.models import Instance
from aybu.manager.exc import ParamsError
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPConflict
from sqlalchemy.orm.exc import NoResultFound


log = logging.getLogger(__name__)


@view_config(route_name='instances', request_method='GET')
def list(context, request):
    return {i.domain: i.to_dict() for i in Instance.all(request.db_session)}


@view_config(route_name='instances', request_method='POST',
             renderer='taskresponse')
def deploy(context, request):
    try:
        params = dict(
            domain=request.params['domain'],
            owner_email=request.params['owner_email'],
            environment_name=request.params['environment_name'],
            technical_contact_email=request.params['technical_contact_email'],
            theme_name=request.params.get('theme_name') or None,
            default_language=request.params.get('default_language', u'it'),
            database_password=request.params.get('database_password'),
            enabled=True if request.params.get('enabled') else False,
        )
        # try to get the instance, as it MUST not exists
        Instance.get_by_domain(request.db_session, params['domain'])

    except KeyError as e:
        log.exception("Error validating params")
        raise ParamsError(e)

    except NoResultFound:
        # no instance found, submit the task
        return request.submit_task('instance.deploy', **params)

    else:
        # found instance, give conflict
        error = 'instance for domain {} already exists'.format(params['domain'])
        return HTTPConflict(headers={'X-Request-Error': error})


@view_config(route_name='instance', request_method=('HEAD', 'GET'))
def info(context, request):
    domain = request.matchdict['domain']
    return Instance.get_by_domain(request.db_session, domain).to_dict()


@view_config(route_name='instance', request_method='PUT',
             request_param='action=restore', renderer='taskresponse')
def restore(context, request):
    raise NotImplementedError


@view_config(route_name='instance', request_method='PUT',
             request_param='action', renderer='taskresponse')
@view_config(route_name='instance', request_method='DELETE',
             renderer='taskresponse')
def update(context, request):
    domain = request.matchdict['domain']
    # prefer 404 upon 400, so try first to get the instance
    instance = Instance.get_by_domain(request.db_session, domain)
    action = request.params['action']
    if action in ('enable', 'disable', 'reload', 'kill', 'sentence',
                  'flush_cache'):
        taskname = "instance.{}".format(action)

    elif request.method == 'DELETE':
        taskname = 'instance.remove'

    else:
        raise ParamsError('invalid action {}'.format(action))

    return request.submit_task(taskname, id=instance.id)
