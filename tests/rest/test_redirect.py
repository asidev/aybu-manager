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
from pyramid import testing
from pyramid.httpexceptions import HTTPCreated, HTTPConflict
from sqlalchemy.exc import IntegrityError
import mock
import unittest


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

    @mock.patch('aybu.manager.models.Instance')
    @mock.patch('aybu.manager.models.Redirect')
    def test_create(self, imock, rmock):
        from aybu.manager.rest.views.redirects import create
        ctx, req = self.get_request()

        for param in ('source', 'destination'):
            req.params.clear()
            req.params[param] = 'redir.example.com'
            with self.assertRaises(ParamsError):
                create(ctx, req)

        req.params['source'] = 'source.example.com'
        req.params['destination'] = 'www.example.com'
        self.assertRaises(HTTPCreated, create, ctx, req)
        self.assertTrue(req.db_session.commit.called)

        imock.side_effect = IntegrityError(1,2,3,4)
        with self.assertRaises(HTTPConflict):
            create(ctx, req)

    @mock.patch('aybu.manager.models.Instance')
    @mock.patch('aybu.manager.models.Redirect')
    def test_update(self, imock, rmock):
        from aybu.manager.rest.views.redirects import update
        ctx, req = self.get_request()
        req.matchdict['source'] = 'redir.example.com'

        # FIXME: this does not seem to work :(
        #get_mock = mock.Mock()
        #get_mock.side_effect = NoResultFound
        #rmock.get = get_mock
        #self.assertRaises(NoResultFound, update, ctx, req)

        self.assertRaises(ParamsError, update, ctx, req)

        req.params['http_code'] = 301
        req.params['target_path'] = '/'
        req.params['destination'] = 'www.example.com'
        update(ctx, req)
        self.assertTrue(req.db_session.commit.called)
        self.assertTrue(req.db_session.flush.called)

        req.params.clear()

