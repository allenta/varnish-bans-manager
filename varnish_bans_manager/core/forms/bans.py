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
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.core.helpers.paginator import Paginator
from varnish_bans_manager.core.models import BanSubmission, Node, Group, Setting
from varnish_bans_manager.core.forms.base import FallbackIntegerField, BetterChoiceField, FallbackCharField, SortDirectionField


class TargetField(BetterChoiceField):
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
        self.choices = self.choices + choices

    def clean(self, value):
        """
        Returns a Cache instance.
        """
        value = super(TargetField, self).clean(value)
        if value:
            cache = self._parse_choice_value(value)
            if cache is None:
                raise ValidationError(self.error_messages['invalid'])
            return cache
        else:
            return None

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
        label=_('Target'),
        placeholder=_('select'))

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


class SubmissionsForm(forms.Form):
    ITEMS_PER_PAGE_CHOICES = [10, 20, 50]
    SORT_CRITERIA_CHOICES = (
        ('launched_at', _('Submission date')),
    )

    user = BetterChoiceField(
        choices=(),
        required=False,
        placeholder=_('all submitters'))
    ban_type = BetterChoiceField(
        choices=BanSubmission.BAN_TYPE_CHOICES,
        required=False,
        placeholder=_('all types'))
    target = TargetField(
        required=False,
        placeholder=_('all targets'))
    items_per_page = FallbackIntegerField(choices=ITEMS_PER_PAGE_CHOICES)
    page = FallbackIntegerField(default=1, min_value=1)
    sort_criteria = FallbackCharField(choices=[id for (id, name) in SORT_CRITERIA_CHOICES])
    sort_direction = SortDirectionField(default='desc')

    def __init__(self, *args, **kwargs):
        super(SubmissionsForm, self).__init__(*args, **kwargs)
        self.fields['target'].load_choices(expert=True)
        self.fields['user'].choices = \
            list(self.fields['user'].choices) + \
            sorted(
                [(user.id, user.human_name) for user in User.objects.all()],
                key=lambda item: item[1])
        self.paginator = None

    def execute(self):
        self.paginator = Paginator(
            object_list=self._query_set(),
            expander=self._expander(),
            per_page=self.cleaned_data.get('items_per_page'),
            page=self.cleaned_data.get('page'))

    def _query_set(self):
        # Sort criteria.
        order_by_prefix = '-' if self.cleaned_data.get('sort_direction') == 'desc' else ''
        result = BanSubmission.objects.\
            order_by(order_by_prefix + self.cleaned_data.get('sort_criteria'))
        # Basic filters.
        filters = {}
        for field in ('user', 'ban_type',):
            value = self.cleaned_data.get(field)
            if value:
                filters[field] = value
        # Target filter.
        target = self.cleaned_data.get('target')
        if target:
            filters['target_content_type'] = ContentType.objects.get_for_model(target)
            filters['target_id'] = target.id
        # Done!
        if filters:
            result = result.filter(**filters)
        return result

    def _expander(self):
        def fn(ban_submission):
            items = ban_submission.items.all().order_by('created_at')
            return {
                'ban_submission': ban_submission,
                'items': items,
                'errors': sum(1 for item in items if not item.success),
            }
        return fn


class StatusForm(forms.Form):
    cache = TargetField(
        placeholder=_('cache'))

    def __init__(self, *args, **kwargs):
        super(StatusForm, self).__init__(*args, **kwargs)
        self.fields['cache'].load_choices(expert=True)
