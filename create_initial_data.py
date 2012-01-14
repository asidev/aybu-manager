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
import pkg_resources
import argparse

import alembic
import alembic.config
import os
import sys

from aybu.manager.models import (Base,
                                 import_from_json)
from paste.deploy.loadwsgi import appconfig
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker


def parse_args(arguments):
    parser = argparse.ArgumentParser(description='setup database')
    parser.add_argument('configfile', metavar='CONFIG', help='config file')
    args = parser.parse_args()
    return os.path.realpath(args.configfile)


def parse_config(configfile):
    return appconfig('config:' + configfile + '#aybu-manager')


def setup_alembic(configfile):
    config = alembic.config.Config(configfile)
    alembic.command.stamp(config, 'head')


def import_data(config):
    engine = engine_from_config(config, prefix='sqlalchemy.')
    Session = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.drop_all()
    Base.metadata.create_all()
    session = Session()
    session.configure(bind=engine)
    try:
        import_from_json(session,
                         pkg_resources.resource_stream(
                             'aybu.manager.data', 'manager_default_data.json'))
        session.flush()

    except:
        session.rollback()
        raise

    else:
        session.commit()

    finally:
        session.close()
        session.close_all()


if __name__ == '__main__':

    cfile = parse_args(sys.argv)
    config = parse_config(cfile)
    setup_alembic(cfile)
    import_data(config)
