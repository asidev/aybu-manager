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
import aybu.manager.rest.views.redirects as views
from pyramid import testing
from pyramid.httpexceptions import HTTPCreated, HTTPConflict
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
import mock
import unittest

@mock.patch('aybu.manager.models.Instance')
@mock.patch('aybu.manager.models.Redirect')
class TestRedirectsViews(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        super(TestRedirectsViews, self).setUp()

    def tearDown(self):
        testing.tearDown()
        super(TestRedirectsViews, self).tearDown()

    def get_request(self, *args, **kwargs):
        req = testing.DummyRequest(*args, **kwargs)
        req.db_session = mock.Mock()
        return testing.DummyResource(), req

    def __test_create_missing_instance_param(self, imock, rmock):
        with self.assertRaises(ParamsError):
            views.create(*self.get_request(
                params=dict(source='redir.example.com')))

    def __test_create_missing_source_param(self, imock, rmock):
        ctx, req = self.get_request(params=dict(destination='www.example.com'))

        with self.assertRaises(ParamsError):
            views.create(ctx, req)

    def __test_create_ok(self, imock, rmock):
        params = dict(destination='www.example.com',source='redir.example.com')
        ctx, req = self.get_request(params=params)

        self.assertTrue(isinstance(views.create(ctx, req), HTTPCreated))


    def test_no_instance_found(self, imock, rmock):
        imock.get_by_domain.side_effect = NoResultFound()
        params = dict(destination='www.example.com', source='redir.example.com')
        ctx, req = self.get_request(params=params)

        with self.assertRaises(ParamsError):
            views.create(ctx, req)

    def __test_integrity_error(self, imock, rmock):
        params = dict(destination='www.example.com', source='redir.example.com')
        ctx, req = self.get_request(params=params)
        req.db_session.flush.side_effect = IntegrityError(1,2,3,4)

        with self.assertRaises(HTTPConflict):
            views.create(ctx, req)

    def test_params_validation(self, imock, rmock):

        params = dict(destination='www.example.com', source='invalid')
        ctx, req = self.get_request(params=params)
        self.assertRaises(ParamsError, views.create, ctx, req)

        req.params['source'] = 'www.pippo.it.'
        self.assertRaises(ParamsError, views.create, ctx, req)

        req.params['source'] = 'a' * 255 + ".com"
#        self.assertRaises(ParamsError, views.create, ctx, req)




