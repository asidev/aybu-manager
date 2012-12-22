#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright 2010-2012 Asidev s.r.l.

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

import datetime
import glob
import os
import shutil
from aybu.manager.models import (Environment,
                                 Instance)
from aybu.manager.exc import ParamsError
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import (HTTPNotFound,
                                    HTTPNoContent)


@view_config(route_name='archives', request_method=('HEAD', 'GET'))
def list(context, request):
    archives = Environment.settings['paths.archives']
    return {path.replace(archives, '')[1:]: path for path in
            glob.glob("{}/*.tar.gz".format(archives))}


@view_config(route_name='archives', request_method='POST',
             renderer='taskresponse')
def create(context, request):
    try:
        domain = request.params['domain']
        now = datetime.datetime.now().strftime('%Y%m%d-%H.%M.%S')
        default_name = "{}-{}".format(domain, now)
        name = request.params.get('name', default_name)
        name.replace(":", ".")

    except KeyError as e:
        raise ParamsError(e)

    instance = Instance.get_by_domain(request.db_session, domain)
    return request.submit_task('instance.archive', id=instance.id,
                                name=name)


@view_config(route_name='archive', request_method=('HEAD', 'GET'),
             renderer=None)
def download(context, request):
    try:
        name = request.matchdict['name'].replace(".tar.gz", "")
        if not name.endswith("tar.gz"):
            name = "{}.tar.gz".format(name)

        archives = Environment.settings['paths.archives']
        archive_path = os.path.join(archives, name)
        archive = open(archive_path)
        return Response(content_type="application/octet-stream",
                        app_iter=archive)
    except IOError:
        raise HTTPNotFound()


@view_config(route_name='archive', request_method='DELETE')
def remove(context, request):
    try:
        name = request.matchdict['name'].replace(".tar.gz", "")
        if not name.endswith("tar.gz"):
            name = "{}.tar.gz".format(name)
        archives = Environment.settings['paths.archives']
        os.unlink(os.path.join(archives, name))
        raise HTTPNoContent()

    except OSError as e:
        if e.errno == 2:
            raise HTTPNotFound()

        else:
            # die with a 500
            raise e


@view_config(route_name='archive', request_method='PUT')
def update(context, request):
    try:
        name = request.matchdict['name']
        archives = Environment.settings['paths.archives']
        new_name = request.params['name']
        shutil.mv(os.path.join(archives, name),
                  os.path.join(archives, new_name))

    except IOError as e:
        raise HTTPNotFound()

    except KeyError as e:
        raise ParamsError(e)

    else:
        raise HTTPNoContent()
