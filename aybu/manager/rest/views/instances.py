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


log = logging.getLogger(__name__)


@view_config(route_name='instances', request_method='GET')
def list(context, request):
    return dict(instances=[i.to_dict() for i in
                           Instance.all(request.db_session)])


@view_config(route_name='instances', request_method='POST',
             renderer='taskresponse')
def deploy(context, request):
    log.info("received request for %s", request.current_route_url())
    uuid = request.headers.get('X-Task-UUID')
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
        if uuid:
            params['uuid'] = uuid
        log.debug("params: %s", params)

    except KeyError as e:
        log.exception("Error validating params")
        raise ParamsError(e)

    return request.submit_task('instance.deploy', **params)


@view_config(route_name='instance', request_method=('HEAD', 'GET'))
def info(context, request):
    raise NotImplementedError


@view_config(route_name='instance', request_method='PUT',
             request_param='action=enable')
def enable(context, request):
    raise NotImplementedError


@view_config(route_name='instance', request_method='PUT',
             request_param='action=disable')
def disable(context, request):
    raise NotImplementedError


@view_config(route_name='instance', request_method='PUT',
            request_param='action=reload')
def reload(context, request):
    raise NotImplementedError


@view_config(route_name='instance', request_method='PUT',
             request_param='action=kill')
def kill(context, request):
    raise NotImplementedError


@view_config(route_name='instance', request_method='PUT',
             request_param='action=sentence')
def sentence(context, request):
    raise NotImplementedError


@view_config(route_name='instance', request_method='PUT',
             request_param='action=flush')
def flush(context, request):
    raise NotImplementedError


@view_config(route_name='instance', request_method='PUT',
             request_param='action=restore')
def restore(context, request):
    raise NotImplementedError


@view_config(route_name='instance', request_method='DELETE')
def remove(context, request):
    raise NotImplementedError
