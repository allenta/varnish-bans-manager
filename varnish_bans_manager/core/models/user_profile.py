# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from ordereddict import OrderedDict
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.filesystem import randomize_filename
from varnish_bans_manager.filesystem.models import ImageField
from varnish_bans_manager.core.models.base import Model, RevisionField


PERMISSIONS = OrderedDict([
    ('can_access_advanced_ban_submission', _('Advanced')),
    ('can_access_expert_ban_submission', _('Expert')),
    ('can_access_bans_submissions', _('Submissions')),
    ('can_access_bans_status', _('Status')),
    ('can_access_caches_management', _('Caches')),
    ('can_access_users_management', _('Users')),
    ('can_access_settings', _('Settings')),
])


def _photo_upload_destination(instance, filename):
    return 'users/%d/%s' % (instance.user.id, randomize_filename(filename))


def _create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(_create_user_profile, sender=User)


def _human_name(self):
    if self.first_name or self.last_name:
        return ', '.join([self.last_name, self.first_name])
    else:
        return self.email

User.human_name = property(_human_name)


class UserProfile(Model):
    user = models.OneToOneField(
        User,
        null=False
    )
    creator = models.ForeignKey(
        User,
        related_name='+',
        null=True,
        on_delete=models.SET_NULL
    )
    photo = ImageField(
        _('Photo'),
        help_text=_('Upload a photo. It will only be visible by administrators.'),
        upload_to=_photo_upload_destination,
        null=True,
        blank=True,
        private=True,
        attachment=False,
        max_upload_size=1024 * 1024,
        content_types=['image/jpeg', 'image/png'],
        max_width=128,
        max_height=128
    )
    revision = RevisionField()

    def editable_user_permission_labels(self):
        permissions = filter(
            lambda permission: permission.codename in PERMISSIONS,
            self.user.user_permissions.all())
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
