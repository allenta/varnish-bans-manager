# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
import re
from urlparse import urlparse
from django import forms
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.core.models import Cache, Group, Setting


class TargetField(forms.ChoiceField):
    CACHE_CHOICE_PREFIX = 'c'
    GROUP_CHOICE_PREFIX = 'g'

    default_error_messages = {
        'invalid_cache': _('This cache is no longer available. Please, refresh the page to update the list and choose another.'),
        'invalid_group': _('This group is no longer available. Please, refresh the page to update the list and choose another.'),
    }

    def load_choices(self, expert=False):
        """
        Build choices from current available groups and caches.
        """
        groups = Group.objects.all().order_by('weight', 'created_at')
        caches = Cache.objects.all().order_by('weight', 'created_at')
        # Add caches not linked to any group.
        choices = [(self._cache_choice_value(cache), cache.human_name) for cache in caches if cache.group_id is None]
        # Add each group with its linked caches.
        for group in groups:
            caches_in_current_group = [cache for cache in caches if cache.group_id == group.id]
            if caches_in_current_group:
                choices.append((self._group_choice_value(group), '%s (%d)' % (group.name, len(caches_in_current_group))))
                if expert:
                    choices.extend((self._cache_choice_value(cache), mark_safe('&nbsp;&nbsp;' + force_text(cache.human_name))) for cache in caches_in_current_group)
        self.choices = choices

    def clean(self, value):
        """
        Returns a list of caches.
        """
        caches = []
        value = super(TargetField, self).clean(value)
        if value.startswith(self.CACHE_CHOICE_PREFIX):
            try:
                caches = [Cache.objects.get(pk=value[len(self.CACHE_CHOICE_PREFIX):])]
            except Cache.DoesNotExist:
                raise ValidationError(self.error_messages['invalid_cache'])
        elif value.startswith(self.GROUP_CHOICE_PREFIX):
            try:
                caches = Group.objects.get(pk=value[len(self.GROUP_CHOICE_PREFIX):]).caches.all()
            except Group.DoesNotExist:
                raise ValidationError(self.error_messages['invalid_group'])
        return caches

    def _cache_choice_value(self, cache):
        return '%s%d' % (self.CACHE_CHOICE_PREFIX, cache.id)

    def _group_choice_value(self, group):
        return '%s%d' % (self.GROUP_CHOICE_PREFIX, group.id)


class SubmitForm(forms.Form):
    def _merge_base_ban_expression(self, expression):
        base_ban_expression = Setting.base_ban_expression
        if base_ban_expression != '':
            return '%s && %s' % (base_ban_expression, expression)
        return expression


class BasicForm(SubmitForm):
    url = forms.URLField(
        label=_('URL'),
        widget=forms.TextInput(attrs={'placeholder': _('URL to be removed from caches')}),
        max_length=2048)

    target = TargetField(
        label=_('Target'))

    error_messages = {
        'invalid_url_scheme': _('Only http:// and https:// schemes are supported.')
    }

    def __init__(self, *args, **kwargs):
        super(BasicForm, self).__init__(*args, **kwargs)
        self.fields['target'].load_choices(expert=False)

    def clean_url(self):
        url = self.cleaned_data['url']
        if not re.compile(r'^https?://').match(url):
            raise forms.ValidationError(self.error_messages['invalid_url_scheme'])
        return url

    def _expression(self):
        parsed = urlparse(self.cleaned_data['url'])
        return self._merge_base_ban_expression('%s == "%s" && %s == "%s"' % (
            Setting.host_matching_variable,
            parsed.netloc,
            Setting.url_matching_variable,
            parsed.path,
        ))

    expression = property(_expression)


class AdvancedForm(SubmitForm):
    regular_expression = forms.CharField(
        label=_('Regular expression'),
        widget=forms.TextInput(attrs={'placeholder': _('match contents to be removed from caches')}),
        max_length=1024)

    target = TargetField(
        label=_('Target'))

    def __init__(self, *args, **kwargs):
        super(AdvancedForm, self).__init__(*args, **kwargs)
        self.fields['target'].load_choices(expert=False)

    def _expression(self):
        regular_expression = self.cleaned_data.get('regular_expression')
        return self._merge_base_ban_expression('%s ~ %s' % (
            Setting.url_matching_variable,
            regular_expression,
        ))

    expression = property(_expression)


class ExpertForm(SubmitForm):
    ban_expression = forms.CharField(
        label=_('Ban expression'),
        widget=forms.Textarea(attrs={'placeholder': _('match contents to be removed from caches'), 'rows': 4}),
        max_length=1024)

    target = TargetField(
        label=_('Target'))

    def __init__(self, *args, **kwargs):
        super(ExpertForm, self).__init__(*args, **kwargs)
        self.fields['target'].load_choices(expert=True)

    def _expression(self):
        return self.cleaned_data.get('ban_expression')

    expression = property(_expression)
