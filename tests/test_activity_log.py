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

from collections import namedtuple
import os
import shutil
import stat
import tempfile
import unittest
from aybu.manager.activity_log import ActivityLog
from aybu.manager.activity_log.fs import (mkdir,
                                          create,
                                          copy,
                                          rm,
                                          rmdir,
                                          rmtree)
from aybu.manager.activity_log.exc import TransactionError
from aybu.manager.activity_log.template import render


class ActivityLogTests(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)


    def test_create(self):
        al = ActivityLog()

        # test rollback
        file_= os.path.join(self.tempdir, 'test.txt')
        al.add(create, file_)
        self.assertTrue(os.path.exists(file_))
        al.rollback()
        self.assertFalse(os.path.exists(file_))

        # test successfull create
        al.add(create, file_)
        al.commit()
        self.assertTrue(os.path.exists(file_))

        # test unsuccessfull create
        with self.assertRaises(OSError):
            al.add(create, file_)
        self.assertTrue(os.path.exists(file_))

    def test_transaction_status(self):
        al = ActivityLog(autobegin=False)
        with self.assertRaises(TransactionError):
            al.commit()
        with self.assertRaises(TransactionError):
            al.rollback()

        al.begin()
        al.commit()

        with self.assertRaises(TransactionError):
            al.commit()

    def test_transaction(self):
        al = ActivityLog()
        dir_ = os.path.join(self.tempdir, 'test')
        join = os.path.join

        def dostuff():
            al.add(mkdir, dir_)
            al.add(create, join(dir_, 'testfile.txt'), content="Test")
            al.add(copy, join(dir_, 'testfile.txt'), join(dir_, 'test2.txt'))

        dostuff()
        al.rollback()
        self.assertFalse(os.path.exists(join(dir_, 'test2.txt')))
        self.assertFalse(os.path.exists(join(dir_, 'testfile.txt')))
        self.assertFalse(os.path.exists(dir_))

        dostuff()
        al.commit()
        self.assertTrue(os.path.exists(dir_))
        self.assertTrue(os.path.exists(join(dir_, 'testfile.txt')))
        self.assertTrue(os.path.exists(join(dir_, 'test2.txt')))

    def test_failed_rollback(self):
        al = ActivityLog()
        dir_ = os.path.join(self.tempdir, 'test')
        inner_dir = os.path.join(dir_, 'inner')
        al.add(mkdir, dir_)
        al.add(mkdir, inner_dir)

        os.chmod(dir_, stat.S_IRUSR|stat.S_IXUSR)
        with self.assertRaises(OSError):
            al.rollback()

        self.assertTrue(os.path.exists(dir_))
        self.assertTrue(os.path.exists(inner_dir))

        os.chmod(dir_, stat.S_IRWXU | stat.S_IRWXG)

    def test_error_on_exists(self):
        al = ActivityLog()
        dir_ = os.path.join(self.tempdir, 'test')
        al.add(mkdir, dir_)
        al.commit()

        al.add(mkdir, dir_, error_on_exists=False)
        al.rollback()
        self.assertTrue(os.path.exists(dir_))


    def test_render(self):
        al = ActivityLog()
        instance = namedtuple('Instance', ['paths', 'environment'])(
            paths=namedtuple('Paths', ['config'])(
                config='MYDUMMYCONFIG'
            ),
            environment= namedtuple('Environment', ['smtp_config', 'os_config'])(
                smtp_config=None,
                os_config=None
            )
        )
        template_name = 'main.py.mako'
        target = os.path.join(self.tempdir, 'main.py')
        al.add(render, instance, template_name, target)
        self.assertTrue(os.path.exists(target))
        with open(target) as f:
            self.assertIn('MYDUMMYCONFIG', f.read())
        al.rollback()
        self.assertFalse(os.path.exists(target))

        al.add(render, instance, template_name, target, deferred=True)
        self.assertFalse(os.path.exists(target))
        al.commit()
        self.assertTrue(os.path.exists(target))


    def test_delete(self):
        al = ActivityLog()
        testfile = os.path.join(self.tempdir, 'test.txt')

        with self.assertRaises(OSError):
            al.add(rm, testfile)

        al.add(rm, testfile, error_on_not_exists=False)
        al.commit()

        with open(testfile, "w") as f:
            f.write("###")

        al.add(rm, testfile)
        self.assertFalse(os.path.exists(testfile))

        al.rollback()
        self.assertTrue(os.path.exists(testfile))

        al.add(rm, testfile)
        self.assertFalse(os.path.exists(testfile))
        al.commit()
        self.assertFalse(os.path.exists(testfile))

        testdir = os.path.join(self.tempdir, 'test')
        al.add(mkdir, testdir)
        al.commit()

        # test rmdir
        al.add(rmdir, testdir)
        self.assertFalse(os.path.exists(testdir))
        al.rollback()
        self.assertTrue(os.path.exists(testdir))
        al.add(rmdir, testdir)
        al.commit()
        self.assertFalse(os.path.exists(testdir))

        # test rmtree
        al.add(mkdir, testdir)
        inner = os.path.join(testdir, 'inner')
        al.add(mkdir, inner)
        al.commit()

        al.add(rmtree, testdir)
        self.assertFalse(os.path.exists(testdir))
        al.rollback()
        self.assertTrue(os.path.exists(testdir))
        al.add(rmtree, testdir)
        al.commit()
        self.assertFalse(os.path.exists(testdir))


