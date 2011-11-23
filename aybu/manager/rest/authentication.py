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
import binascii

from zope.interface import implements

from paste.httpheaders import AUTHORIZATION
from paste.httpheaders import WWW_AUTHENTICATE

from pyramid.interfaces import IAuthenticationPolicy
from pyramid.security import Everyone
from pyramid.security import Authenticated

from aybu.manager.models import User

__all__ = ['AuthenticationPolicy']


def _get_basicauth_credentials(request):
    authorization = AUTHORIZATION(request.environ)
    try:
        authmeth, auth = authorization.split(' ', 1)

    except ValueError:
        # not enough values to unpack
        return None

    if authmeth.lower() == 'basic':
        try:
            auth = auth.strip().decode('base64')

        except binascii.Error:
            # can't decode
            return None

        try:
            login, password = auth.split(':', 1)

        except ValueError:
            # not enough values to unpack
            return None

        return {'email':login, 'password':password}

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

        userid = credentials['login']
        if not self.check(credentials, request) is None:
            return userid

    def effective_principals(self, request):
        effective_principals = [Everyone]
        credentials = _get_basicauth_credentials(request)
        if credentials is None:
            return effective_principals

        userid = credentials['login']
        groups = self.check(credentials, request)
        if groups is None: # is None!
            return effective_principals

        effective_principals.append(Authenticated)
        effective_principals.append(userid)
        effective_principals.extend(groups)
        return effective_principals

    def unauthenticated_userid(self, request):
        creds = self._get_credentials(request)
        if not creds is None:
            return creds['login']

        return None

    def remember(self, request, principal, **kw):
        return []

    def forget(self, request):
        head = WWW_AUTHENTICATE.tuples('Basic realm="%s"' % self.realm)
        return head


class AuthenticationPolicy(BasicAuthenticationPolicy):

    def __init__(self, realm='Realm'):
        super(AuthenticationPolicy, self).__init__(check=self.check_user,
                                                   realm=realm)

    def check_user(self, credentials, request):
        email = credentials['email']
        password = credentials['password']

        try:
            user = User.get(request.db_session, email)
            if not user.check(password):
                return None

        except:
            return None

        else:
            return [group.name for group in user.groups]
