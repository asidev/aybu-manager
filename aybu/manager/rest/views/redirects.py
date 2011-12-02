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
from aybu.manager.models import (Instance,
                                 Redirect)
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from pyramid.httpexceptions import HTTPConflict, HTTPCreated


def validate_http_code(http_code):
    try:
        http_code = int(http_code)
        assert http_code in (301, 302, 303, 307)

    except (ValueError, AssertionError) as e:
        raise ParamsError("Invalid http_code {}".format(http_code))

    else:
        return http_code


def validate_target_path(target_path):
    try:
        assert not target_path or target_path.startswith('/')

    except AssertionError:
        raise ParamsError("Target must be an absolute path")

    else:
        return target_path


def validate_hostname(source):
    if len(hostname) > 255:
        return False
    if hostname[-1:] == ".":
        hostname = hostname[:-1]

    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    if not all(allowed.match(x) for x in hostname.split(".")):
        raise ParamsError("{} is not a valid hostname".format(source))

    return source


@view_config(route_name='redirects', request_method='GET')
def list(context, request):
    return {r.source: r.to_dict() for r in Redirect.all(request.db_session)}


@view_config(route_name='redirects', request_method='POST')
def create(context, request):
    try:
        source = request.params['source']
        instance = Instance.get_by_domain(request.db_session,
                                          request.params['destination'])
        http_code = request.params.get('http_code', 301)
        target_path = request.params.get('target_path', '')

    except KeyError as e:
        raise ParamsError(e)

    except NoResultFound:
        raise ParamsError('No instance for domain {}'\
                          .format(request.params['destination']))

    http_code = validate_http_code(http_code)
    target_path = validate_target_path(target_path)
    source = validate_source(source)

    try:
        r = Redirect(source=source, instance=instance, http_code=http_code,
                 target_path=target_path)
        request.db_session.add(r)
        request.db_session.flush()

    except IntegrityError:
        error = 'redirect for source {} already exists'.format(source)
        raise HTTPConflict(headers={'X-Request-Error': error})

    else:
        request.db_session.commit()
        return HTTPCreated()


@view_config(route_name='redirect', request_method=('HEAD', 'GET'))
def info(context, request):
    return Redirect.get(request.db_session,
                        request.matchdict['source']).to_dict()


@view_config(route_name='redirect', request_method='DELETE')
def delete(context, request):
    redirect = Redirect.get(request.db_session,
                            request.matchdict['source'])
    redirect.delete()
    request.db_session.commit()


@view_config(route_name='redirect', request_method='PUT')
def update(context, request):

    params = dict()
    redirect = Redirect.get(request.db_session, request.matchdict['source'])
    specs = (
       ('source', validate_hostname, []),
       ('destination', Instance.get_by_domain, [request.db_session]),
       ('http_code', validate_http_code, []),
       ('target_path', validate_target_path, [])
    )
    try:
        for attr, validate_fun, fun_args in specs:
            if attr in request.params:
                fun_args.append(request.params[attr])
                params[request.params[attr]] = validate_fun(*fun_args)

    except NoResultFound:
        raise ParamsError("No instance for domain {}"\
                          .format(request.params['destination']))

    if not params:
        raise ParamsError("Missing update fields")

    for param in params:
       setattr(redirect, param, params[param])

    try:
        request.db_session.flush()

    except IntegrityError as e:
        raise HTTPConflict(headers={'X-Request-Error': str(e)})

    else:
        request.db_session.commit()

    return redirect.to_dict()




