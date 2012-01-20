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

import os.path
from aybu.manager.activity_log.command import command


def dump_database(config, dump_dir, dump_name=None):
    dump_name = config.type if not dump_name else dump_name
    dump_name = "{}.sql".format(dump_name)
    dump_path = os.path.join(dump_dir, dump_name)

    if config.type == 'mysql':
        dump_cmd = "mysqldump {config.name} --add-drop-database "\
                    " --single-transaction -r {dump_path}"\
                    .format(config=config, dump_path=dump_path)
    elif config.type == 'postgresql':
        dump_cmd = "pg_dump -C {config.name} -f {dump_path}"\
                    .format(config=config, dump_path=dump_path)
    else:
        raise ValueError("Invalid db type {}".format(config.type))

    return command(dump_cmd, on_init=True)
