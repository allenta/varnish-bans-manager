# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.core.models.base import Model, RevisionField
from varnish_bans_manager.core.models.ban_submission import BanSubmission
from varnish_bans_manager.core.helpers.cli import Varnish


class Cache(Model):
    ban_submissions = GenericRelation(
        BanSubmission,
        content_type_field='target_content_type',
        object_id_field='target_id'
    )

    def _human_name(self):
        raise NotImplementedError('Please implement this method')

    human_name = property(_human_name)

    def _human_class_name(self):
        return self.__class__.verbose_name

    human_class_name = property(_human_class_name)

    def _items(self):
        raise NotImplementedError('Please implement this method')

    items = property(_items)

    def __iter__(self):
        for item in self.items:
            yield item

    def __unicode__(self):
        return self.human_name

    class Meta:
        abstract = True


class Group(Cache):
    name = models.CharField(
        _('Name'),
        help_text=_(
            'Some name used internally by VBM to refer to the group of '
            'caching nodes.'),
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

    # Cache methods.
    def _human_name(self):
        return self.name

    human_name = property(_human_name)

    def _items(self):
        return self.nodes.all().order_by('weight', 'created_at')

    items = property(_items)

    class Meta:
        verbose_name = _('cache group')
        verbose_name_plural = _('cache groups')


class Node(Cache):
    VERSION_21 = 21
    VERSION_30 = 30
    VERSION_CHOICES = (
        (VERSION_21, '2.1'),
        (VERSION_30, '>= 3.0'),
    )

    name = models.CharField(
        _('Name'),
        help_text=_(
            'Some name used internally by VBM to refer to the cache node. If '
            'not provided, the host and port number of the node will be '
            'used.'),
        max_length=255,
        null=True,
        blank=True
    )
    host = models.CharField(
        _('Host'),
        help_text=_(
            'Name or IP address of the server running the Varnish cache '
            'node.'),
        max_length=255,
        null=False
    )
    port = models.PositiveIntegerField(
        _('Port'),
        help_text=_('Varnish management port number.'),
        null=False
    )
    secret = models.TextField(
        _('Secret'),
        help_text=_(
            'If the -S secret-file is used in the cache node, provide here '
            'the contents of that file in order to authenticate CLI '
            'connections opened by VBM.'),
        max_length=65536,
        null=True,
        blank=True,
    )
    version = models.SmallIntegerField(
        _('Version'),
        help_text=_('Select the Varnish version running in the cache node.'),
        choices=VERSION_CHOICES,
        default=VERSION_30,
        null=False
    )
    weight = models.SmallIntegerField(
        default=0,
        null=False
    )
    group = models.ForeignKey(
        Group,
        related_name='nodes',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
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

    def ban(self, expression):
        self._cli('ban', expression)

    def ban_list(self):
        return self._cli('ban_list')

    def _cli(self, name, *args):
        varnish = Varnish(
            self.host, int(self.port), self.human_name,
            secret=self.secret,
            version=self.version)
        try:
            return getattr(varnish, name)(*args)
        finally:
            varnish.quit()

    # Cache methods.

    def _human_name(self):
        return self.name if self.name else '%s:%d' % (self.host, self.port,)

    human_name = property(_human_name)

    def _items(self):
        return [self]

    items = property(_items)

    class Meta:
        verbose_name = _('cache node')
        verbose_name_plural = _('cache nodes')
