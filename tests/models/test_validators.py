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

import unittest
import aybu.manager.models.validators as validators
from aybu.manager.exc import ValidationError


class TestValidators(unittest.TestCase):

    def test_validate_http_code(self):
        for code in ('a', '', '404', '200', 'a23', -1, 405, 304, 305, 306):
            self.assertRaises(ValidationError,
                              validators.validate_redirect_http_code,
                              code)

        for code in ('301', 301, '302', 302, '303', 303, '307', 307):
            self.assertEqual(int(code),
                             validators.validate_redirect_http_code(code))

    def test_validate_target_path(self):
        for path in ('abc', 'abc/cd'):
            self.assertRaises(ValidationError,
                              validators.validate_redirect_target_path,
                              path)

        for path in ('', '/a', '/asjfr/kejrkejr'):
            self.assertEqual(path,
                             validators.validate_redirect_target_path(path))

        self.assertEqual('', validators.validate_redirect_target_path(None))

    def test_validate_hostname(self):
        long_string = 'a' * 512
        for hname in ('www.example.com.', 'invalid', 'www.a&b.com',
                      'www.a/b.com', long_string):
            self.assertRaises(ValidationError,
                              validators.validate_hostname, hname)

        for hname in ('www.example.com', 'example.com', 'sub.sub.example.com',
                      'www.42.com'):
            self.assertEqual(hname, validators.validate_hostname(hname))



