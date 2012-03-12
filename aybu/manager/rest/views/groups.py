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


from aybu.manager.exc import ParamsError
from aybu.manager.models import Group
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from pyramid.httpexceptions import (HTTPCreated,
                                    HTTPNoContent,
                                    HTTPConflict,
                                    HTTPPreconditionFailed)
from pyramid.view import view_config


@view_config(route_name='groups', request_method=('HEAD', 'GET'))
def list(context, request):
    return {group.name: group.to_dict() for group in
           Group.all(request.db_session)}


@view_config(route_name='groups', request_method='POST')
def create(context, request):

    try:
        name = request.params['name']
        parent = request.params.get('parent')

        g = Group(name=name)
        request.db_session.add(g)
        request.db_session.flush()
        if parent:
            try:
                g.parent = Group.get(request.db_session, parent)

            except NoResultFound:
                raise ParamsError('Invalid parent: %s', parent)

    except KeyError as e:
        raise ParamsError('Missing parameter: {}'.format(e))

    except IntegrityError as e:
        error = 'Group {} already exists'.format(name)
        raise HTTPConflict(headers={'X-Request-Error': error})

    else:
        request.db_session.commit()
        raise HTTPCreated()


@view_config(route_name='group', request_method=('GET', 'HEAD'))
def info(context, request):
    group = Group.get(request.db_session, request.matchdict['name'])
    return group.to_dict()


@view_config(route_name='group', request_method='DELETE')
def delete(context, request):
    try:
        name = request.matchdict['name']
        group = Group.get(request.db_session, name)
        group.delete()
        request.db_session.flush()

    except IntegrityError as e:
        Group.log.exception('Error deleting group {}'.format(name))
        request.db_session.rollback()
        raise HTTPPreconditionFailed(
            headers={'X-Request-Error': 'Cannot delete group {}: {}'\
                     .format(group, e)})

    else:
        request.db_session.commit()
        raise HTTPNoContent()


@view_config(route_name='group', request_method='PUT')
def update(context, request):
    name = request.matchdict['name']
    group = Group.get(request.db_session, name)
    params = {}

    if 'name' in request.params:
        params['name'] = request.params['name']

    if 'parent' in request.params:
        parent = request.params['parent']

        try:
            if parent:
                params['parent'] = Group.get(request.db_session, parent)

            else:
                params['parent'] = None

        except NoResultFound:
            raise ParamsError('Invalid parent: %s', parent)

    if not params:
        raise ParamsError('Missing update fields')

    try:
        for attr, value in params.iteritems():
            setattr(group, attr, value)

        request.db_session.flush()

    except IntegrityError:
        request.db_session.rollback()
        raise HTTPConflict(headers={'X-Request-Error':
                                    'Group {} already exists'.format(name)})

    else:
        request.db_session.commit()
        return group.to_dict()
