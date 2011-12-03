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
from sqlalchemy.orm.exc import NoResultFound
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

    def __test_params_validation(self, imock, rmock):

        params = dict(destination='www.example.com', source='invalid')
        ctx, req = self.get_request(params=params)
        self.assertRaises(ParamsError, views.create, ctx, req)

        req.params['source'] = 'www.pippo.it.'
        self.assertRaises(ParamsError, views.create, ctx, req)

        req.params['source'] = 'a' * 255 + ".com"
#        self.assertRaises(ParamsError, views.create, ctx, req)


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
        self.assertTrue(isinstance(create(ctx, req), HTTPCreated))
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

    def test_validate_http_code(self):
        from aybu.manager.rest.views.redirects import validate_http_code

        for code in ('a', '', '404', '200', 'a23', -1, 405, 304, 305, 306):
            self.assertRaises(ParamsError, validate_http_code, code)

        for code in ('301', 301, '302', 302, '303', 303, '307', 307):
            self.assertEqual(int(code), validate_http_code(code))

    def test_validate_target_path(self):
        from aybu.manager.rest.views.redirects import validate_target_path

        for path in ('abc', 'abc/cd'):
            self.assertRaises(ParamsError, validate_target_path, path)

        for path in ('', '/a', '/asjfr/kejrkejr'):
            self.assertEqual(path, validate_target_path(path))

        self.assertEqual('', validate_target_path(None))

    def test_validate_hostname(self):
        from aybu.manager.rest.views.redirects import validate_hostname

        long_string = 'a' * 512
        for hname in ('www.example.com.', 'invalid', 'www.a&b.com',
                      'www.a/b.com', long_string):
            self.assertRaises(ParamsError, validate_hostname, hname)

        for hname in ('www.example.com', 'example.com', 'sub.sub.example.com',
                      'www.42.com'):
            self.assertEqual(hname, validate_hostname(hname))



