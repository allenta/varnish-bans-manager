# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from ordereddict import OrderedDict
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


PERMISSIONS = OrderedDict([
    ('can_access_advanced_ban_submission', _('Advanced')),
    ('can_access_expert_ban_submission', _('Expert')),
    ('can_access_bans_submissions', _('Submissions')),
    ('can_access_bans_status', _('Status')),
    ('can_access_caches_management', _('Caches')),
    ('can_access_users_management', _('Users')),
    ('can_access_settings', _('Settings')),
])


class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        extra_fields.update({'is_staff': False, 'is_superuser': False})
        return self._build_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.update({'is_staff': True, 'is_superuser': True})
        return self._build_user(email, password, **extra_fields)

    def _build_user(self, email, password, **extra_fields):
        now = timezone.now()
        email = UserManager.normalize_email(email)
        user = self.model(email=email, is_active=True, last_login=now,
                          date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def get_full_name(self):
        if self.first_name or self.last_name:
            return ', '.join([self.last_name, self.first_name])
        else:
            return self.email

    def get_short_name(self):
        return self.first_name if self.first_name else self.email

    human_name = property(get_full_name)

    def editable_user_permission_labels(self):
        permissions = filter(
            lambda permission: permission.codename in PERMISSIONS,
            self.user_permissions.all())
        return [PERMISSIONS[permission.codename] for permission in permissions]

    class Meta:
        app_label = 'core'
        permissions = (
            ('can_access_advanced_ban_submission', 'Access advanced ban submission form'),
            ('can_access_expert_ban_submission', 'Access expert ban submission form'),
            ('can_access_bans_submissions', 'Access bans submissions'),
            ('can_access_bans_status', 'Access bans status'),
            ('can_access_caches_management', 'Access caches management'),
            ('can_access_users_management', 'Access users management'),
            ('can_access_settings', 'Access settings'),
        )
        verbose_name = _('user')
        verbose_name_plural = _('users')
