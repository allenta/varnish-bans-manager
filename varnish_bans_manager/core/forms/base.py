# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.core.exceptions import ValidationError
from django.core import validators
from django.forms import IntegerField, CharField, BooleanField, ChoiceField, Field
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import SelectMultiple


class FallbackMixinField(object):
    def __init__(self, default=None, choices=None, *args, **kwargs):
        self.default = choices[0] if default is None else default
        self.choices = choices
        super(FallbackMixinField, self).__init__(required=False, *args, **kwargs)

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
    def __init__(self, default=None, *args, **kwargs):
        super(SortDirectionField, self).__init__(choices=['asc', 'desc'], default=default, *args, **kwargs)


class BetterChoiceField(ChoiceField):
    def __init__(self, choices=(), placeholder=None, *args, **kwargs):
        choices = tuple([(u'', (u'- %s -' % unicode(placeholder)) if placeholder else u'')] + list(choices))
        super(BetterChoiceField, self).__init__(choices=choices, *args, **kwargs)

    def clean(self, value):
        value = super(BetterChoiceField, self).clean(value)
        return None if value == u'' else value


class IntegerListField(Field):
    widget = SelectMultiple

    default_error_messages = {
        'invalid_list': _('Enter a list of integer values.'),
        'min_value': _('Ensure all values are greater than or equal to %s.'),
        'max_value': _('Ensure all values are less than or equal to %s.'),
    }

    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        super(IntegerListField, self).__init__(*args, **kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def to_python(self, value):
        if not value:
            return []
        elif not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages['invalid_list'])
        return [int(val) for val in value]

    def validate(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages['required'])
        for val in value:
            if self.min_value is not None and val < self.min_value:
                raise ValidationError(self.error_messages['min_value'] % self.min_value)
            elif self.max_value is not None and val > self.max_value:
                raise ValidationError(self.error_messages['max_value'] % self.max_value)
