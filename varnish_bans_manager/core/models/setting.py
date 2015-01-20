# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.db import models
from varnish_bans_manager.core.models.base import Model, JSONField


class Setting(Model):
    DEFAULT_HOST_MATCHING_VARIABLE = 'obj.http.x-host'
    DEFAULT_URL_MATCHING_VARIABLE = 'obj.http.x-url'

    name = models.CharField(
        max_length=255,
        null=False,
        db_index=True,
        unique=True
    )
    value = JSONField(
        max_length=1024,
        null=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=False
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=False
    )


class SettingMetaclass(Setting.__class__):
    def _property(name, default):
        def fget(cls):
            try:
                return cls.objects.get(name__iexact=name).value
            except cls.DoesNotExist:
                return default

        def fset(cls, value):
            try:
                setting = cls.objects.get(name__iexact=name)
                setting.value = value
            except cls.DoesNotExist:
                setting = cls(name=name, value=value)
            setting.save()

        def fdel(cls):
            try:
                cls.objects.get(name__iexact=name).delete()
            except cls.DoesNotExist:
                pass

        return (fget, fset, fdel)

    host_matching_variable = property(*_property(
        'host_matching_variable',
        Setting.DEFAULT_HOST_MATCHING_VARIABLE))
    url_matching_variable = property(*_property(
        'url_matching_variable', Setting.DEFAULT_URL_MATCHING_VARIABLE))
    base_ban_expression = property(*_property(
        'base_ban_expression', ''))
    notify_bans = property(*_property(
        'notify_bans', False))
    notify_bans_task_status = property(*_property(
        'notify_bans_task_status', None))


Setting.__class__ = SettingMetaclass
