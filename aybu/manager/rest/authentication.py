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
import binascii
import logging

from zope.interface import implements
from paste.httpheaders import AUTHORIZATION
from paste.httpheaders import WWW_AUTHENTICATE
from pyramid.interfaces import IAuthenticationPolicy
import pyramid.httpexceptions
import pyramid.security
from pyramid.security import (Allow,
                              Authenticated,
                              ALL_PERMISSIONS,
                              DENY_ALL)
from aybu.manager.models import User


log = logging.getLogger(__name__)
__all__ = ['AuthenticationPolicy', 'AuthenticatedFactory']


def _get_basicauth_credentials(request):
    try:
        authorization = AUTHORIZATION(request.environ)
        authmeth, auth = authorization.split(' ', 1)
        assert authmeth.lower() == 'basic'
        auth = auth.strip().decode('base64')
        username, password = auth.split(':', 1)
        return {'username': username, 'password': password}

    except (AssertionError, ValueError, binascii):
        return None


class BasicAuthenticationPolicy(object):
    """ A :app:`Pyramid` :term:`authentication policy` which
    obtains data from basic authentication headers.

    Constructor Arguments

    ``check``

        A callback passed the credentials and the request,
        expected to return None if the userid doesn't exist or a sequence
        of group identifiers (possibly empty) if the user does exist.
        Required.

    ``realm``

        Default: ``Realm``.  The Basic Auth realm string.

    """
    implements(IAuthenticationPolicy)

    def __init__(self, check, realm='Realm'):
        self.check = check
        self.realm = realm

    def authenticated_userid(self, request):
        credentials = _get_basicauth_credentials(request)
        if credentials is None:
            return None

        userid = credentials['username']
        if not self.check(credentials, request) is None:
            return userid

    def effective_principals(self, request):
        effective_principals = [pyramid.security.Everyone]
        credentials = _get_basicauth_credentials(request)
        if credentials is None:
            return effective_principals

        userid = credentials['username']
        groups = self.check(credentials, request)
        if groups is None:  # is None!
            return effective_principals

        effective_principals.append(pyramid.security.Authenticated)
        effective_principals.extend(groups)
        effective_principals.append(userid)
        return effective_principals

    def unauthenticated_userid(self, request):
        creds = self._get_credentials(request)
        if not creds is None:
            return creds['username']

        return None

    def remember(self, request, principal, **kw):
        return []

    def forget(self, request):
        head = WWW_AUTHENTICATE.tuples('Basic realm="%s"' % self.realm)
        return head


class AuthenticationPolicy(BasicAuthenticationPolicy):

    def __init__(self, realm='Realm'):
        log.info("Creating AuthenticationPolicy for realm %s", realm)
        super(AuthenticationPolicy, self).__init__(check=self.check_user,
                                                   realm=realm)

    def check_user(self, credentials, request):
        username = credentials['username']
        password = credentials['password']

        try:
            user = User.check(request.db_session, username, password)

        except:
            return None

        else:
            groups = [group.name for group in user.groups]
            return groups


class AuthenticatedFactory(object):
    """ User must be logged in, but no special permission
        is required
    """
    __acl__ = [(Allow, 'admin', ALL_PERMISSIONS),
               (Allow, Authenticated, 'user'),
               DENY_ALL]

    def __init__(self, request):
        pass
