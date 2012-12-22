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
                      'www.42.com', '4r.aybu.it'):
            self.assertEqual(hname, validators.validate_hostname(hname))

    def test_validate_name(self):
        for name in ('èlker', 'test-name'):
            self.assertRaises(ValidationError, validators.validate_name, name)

        for name in ('test', 'test_name', 'test_9_name', '9name'):
            self.assertEqual(name, validators.validate_name(name))

    def test_validate_password(self):
        for psw in ('password', 'l666238%% `£àà%%%$©»»', '  9 l3 00 '):
            self.assertEqual(psw, validators.validate_password(psw))

    def test_validate_version(self):
        for version in ('1', '2.7.2.2', '1.5.a4', '1.5p4', '1.3c4'):
            self.assertRaises(ValidationError, validators.validate_version,
                              version)
        for version in ('0.4', '0.4.1', '0.5a2', '0.5b3', '0.9.12', '1.0.4b3',
                        '1.0.2a1'):
            self.assertEqual(version, validators.validate_version(version))

    def test_validate_positive_int(self):
        for i in ('-1', 'a', 0):
            self.assertRaises(ValidationError,
                              validators.validate_positive_int,
                              i)

        for i in ('1', 1, 10):
            self.assertEqual(int(i), validators.validate_positive_int(i))

    def test_validate_web_address(self):
        for addr in (3, 'www.a&b.com/test', 'www.a//b.com/it/index'
                     'www.example.com./it/index'):
            self.assertRaises(ValidationError, validators.validate_web_address,
                              addr)

        for addr in ('http://www.example.com', 'http://www.example.com/',
                     'http://www.example.com/it'):
            self.assertEqual(addr, validators.validate_web_address(addr))

        for addr in ('www.example.com', 'www.example.com/',
                     'www.example.com/it'):
            self.assertEqual("http://" + addr,
                             validators.validate_web_address(addr))

        self.assertEqual('', validators.validate_web_address(''))

    def test_validate_twitter(self):
        for tw in ('#hastag', 'name', '99name'):
            self.assertRaises(ValidationError, validators.validate_twitter, tw)

        for tw in ('', None, False):
            self.assertEqual('', validators.validate_twitter(tw))

        for tw in ('@gbagnoli', '@asidev'):
            self.assertEqual(tw, validators.validate_twitter(tw))

    def test_validate_email(self):
        for email in ('mail@example.com.', 'mail@example/.com',
                      '@example.com'):
            self.assertRaises(ValidationError, validators.validate_email,
                              email)

        for email in ('mail@example.com', 'mail&mail@example.com',
                      'mail+mail@example.com'):
            self.assertEqual(email, validators.validate_email(email))


    def test_validate_language(self):
        for lang in ('it_IT', 'ita', '__', 'i-'):
            self.assertRaises(ValidationError, validators.validate_language,
                              lang)

        for lang in ('it', 'nn', 'ex', 'EN', 'IT'):
            self.assertEqual(lang.lower(), validators.validate_language(lang))
