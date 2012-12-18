# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.db import models
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.core.models.base import Model, RevisionField


class Group(Model):
    name = models.CharField(
        _('Name'),
        help_text=_('Some name used internally by VBM to refer to the group of caching nodes.'),
        max_length=255,
        null=False
    )
    weight = models.SmallIntegerField(
        default=0,
        null=False
    )
    revision = RevisionField()
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=False
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=False
    )

    class Meta:
        app_label = 'core'
