# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend


class EmailAuthBackend(ModelBackend):
    """
    Email Authentication Backend

    Allows a user to sign in using an email/password pair rather than
    a username/password pair.

    See http://www.micahcarrick.com/django-email-authentication.html
    """

    supports_inactive_user = False

    def authenticate(self, username=None, password=None):
        """ Authenticate a user based on email address as the user name. """
        try:
            user = User.objects.filter(email__iexact=username).order_by('date_joined')[:1].get()
            return user if user.check_password(password) else None
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        """ Get a User object from the user_id. """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
