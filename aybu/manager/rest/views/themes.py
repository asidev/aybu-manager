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
from aybu.manager.models import (Theme,
                                 User)
from pyramid.view import view_config
from pyramid.httpexceptions import (HTTPCreated,
                                    HTTPNoContent,
                                    HTTPConflict,
                                    HTTPPreconditionFailed)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound


@view_config(route_name='themes', request_method='GET')
def list(context, request):
    return {t.name: t.to_dict() for t in Theme.all(request.db_session)}


@view_config(route_name='themes', request_param='schema',
             request_method='POST')
def upload(context, request):
    # TODO
    # 1. read yaml from schema in request.params
    # 2. validate yaml
    # 3. create owner and author if needed
    # 4. create Theme
    # 5. handle upload of templates/images/css/js/etc
    raise NotImplementedError


@view_config(route_name='themes', request_method='POST')
def create_no_upload(context, request):
    try:
        name = request.params['name']
        parent_name = request.params.get('parent', None)
        version = request.params.get('version', '')
        author_email = request.params['author']
        owner_email = request.params['owner']
        banner_width = request.params['banner_width']
        banner_height = request.params['banner_height']
        logo_width = request.params['logo_width']
        logo_height = request.params['logo_height']
        main_menu_levels = request.params['main_menu_levels']
        template_levels = request.params['template_levels']
        image_full_size = request.params['image_full_size']

        owner = User.get(request.db_session, owner_email)
        author = User.get(request.db_session, author_email)
        if parent_name:
            parent = Theme.get(request.db_session, parent_name)
        else:
            parent = None

        # check if a theme exists in package aybu.themes
        __import__('aybu.themes.{}'.format(name))

        t = Theme(name=name, parent=parent, author=author,
                  version=version, owner=owner, banner_width=banner_width,
                  banner_height=banner_height, logo_width=logo_width,
                  logo_height=logo_height, main_menu_levels=main_menu_levels,
                  template_levels=template_levels,
                  image_full_size=image_full_size)
        request.db_session.add(t)
        request.db_session.flush()

    except (KeyError, NoResultFound) as e:
        raise ParamsError(e)

    except ImportError as e:
        error = 'Theme {} does not exists in aybu.themes package'.format(name)
        raise HTTPPreconditionFailed(headers={'X-Request-Error': error})

    except IntegrityError as e:
        error = 'Theme with name {} already exists'.format(name)
        request.db_session.rollback()
        raise HTTPConflict(headers={'X-Request-Error': error})

    else:
        request.db_session.commit()
        return HTTPCreated()


@view_config(route_name='theme', request_method=('HEAD', 'GET'))
def info(context, request):
    return Theme.get(request.db_session,
                     request.matchdict['theme']).to_dict()


@view_config(route_name='theme', request_method='DELETE')
def delete(context, request):

    try:
        name = request.matchdict['theme']
        theme = Theme.get(request.db_session, name)
        theme.delete()
        request.db_session.flush()

    except IntegrityError:
        Theme.log.exception('Error deleting theme {}'.format(name))
        request.db_session.rollback()
        raise HTTPPreconditionFailed(
            headers={'X-Request-Error': 'Theme {} is in use'.format(name)})
    else:
        request.db_session.commit()
        return HTTPNoContent()


@view_config(route_name='theme', request_method='PUT')
def update(context, request):

    params = dict()
    theme = Theme.get(request.db_session, request.matchdict(['theme']))

    try:
        for attr in ('owner', 'author'):
            value = request.params.get(attr)
            if value:
                params[attr] = User.get(request.db_session, value)

    except NoResultFound:
        raise ParamsError('No user with email {}'.format(value))

    try:
        attr = 'parent'
        parent = request.params.get(attr)
        if parent:
            parent = Theme.get(request.db_session, parent)
            params[attr] = parent

    except NoResultFound:
        raise ParamsError('No theme named {}'.format(value))


    for attr in ('version', 'banner_height', 'banner_width', 'logo_height',
                 'logo_width', 'main_menu_levels', 'template_levels', 'name',
                 'image_full_size'):
        value = request.params.get(attr)
        if value:
            params[attr] = value

    if not params:
        raise ParamsError('Missing update fields')

    try:
        if 'name' in params and params['name'] != theme.name:
            raise NotImplementedError('Changing theme name is not supported')
            __import__('aybu.themes.{}'.format(params['name']))

        for param in params:
            setattr(theme, param, params[param])

        request.db_session.flush()

    except ImportError as e:
        error = 'Theme {} does not exists in aybu.themes package'\
                .format(params['name'])
        raise HTTPPreconditionFailed(headers={'X-Request-Error': error})

    except IntegrityError as e:
        request.db_session.rollback()
        raise HTTPConflict(headers={'X-Request-Error': str(e)})

    else:
        request.db_session.commit()

    return theme.to_dict()
