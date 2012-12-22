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
import os


def convert_bytes(b):
    b = float(b)
    if b >= 1099511627776:
        terabytes = b / 1099511627776
        size = '%.2fT' % terabytes
    elif b >= 1073741824:
        gigabytes = b / 1073741824
        size = '%.2fG' % gigabytes
    elif b >= 1048576:
        megabytes = b / 1048576
        size = '%.2fM' % megabytes
    elif b >= 1024:
        kilobytes = b / 1024
        size = '%.2fK' % kilobytes
    else:
        size = '%.2fb' % b
    return size


class CGroupController(object):

    def __init__(self, path):
        self.group_path = path

    def to_list(self, path, convert=None):
        with open(os.path.join(self.group_path, path)) as f:
            res = f.read().strip().split("\n")

        if convert:
            return [convert(elem) for elem in res]

        return res

    def get_first_in(self, path):
        return self.to_list(path)[0]

    def to_dict(self, path, sep=" "):
        res = {}
        for l in self.to_list(path):
            k, v = l.split(sep)
            res[k.strip()] = v.strip()
        return res

    def bytes_to_str(self, path):
        return convert_bytes(self.get_first_in(path))


class CGroup(object):

    def __init__(self, paths):
        self.controllers = []
        for path in paths:
            self.controllers.append(CGroupController(path))

    @property
    def master_pid(self):
        try:
            return int(self.controllers[0].get_first_in('tasks'))

        except (IOError, ValueError):
            return None

    @property
    def tasks(self):
        tasks = set()
        for ctrl in self.controllers:
            try:
                tasks = tasks | set(ctrl.to_list('tasks', convert=int))
            except IOError:
                pass

        return tasks

    @property
    def used_memory_bytes(self):
        return self._used_memory(bytes=True)

    @property
    def used_memory(self):
        return self._used_memory()

    def _used_memory(self, bytes=False):
        for ctrl in self.controllers:
            try:
                if bytes:
                    mem = ctrl.get_first_in('memory.usage_in_bytes')
                else:
                    mem = ctrl.bytes_to_str('memory.usage_in_bytes')

            except IOError:
                continue

            else:
                return mem

        raise TypeError('Memory cgroup not available')
