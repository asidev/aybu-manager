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

import json

from . alias import Alias
from . instance import Instance
from . redirect import Redirect
from . environment import Environment
from . user import User, Group
from . theme import Theme
from . base import Base


__all__ = ['Instance', 'Environment', 'Redirect', 'User', 'Group', 'Theme',
           'Base', 'Alias', 'import_from_json']


def import_from_json(session, source):

    source_ = open(source) if isinstance(source, basestring) else source
    data = json.loads(source_.read())
    if isinstance(source, basestring):
        source_.close()

    for obj_data in data:
        cls = globals()[obj_data.pop('cls_')]
        if cls == Theme and 'parent_name' not in obj_data:
            obj_data['parent_name'] = 'base'
        if cls == User:
            groups = obj_data.pop("groups", [])
        obj = cls(**obj_data)

        if cls == User:
            for group_name in groups:
                group = Group.get(session, group_name)
                obj.groups.append(group)

        session.merge(obj)
