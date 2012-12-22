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

import logging
import ast
from aybu.manager.exc import ParamsError
from sqlalchemy import not_


def search(request, entity, searchables, query_options=(), return_query=False):
    log = logging.getLogger("{}.search".format(__name__))
    filters = []
    params = dict(request.params)
    log.debug("params: %s", params)

    for key, convert_fun in searchables.iteritems():
        value = params.pop(key, None)
        if not value:
            continue

        try:
            negate = False
            if value.startswith("!"):
                negate = True
                value = value[1:]

            value = convert_fun(value)
            log.debug("Adding %s.%s == %s to filters (negate: %s)",
                      entity, key, value, negate)
            filter_ = getattr(entity, key) == value

            if negate:
                filter_ = not_(filter_)

            filters.append(filter_)

        except ValueError:
            raise ParamsError('Invalid value {} for {}'.format(value, key))

    sort_by = params.pop('sort_by', None)
    if sort_by and not hasattr(entity, sort_by):
        raise ParamsError('Invalid sort field {}'.format(sort_by))

    sort_order = params.pop('sort_order', None)
    if sort_order and not sort_order in ('asc', 'desc'):
        raise ParamsError('Invalid sort order {}'.format(sort_order))

    start = params.pop('start', None)
    if start:
        try:
            start = ast.literal_eval(start)

        except ValueError:
            raise ParamsError('Invalid value for start: {}'.format(start))

    limit = params.pop('limit', None)
    if limit:
        try:
            limit = ast.literal_eval(limit)

        except ValueError:
            raise ParamsError('Invalid value for limit: {}'.format(limit))

    if len(params):
        raise ParamsError('Unnkown parameters: {}'\
                                .format(" ".join(params.keys())))

    log.debug("search: sort: %s sort_order: %s", sort_by, sort_order)
    return entity.search(request.db_session, filters=filters,
                         sort_order=sort_order, sort_by=sort_by,
                         limit=limit, start=start,
                         query_options=query_options,
                         return_query=return_query)
