#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright 2010-2012 Asidev s.r.l.

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
import zmq
from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from zmq.devices.basedevice import ThreadDevice

from aybu.manager.models import Base, Environment
from . authentication import AuthenticationPolicy
from . request import Request


def main(global_config, **settings):

    engine = engine_from_config(settings, 'sqlalchemy.')
    Base.metadata.create_all(engine)
    Request.set_db_engine(engine)
    authentication_policy = AuthenticationPolicy(
                            realm=settings['authentication.realm'])
    config = Configurator(settings=settings, request_factory=Request,
                          default_permission='admin',
                          authentication_policy=authentication_policy)

    config.include(includeme)
    log = logging.getLogger(__name__)
    log.info("Starting zmq QUEUE (%s ==> |QUEUE| ==> %s)",
             settings['zmq.queue_addr'], settings['zmq.daemon_addr'])

    device = ThreadDevice(zmq.QUEUE, zmq.REP, zmq.REQ)
    device.bind_in(settings['zmq.queue_addr'])
    device.connect_out(settings['zmq.daemon_addr'])
    device.setsockopt_in(zmq.IDENTITY, 'REP')
    device.setsockopt_out(zmq.IDENTITY, 'REQ')
    device.start()

    return config.make_wsgi_app()


def includeme(config):
    Environment.initialize(config.registry.settings, None)
    config.include(add_routes)
    config.add_renderer('taskresponse',
                        'aybu.manager.rest.renderers.TaskResponseRender')
    config.add_renderer(None, 'pyramid.renderers.json_renderer_factory')
    config.scan()


def add_routes(config):
    aclfct = 'aybu.manager.rest.authentication.AuthenticatedFactory'
    config.add_route('aliases', '/aliases', factory=aclfct)
    config.add_route('alias', '/aliases/{domain}', factory=aclfct)
    config.add_route('archives', '/archives', factory=aclfct)
    config.add_route('archive', '/archives/{name}', factory=aclfct)
    config.add_route('environments', '/environments', factory=aclfct)
    config.add_route('environment', '/environments/{name}', factory=aclfct)
    config.add_route('groups', '/groups', factory=aclfct)
    config.add_route('group', '/groups/{name}', factory=aclfct)
    config.add_route('instances', '/instances', factory=aclfct)
    config.add_route('instance', '/instances/{domain}', factory=aclfct)
    config.add_route('instance_groups', '/instances/{domain}/groups',
                      factory=aclfct)
    config.add_route('instance_group', '/instances/{domain}/groups/{group}',
                     factory=aclfct)
    config.add_route('instance_users', '/instances/{domain}/users',
                     factory=aclfct)
    config.add_route('redirects', '/redirects', factory=aclfct)
    config.add_route('redirect', '/redirects/{source}', factory=aclfct)
    config.add_route('tasks', '/tasks', factory=aclfct)
    config.add_route('task', '/tasks/{uuid}', factory=aclfct)
    config.add_route('tasklogs', '/tasks/{uuid}/logs', factory=aclfct)
    config.add_route('themes', '/themes', factory=aclfct)
    config.add_route('theme', '/themes/{name}', factory=aclfct)
    config.add_route('users', '/users', factory=aclfct)
    config.add_route('user', '/users/{email}', factory=aclfct)
    config.add_route('user_instances', '/users/{email}/instances',
                     factory=aclfct)
