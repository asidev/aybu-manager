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

import os
import shutil
import stat
import tempfile
import unittest
import aybu.manager.utils.filesystem


class FSTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)


    def test_create(self):
        fs = aybu.manager.utils.filesystem.FileSystemSession()

        # test rollback
        file_= os.path.join(self.tempdir, 'test.txt')
        fs.create(file_)
        self.assertTrue(os.path.exists(file_))
        fs.rollback()
        self.assertFalse(os.path.exists(file_))

        # test successfull create
        fs.create(file_)
        fs.commit()
        self.assertTrue(os.path.exists(file_))

        # test unsuccessfull create
        with self.assertRaises(OSError):
            fs.create(file_)
        self.assertTrue(os.path.exists(file_))

    def test_transaction_status(self):
        fs = aybu.manager.utils.filesystem.FileSystemSession(autobegin=False)
        with self.assertRaises(aybu.manager.utils.filesystem.TransactionError):
            fs.commit()
        with self.assertRaises(aybu.manager.utils.filesystem.TransactionError):
            fs.rollback()

        fs.begin()
        fs.commit()

        with self.assertRaises(aybu.manager.utils.filesystem.TransactionError):
            fs.commit()

    def test_transaction(self):
        fs = aybu.manager.utils.filesystem.FileSystemSession()
        dir_ = os.path.join(self.tempdir, 'test')
        join = os.path.join

        def dostuff():
            fs.mkdir(dir_)
            fs.create(join(dir_, 'testfile.txt'), content="Test")
            fs.copy(join(dir_, 'testfile.txt'), join(dir_, 'test2.txt'))

        dostuff()
        fs.rollback()
        self.assertFalse(os.path.exists(join(dir_, 'test2.txt')))
        self.assertFalse(os.path.exists(join(dir_, 'testfile.txt')))
        self.assertFalse(os.path.exists(dir_))

        dostuff()
        fs.commit()
        self.assertTrue(os.path.exists(dir_))
        self.assertTrue(os.path.exists(join(dir_, 'testfile.txt')))
        self.assertTrue(os.path.exists(join(dir_, 'test2.txt')))

    def test_failed_rollback(self):
        fs = aybu.manager.utils.filesystem.FileSystemSession()
        dir_ = os.path.join(self.tempdir, 'test')
        inner_dir = os.path.join(dir_, 'inner')
        fs.mkdir(dir_)
        fs.mkdir(inner_dir)

        os.chmod(dir_, stat.S_IRUSR|stat.S_IXUSR)
        with self.assertRaises(OSError):
            fs.rollback()

        self.assertTrue(os.path.exists(dir_))
        self.assertTrue(os.path.exists(inner_dir))

        fs.rollback() # transaction lost, no errors
        os.chmod(dir_, stat.S_IRWXU | stat.S_IRWXG)

    def test_error_on_exists(self):
        fs = aybu.manager.utils.filesystem.FileSystemSession()
        dir_ = os.path.join(self.tempdir, 'test')
        fs.mkdir(dir_)
        fs.commit()

        fs.mkdir(dir_, error_on_exists=False)
        fs.rollback()
        self.assertTrue(os.path.exists(dir_))

