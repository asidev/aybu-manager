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
import zmq
from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from zmq.devices.basedevice import ThreadDevice

from aybu.manager.models import Base
from . authentication import AuthenticationPolicy
from . request import Request


def main(global_config, **settings):

    engine = engine_from_config(settings, 'sqlalchemy.')
    Base.metadata.create_all(engine)
    Request.set_db_engine(engine)
    authentication_policy = AuthenticationPolicy(
                            realm=settings['authentication.realm'])
    config = Configurator(settings=settings, request_factory=Request,
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
    config.include(add_routes)
    config.add_renderer('taskresponse',
                        'aybu.manager.rest.renderers.TaskResponseRender')
    config.add_renderer(None, 'pyramid.renderers.json_renderer_factory')
    config.scan()


def add_routes(config):
    config.add_route('instances', '/instances')
    config.add_route('instance', '/instances/{domain}')
    config.add_route('archives', '/archives')
    config.add_route('archive', '/archives/{name}')
    config.add_route('themes', '/themes')
    config.add_route('theme', '/themes/{name}')
    config.add_route('redirects', '/redirects')
    config.add_route('redirect', '/redirects/{source}')
    config.add_route('environments', '/environments')
    config.add_route('environment', '/environments/{name}')
    config.add_route('users', '/users')
    config.add_route('user', '/users/{email}')
