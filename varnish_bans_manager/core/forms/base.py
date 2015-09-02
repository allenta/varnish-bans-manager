# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.core.exceptions import ValidationError
from django.core import validators
from django.forms import IntegerField, CharField, BooleanField, ChoiceField, Field
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from django.forms.widgets import SelectMultiple


class FallbackMixinField(object):
    def __init__(self, default=None, choices=None, *args, **kwargs):
        # Fallback fields are never required. Trying to require them should be
        # an error.
        kwargs.setdefault('required', False)
        assert not kwargs['required'], 'No fallback field can be set as '\
            'required.'
        # Set default value and choices.
        assert default is not None or choices, 'All fallback fields should '\
            'provide a default value or/and a non-empty choices list.'
        self.default = choices[0] if default is None else default
        self.choices = choices
        # Done!
        super(FallbackMixinField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(FallbackMixinField, self).clean(value)
        if value in validators.EMPTY_VALUES or\
           (self.choices is not None and value not in self.choices):
            value = self.default
        return value


class FallbackIntegerField(FallbackMixinField, IntegerField):
    pass


class FallbackCharField(FallbackMixinField, CharField):
    pass


class FallbackBooleanField(FallbackMixinField, BooleanField):
    pass


class SortDirectionField(FallbackCharField):
    def __init__(self, *args, **kwargs):
        assert 'choices' not in kwargs, 'No custom choices can be set for a'\
            'SortDirectionField'
        kwargs['choices'] = ['asc', 'desc']
        super(SortDirectionField, self).__init__(*args, **kwargs)


class BetterChoiceField(ChoiceField):
    def __init__(self, choices=(), placeholder=None, *args, **kwargs):
        placeholder_with_decorations = \
            string_concat('- ', placeholder, ' -') if placeholder else u''
        choices = [(None, placeholder_with_decorations)] + list(choices)
        super(BetterChoiceField, self).__init__(
            choices=choices, *args, **kwargs)

    def clean(self, value):
        value = super(BetterChoiceField, self).clean(value)
        return None if value == u'' else value


class IntegerListField(Field):
    widget = SelectMultiple

    default_error_messages = {
        'invalid_list': _('Enter a list of integer values.'),
        'min_value': _(
            'Ensure all values are greater than or equal to %(min)d.'),
        'max_value': _(
            'Ensure all values are less than or equal to %(max)d.'),
    }

    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        super(IntegerListField, self).__init__(*args, **kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def to_python(self, value):
        if not value:
            return []
        elif not isinstance(value, (list, tuple)):
            raise ValidationError(
                self.error_messages['invalid_list'], code='invalid_list')
        return [int(val) for val in value]

    def validate(self, value):
        if self.required and not value:
            raise ValidationError(
                self.error_messages['required'], code='required')
        for val in value:
            if self.min_value is not None and val < self.min_value:
                raise ValidationError(
                    self.error_messages['min_value'],
                    code='min_value',
                    params={
                        'min': self.min_value,
                    })
            elif self.max_value is not None and val > self.max_value:
                raise ValidationError(
                    self.error_messages['max_value'],
                    code='max_value',
                    params={
                        'max': self.max_value,
                    })
