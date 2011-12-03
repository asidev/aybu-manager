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

import re
import urllib
from .. exc import ValidationError


def validate_hostname(source):
    if len(source) > 255:
        raise ValidationError('hostname too long')

    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    if not '.' in source\
      or source[-1:] == "."\
      or not all(allowed.match(x) for x in source.split(".")):
        raise ValidationError("{} is not a valid hostname".format(source))

    return source


def validate_redirect_http_code(http_code):
    try:
        http_code = int(http_code)
        assert http_code in (301, 302, 303, 307)

    except (ValueError, AssertionError):
        raise ValidationError("Invalid redirection http_code {}"\
                              .format(http_code))

    else:
        return http_code


def validate_redirect_target_path(target_path):
    try:
        target_path = urllib.quote(target_path)
        assert not target_path or target_path.startswith('/')

    except AssertionError:
        raise ValidationError("Target path for redirects must be absolute")

    except TypeError:
        target_path = ''

    return unicode(target_path)
