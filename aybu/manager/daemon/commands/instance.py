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

from aybu.manager.models import (Environment,
                                 Instance,
                                 Theme,
                                 User)


def deploy(session, domain, owner_email, environment_name, tech_contact_email,
           theme_name=None, default_language=u'it', database_password=None,
           enabled=True):

    env = Environment.get(session, environment_name)
    theme = None if not theme_name else Theme.get(session, theme_name)
    owner = User.get(session, owner_email)
    technical_contact = User.get(session, tech_contact_email)

    instance = Instance.deploy(domain, owner, env, technical_contact, theme,
                               default_language, database_password, enabled)

    return instance.id


def reload(session, domain):

    instance = Instance.get(session, domain)
    instance.reload()


def delete(session, domain):
    instance = Instance.get(session, domain)
    instance.delete()


def enable(session, domain):
    instance = Instance.get(session, domain)
    instance.enabled = True


def disable(session, domain):
    instance = Instance.get(session, domain)
    instance.disabled = False


def flush(session, domain):
    instance = Instance.get(session, domain)
    instance.flush_cache()
