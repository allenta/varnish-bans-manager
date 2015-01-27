# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.conf import settings
from django import forms
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.core.models import Setting


class GeneralForm(forms.Form):
    host_matching_variable = forms.CharField(
        label=_('Host matching variable'),
        max_length=128,
        required=False)

    url_matching_variable = forms.CharField(
        label=_('URL matching variable'),
        max_length=128,
        required=False)

    base_ban_expression = forms.CharField(
        label=_('Base ban expression'),
        help_text=_(
            'Restrict bans submitted using the basic and advanced forms '
            'writing here a base ban expression which will be merged with '
            'user defined expressions.'),
        max_length=1024,
        required=False)

    notify_bans = forms.BooleanField(
        help_text=_(
            'Adjust VBM settings file to use a different e-mail address.'),
        required=False)

    def __init__(self, *args, **kwargs):
        super(GeneralForm, self).__init__(*args, **kwargs)
        self.fields['host_matching_variable'].help_text = _(
            'If not specified, defaults to <code>%s</code> for lurker '
            'friendly bans.'
        ) % Setting.DEFAULT_HOST_MATCHING_VARIABLE
        self.fields['url_matching_variable'].help_text = _(
            'If not specified, defaults to <code>%s</code> for lurker '
            'friendly bans.'
        ) % Setting.DEFAULT_URL_MATCHING_VARIABLE
        self.fields['notify_bans'].label = _(
            'Deliver periodical ban submission reports to <code>%s</code>.'
        ) % settings.VBM_NOTIFICATIONS_EMAIL
        for field_name in self.fields.keys():
            self.initial[field_name] = getattr(Setting, field_name)

    def save(self):
        for field_name in self.fields.keys():
            value = self.cleaned_data.get(field_name)
            if isinstance(value, basestring):
                value = value.strip()
            if value == '':
                delattr(Setting, field_name)
            else:
                setattr(Setting, field_name, value)
