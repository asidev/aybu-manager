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

from sqlalchemy import engine_from_config
from pyramid.config import Configurator
from aybu.core.request import BaseRequest
from aybu.manager.models import Base
from . authentication import AuthenticationPolicy


def main(global_config, **settings):

    engine = engine_from_config(settings, 'sqlalchemy.')
    Base.metadata.create_all(engine)
    BaseRequest.set_db_engine(engine)
    authentication_policy = AuthenticationPolicy()
    config = Configurator(settings=settings, request_factory=BaseRequest,
                          authentication_policy=authentication_policy)

    config.include(includeme)

    return config.make_wsgi_app()


def includeme(config):
    config.include(add_routes)


def add_routes(config):
    config.add_route('instances', '/instances')
    config.add_route('instance', '/instances/{domain}')
    config.add_route('themes', '/themes')
    config.add_route('theme', '/themes/{name}')
    config.add_route('redirects', '/redirects')
    config.add_route('redirect', '/redirects/{source}')
    config.add_route('environments', '/environments')
    config.add_route('environment', '/environments/{name}')
    config.add_route('users', '/users')
    config.add_route('user', '/users/{email}')
    config.scan()
