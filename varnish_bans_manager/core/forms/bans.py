# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
import re
from urlparse import urlparse
from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.core.models import BanSubmission, Node, Group, Setting


class TargetField(forms.ChoiceField):
    default_error_messages = {
        'invalid': _('The selected item is no longer available. Please, refresh the page to update the list and choose another.'),
    }

    def load_choices(self, expert=False):
        """
        Build choices from current available groups and nodes.
        """
        groups = Group.objects.all().order_by('weight', 'created_at')
        nodes = Node.objects.all().order_by('weight', 'created_at')
        # Add nodes not linked to any group.
        choices = [(self._build_choice_value(node), node.human_name) for node in nodes if node.group_id is None]
        # Add each group with its linked nodes.
        for group in groups:
            nodes_in_current_group = [node for node in nodes if node.group_id == group.id]
            if nodes_in_current_group:
                choices.append((self._build_choice_value(group), '%s (%d)' % (group.name, len(nodes_in_current_group))))
                if expert:
                    choices.extend((self._build_choice_value(node), mark_safe('&nbsp;&nbsp;' + force_text(node.human_name))) for node in nodes_in_current_group)
        self.choices = choices

    def clean(self, value):
        """
        Returns a Cache instance.
        """
        value = super(TargetField, self).clean(value)
        cache = self._parse_choice_value(value)
        if cache is None:
            raise ValidationError(self.error_messages['invalid'])
        return cache

    def _build_choice_value(self, cache):
        return '%d:%d' % (ContentType.objects.get_for_model(cache).id, cache.id)

    def _parse_choice_value(self, choice):
        (content_type_id, cache_id) = choice.split(':')
        try:
            content_type = ContentType.objects.get_for_id(int(content_type_id))
            return content_type.get_object_for_this_type(pk=int(cache_id))
        except ObjectDoesNotExist:
            return None


class SubmitForm(forms.Form):
    target = TargetField(
        label=_('Target'))

    def __init__(self, user, *args, **kwargs):
        super(SubmitForm, self).__init__(*args, **kwargs)
        self.user = user

    def _merge_base_ban_expression(self, expression):
        base_ban_expression = Setting.base_ban_expression
        if base_ban_expression != '':
            return '%s && %s' % (base_ban_expression, expression)
        return expression

    def _ban_submission(self):
        return BanSubmission(
            user=self.user,
            ban_type=self.ban_type,
            expression=self.expression,
            target=self.cleaned_data.get('target'))

    ban_submission = property(_ban_submission)


class BasicForm(SubmitForm):
    ban_type = BanSubmission.BASIC_TYPE

    url = forms.URLField(
        label=_('URL'),
        widget=forms.TextInput(attrs={'placeholder': _('URL to be removed from caches')}),
        max_length=2048)

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
    ban_type = BanSubmission.ADVANCED_TYPE

    regular_expression = forms.CharField(
        label=_('Regular expression'),
        widget=forms.TextInput(attrs={'placeholder': _('match contents to be removed from caches')}),
        max_length=1024)

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
    ban_type = BanSubmission.EXPERT_TYPE

    ban_expression = forms.CharField(
        label=_('Ban expression'),
        widget=forms.Textarea(attrs={'placeholder': _('match contents to be removed from caches'), 'rows': 4}),
        max_length=1024)

    def __init__(self, *args, **kwargs):
        super(ExpertForm, self).__init__(*args, **kwargs)
        self.fields['target'].load_choices(expert=True)

    def _expression(self):
        return self.cleaned_data.get('ban_expression')

    expression = property(_expression)
