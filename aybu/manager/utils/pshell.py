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
import aybu.manager.models
from aybu.manager.activity_log import ActivityLog


def setup(env):
    settings = env['request'].registry.settings
    env['models'] = aybu.manager.models
    env['engine'] = engine_from_config(settings, 'sqlalchemy.')
    env['request'].set_db_engine = env['engine']
    aybu.manager.models.Base.metadata.bind = env['engine']
    aybu.manager.models.Environment.initialize(settings)
    env['session'] = env['request'].db_session
    ActivityLog.attach_to(env['session'])

