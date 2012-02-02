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
                                 Redirect)
import logging
log = logging.getLogger(__name__)


def create(session, task, source, instance_id, http_code=301, target_path=''):
    instance = Instance.get(session, instance_id)
    redirect = Redirect(source=source, instance=instance, http_code=http_code,
                        target_path=target_path)
    session.add(redirect)
    session.flush()
    return redirect.source


def delete(session, task, source):
    redirect = Redirect.get(session, source)
    redirect.delete()


def update(session, task, source, instance_id=None, http_code=None,
           target_path=None):
    try:
        redirect = Redirect.get(session, source)
        if instance_id:
            redirect.instance = Instance.get(session, instance_id)
        if http_code:
            redirect.http_code = http_code
        if target_path:
            redirect.target_path = target_path
    except:
        log.exception('redirect.update')
