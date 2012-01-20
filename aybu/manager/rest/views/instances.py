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
from aybu.manager.models import (Instance,
                                 User,
                                 Theme,
                                 Environment)
from aybu.manager.exc import ParamsError
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPConflict
from sqlalchemy.orm.exc import NoResultFound


log = logging.getLogger(__name__)


@view_config(route_name='instances', request_method=('HEAD', 'GET'))
def list(context, request):
    return {i.domain: i.to_dict() for i in Instance.all(request.db_session)}


@view_config(route_name='instances', request_method='POST',
             renderer='taskresponse')
def deploy(context, request):
    try:
        params = dict(
            domain=request.params['domain'],
            owner_email=request.params['owner_email'],
            environment_name=request.params['environment_name'],
            technical_contact_email=\
                request.params.get('technical_contact_email',
                                   request.params['owner_email']),
            theme_name=request.params.get('theme_name'),
            default_language=request.params.get('default_language', u'it'),
            database_password=request.params.get('database_password'),
            enabled=True if request.params.get('enabled') else False,
            verbose=True if request.params.get('verbose') else False,
        )
        # try to get the instance, as it MUST not exists
        Instance.get_by_domain(request.db_session, params['domain'])

    except KeyError as e:
        log.exception("Error validating params")
        raise ParamsError(e)

    except NoResultFound:
        # no instance found, validate relations.
        try:
            field = 'owner_email'
            cls = 'user'
            User.log.debug("Validating owner %s", params[field])
            owner = User.get(request.db_session, params[field])
            if not owner:
                raise NoResultFound()
            if params['technical_contact_email'] != params['owner_email']:
                field = 'technical_contact_email'
                User.log.debug("Validating contact %s", params[field])
                ctc = User.get(request.db_session, params[field])
                if not ctc:
                    raise NoResultFound()

            field = 'environment_name'
            cls = 'environment'
            Environment.log.debug("validating environment %s", params[field])
            env = Environment.get(request.db_session, params[field])
            if not env:
                raise NoResultFound()

            field = 'theme_name'
            cls = 'theme'
            if params[field]:
                Theme.log.debug("Validating theme %s", params[field])
                theme = Theme.get(request.db_session, params[field])
                if not theme:
                    raise NoResultFound()

        except NoResultFound:
            raise ParamsError('{} "{}" for {} not found'\
                              .format(cls.title(), params[field], field))

        else:
            log.info("Submitting task")
            # relations exists, submit tasks
            return request.submit_task('instance.deploy', **params)

    else:
        # found instance, conflict
        error = 'instance for domain {} already exists'\
                .format(params['domain'])
        raise HTTPConflict(headers={'X-Request-Error': error})


@view_config(route_name='instance', request_method=('HEAD', 'GET'))
def info(context, request):
    domain = request.matchdict['domain']
    instance = Instance.get_by_domain(request.db_session, domain)
    return instance.to_dict(paths=True)


@view_config(route_name='instance', request_method='PUT',
             request_param='action=restore', renderer='taskresponse')
def restore(context, request):
    domain = request.matchdict['domain']
    instance = Instance.get_by_domain(request.db_session, domain)
    archive = request.params.get(archive)
    archive_name = request.params.get(archive_name)

    if archive and archive_name:
        raise ParamsError('archive and archive_name are mutually exclusive')

    elif archive_name and not archive:
        raise ParamsError('missing both archive and archive name')

    elif archive:
        # TODO handle archive upload
        raise NotImplementedError()

    if not archive_name.endswith("tar.gz"):
        archive_name = "{}.tar.gz".format(archive_name)

    archives = Environment.settings['paths.archives']
    archive_path = os.path.join(archives, archive_name)
    if not os.path.exists(archive_path):
        raise ParamsError('{} is not a valid archive'.format(archive_name))

    return request.submit_task('instance.restore', id=instance.id,
                               archive_name=archive_name)


@view_config(route_name='instance', request_method='PUT',
             request_param='action', renderer='taskresponse')
@view_config(route_name='instance', request_method='DELETE',
             renderer='taskresponse')
def update(context, request):
    domain = request.matchdict['domain']
    # prefer 404 upon 400, so try first to get the instance
    instance = Instance.get_by_domain(request.db_session, domain)
    if request.method == 'DELETE':
        taskname = 'instance.delete'

    elif 'action' not in request.params:
        raise ParamsError('No action provided')

    elif request.params['action'] in ('enable', 'disable', 'reload', 'kill',
                                      'sentence', 'flush_cache', 'archive',
                                      'migrate', 'switch_environment'):
        taskname = "instance.{}".format(request.params['action'])

    else:
        raise ParamsError('invalid action {}'.format(request.params['action']))

    params = dict(request.params)
    params.pop('action', '')
    return request.submit_task(taskname, id=instance.id, **params)
