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

from aybu.manager.models import (Instance,
                                 Alias)
import logging
log = logging.getLogger(__name__)


def create(session, task, domain, instance_id):
    instance = Instance.get(session, instance_id)
    alias = Alias(domain=domain, instance=instance)
    session.add(alias)
    session.flush()
    return alias.domain


def delete(session, task, domain):
    alias = Alias.get(session, domain)
    alias.delete()


def update(session, task, domain, new_domain=None, instance_id=None):
    try:
        alias = Alias.get(session, domain)
        if instance_id:
            alias.instance = Instance.get(session, instance_id)
        if new_domain:
            alias.domain = new_domain
        session.flush()

    except:
        log.exception('alias.update')
