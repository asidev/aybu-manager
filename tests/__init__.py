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
from aybu.manager.models import Base, import_from_json


def import_data(engine, Session):
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
        Session.close_all()


def setup_metadata(engine):
    Base.metadata.bind = engine


def create_tables():
    Base.metadata.create_all()


def drop_tables():
    Base.metadata.drop_all()

