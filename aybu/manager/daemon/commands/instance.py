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
import logging
log = logging.getLogger(__name__)


def deploy(session, task, domain, owner_email, environment_name,
           technical_contact_email, theme_name=None, default_language=u'it',
           database_password=None, enabled=True):

    env = Environment.get(session, environment_name)
    theme = None if not theme_name else Theme.get(session, theme_name)
    owner = User.get(session, owner_email)
    technical_contact = User.get(session, technical_contact_email)

    instance = Instance.deploy(session, domain, owner, env, technical_contact,
                               theme, default_language, database_password,
                               enabled)

    return instance.id


def rewrite(session, task, id):
    if id == "all":
        instances = Instance.all(session)
    else:
        instances = [Instance.get(session, id)]

    envs = {}
    for instance in instances:
        if not instance.enabled:
            continue

        env = instance.environment
        envs[env.name] = env
        instance.rewrite(restart_services=False)

    for env in envs.values():
        env.restart_services()


def reload(session, task, id, force=False, kill=False):
    if id == 'all':
        instances = Instance.all(session)
    else:
        instances = [Instance.get(session, id)]

    for instance in instances:
        if instance.enabled:
            instance.reload(force=force, kill=kill)


def delete(session, task, id, archive=False):
    instance = Instance.get(session, id)
    instance.delete(archive=archive)


def enable(session, task, id):
    instance = Instance.get(session, id)
    instance.enabled = True


def disable(session, task, id):
    instance = Instance.get(session, id)
    instance.enabled = False


def flush_cache(session, task, id):
    instance = Instance.get(session, id)
    instance.flush_cache()


def switch_environment(session, task, id, environment):
    instance = Instance.get(session, id)
    new_env = Environment.get(session, environment)
    reenable = False

    if instance.enabled:
        reenable = True
        instance.enabled = False

    instance.environment = new_env

    if reenable:
        instance.enabled = True


def change_domain(session, task, id, domain):
    instance = Instance.get(session, id)
    reenable = False

    if instance.enabled:
        reenable = True
        instance.enabled = False

    instance.change_domain(domain)

    if reenable:
        instance.enabled = True


def migrate(session, task, id, revision):
    instance = Instance.get(session, id)
    instance.upgrade_schema(revision)


def archive(session, task, id, name):
    instance = Instance.get(session, id)
    instance.archive(name)


def restore(session, task, id, archive_name):
    instance = Instance.get(session, id)
    instance.restore(archive_name)


def sentence(session, task, id):
    raise NotImplementedError


def kill(session, task, id):
    raise NotImplementedError
