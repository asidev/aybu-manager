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

from pyramid.view import view_config


@view_config(route_name='instances', request_method='GET')
def list(context, request):
    raise NotImplementedError


@view_config(route_name='instances', request_method='POST')
def deploy(context, request):
    raise NotImplementedError


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
