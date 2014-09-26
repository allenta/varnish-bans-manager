# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.filesystem import randomize_filename
from varnish_bans_manager.filesystem.models import ImageField
from varnish_bans_manager.core.models import User
from varnish_bans_manager.core.models.base import Model, RevisionField


def _photo_upload_destination(instance, filename):
    return 'users/%d/%s' % (instance.user.id, randomize_filename(filename))


def _create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(_create_user_profile, sender=User)


class UserProfile(Model):
    user = models.OneToOneField(
        User,
        related_name='profile',
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

    class Meta:
        app_label = 'core'
