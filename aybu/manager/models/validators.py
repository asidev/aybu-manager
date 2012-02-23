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
from distutils.version import StrictVersion
from pyramid.httpexceptions import HTTPConflict
from sqlalchemy.orm.exc import NoResultFound
from .. exc import ValidationError

name_re = re.compile(r'^[A-Za-z_0-9][\w\._]*$')

# hostname_re and email_re shamelessly stolen from django.core.validators
hostname_re = re.compile(
r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
r'localhost|'
r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
r'(?::\d+)?'
r'(?:/?|[/?]\S+)$', re.IGNORECASE)
email_re = re.compile(
r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'
r')@((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$)'
r'|\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$',
re.IGNORECASE)


def validate_name(name):
    if name_re.match(name) is None:
        raise ValidationError("Invalid name {}".format(name))
    return name


def validate_password(password):
    # nothing as of now
    return password


def validate_hostname(source):
    if len(source) > 255:
        raise ValidationError('hostname too long')

    if source.endswith('.') or \
      not hostname_re.match(source):
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


def validate_version(version):
    validator = StrictVersion()
    try:
        validator.parse(version)

    except:
        raise ValidationError('invalid version {}'.format(version))

    return version


def validate_positive_int(number):
    try:
        number = int(number)
        assert number > 0

    except:
        raise ValidationError('{} is not a positive integer'.format(number))

    return number


def validate_web_address(address):
    if not address:
        return ''

    error = 'Invalid http link {}'.format(address)
    if not isinstance(address, basestring):
        raise ValidationError(error)

    if not address.startswith('http://'):
        address = 'http://{}'.format(address)

    parts = address.split('//')[1].split('/', 1)
    hostname = parts[0]
    target_path = ''

    try:
        hostname = validate_hostname(hostname)
        if len(parts) > 1:
            target_path = validate_redirect_target_path('/' + parts[1])
    except:
        raise ValidationError(error)

    return 'http://{}{}'.format(hostname, target_path)


def validate_twitter(twitter):
    error = 'Invalid twitter name {}'.format(twitter)
    try:
        if not twitter:
            return ''
        return "@{}".format(validate_name(twitter.split('@')[1]))

    except:
        raise ValidationError(error)


def validate_email(email):
    if not email_re.match(email) or email.endswith('.'):
        raise ValidationError('Invalid email addres {}'.format(email))
    return email


def validate_language(lang):
    try:
        assert re.match("^[a-zA-Z][\w]$", lang)
        return lang.lower()

    except:
        raise ValidationError('Invalid language {}'.format(lang))


def check_domain_not_used(request, domain):
    from aybu.manager.models import (Instance, Alias, Redirect)
    for fun, name in ((Alias.get, "alias"), (Redirect.get, 'redirect'),
                  (Instance.get_by_domain, "instance")):
        try:
            fun(request.db_session, domain)

        except NoResultFound:
            pass

        else:
            error = 'domain {} already exists as {}'.format(domain, name)
            raise HTTPConflict(headers={'X-Request-Error': error})
