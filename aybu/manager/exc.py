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


class OperationalError(Exception):
    pass


class NotSupported(OperationalError):

    def __init__(self, operation, msg):
        self.operation = operation
        super(NotSupported, self).__init__(msg)


class ValidationError(Exception):
    pass


class RestError(Exception):
    pass


class TaskExistsError(RestError):
    pass


class ParamsError(RestError):
    pass


class TaskNotFoundError(RestError):
    pass
