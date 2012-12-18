# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from urllib import urlencode
from abc import ABCMeta
from random import choice
from string import letters
from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db import transaction
from django.forms.widgets import CheckboxSelectMultiple
from django.contrib.auth.models import Permission
from varnish_bans_manager.core.models import UserProfile
from varnish_bans_manager.core.models.user_profile import PERMISSIONS
from varnish_bans_manager.core.helpers.paginator import Paginator
from varnish_bans_manager.core.forms.base import FallbackIntegerField, FallbackCharField, FallbackBooleanField, SortDirectionField, IntegerListField


class CollectionForm(forms.Form):
    ITEMS_PER_PAGE_CHOICES = [10, 20, 50]
    SORT_CRITERIA_CHOICES = (
        ('last_name', _('Last name')),
        ('date_joined', _('Creation date')),
    )
    OP_CHOICES = (
        ('download_csv', _('Download CSV')),
        ('delete', _('Delete')),
    )

    email = FallbackCharField(
        widget=forms.TextInput(attrs={'placeholder': _('e-mail address')}),
        default='',
        max_length=128)
    first_name = FallbackCharField(
        widget=forms.TextInput(attrs={'placeholder': _('first name')}),
        default='',
        max_length=128)
    last_name = FallbackCharField(
        widget=forms.TextInput(attrs={'placeholder': _('last name')}),
        default='',
        max_length=128)
    items_per_page = FallbackIntegerField(choices=ITEMS_PER_PAGE_CHOICES)
    page = FallbackIntegerField(default=1, min_value=1)
    sort_criteria = FallbackCharField(choices=[id for (id, name) in SORT_CRITERIA_CHOICES])
    sort_direction = SortDirectionField(default='asc')

    def _base_query_set(self):
        return User.objects.\
            filter(is_active=True)

    def _query_set(self):
        order_by_prefix = '-' if self.cleaned_data.get('sort_direction') == 'desc' else ''
        result = self._base_query_set().\
            order_by(order_by_prefix + self.cleaned_data.get('sort_criteria'))
        filters = {}
        for field in ('email', 'first_name', 'last_name'):
            if self.cleaned_data.get(field):
                filters[field + '__icontains'] = self.cleaned_data.get(field)
        if filters:
            result = result.filter(**filters)
        return result


class BrowseForm(CollectionForm):
    def __init__(self, *args, **kwargs):
        super(BrowseForm, self).__init__(*args, **kwargs)
        self.paginator = None

    def execute(self):
        self.paginator = Paginator(object_list=self._query_set(), per_page=self.cleaned_data.get('items_per_page'), page=self.cleaned_data.get('page'))


class BulkForm(CollectionForm):
    op = forms.ChoiceField(choices=CollectionForm.OP_CHOICES)
    all_items = FallbackBooleanField(default=False)
    items = IntegerListField(min_value=1, required=False)

    def __init__(self, *args, **kwargs):
        super(BulkForm, self).__init__(*args, **kwargs)
        self.ids = []

    def execute(self):
        if self.cleaned_data.get('all_items'):
            items = self._query_set()
        else:
            items = self._base_query_set().\
                filter(id__in=self.cleaned_data.get('items'))
        self.ids = items.values_list('id', flat=True)

    def get_url(self, reset_page=False):
        fields = self.fields.keys()
        # Remove bulk specific fields.
        fields.remove('op')
        fields.remove('all_items')
        fields.remove('items')
        # Optionally remove page field.
        if reset_page:
            fields.remove('page')
        return reverse('users-browse') + \
            '?' + urlencode(dict((field, self.cleaned_data.get(field)) for field in fields))


class EditForm(object):
    __metaclass__ = ABCMeta

    class UserForm(forms.ModelForm):
        first_name = forms.CharField(
            widget=forms.TextInput(attrs={'placeholder': _('first name')}),
            max_length=30)
        last_name = forms.CharField(
            widget=forms.TextInput(attrs={'placeholder': _('last name')}),
            max_length=30)
        password1 = forms.CharField(
            label=_('password'),
            widget=forms.PasswordInput(attrs={'placeholder': _('password')}))
        password2 = forms.CharField(
            label=_('password confirmation'),
            widget=forms.PasswordInput(attrs={'placeholder': _('password confirmation')}))

        error_messages = {
            'password_mismatch': _(
                "The two password fields didn't match."),
            'duplicated_email': _(
                "This e-mail address is already in use."),
        }

        def __init__(self, permissions=[], *args, **kwargs):
            super(EditForm.UserForm, self).__init__(*args, **kwargs)
            self.fields['email'].required = True
            self.fields['permissions'] = forms.MultipleChoiceField(
                required=False,
                widget=CheckboxSelectMultiple,
                initial=list(set(permissions) & set(PERMISSIONS.keys())),
                choices=[
                    (permission, Permission.objects.get(codename=permission).name)
                    for permission in PERMISSIONS.keys()
                ])

        def clean_password2(self):
            password1 = self.cleaned_data.get('password1')
            password2 = self.cleaned_data.get('password2')
            if password1 and password2 and password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'])
            return password2

        class Meta:
            model = User
            fields = ('email', 'first_name', 'last_name',)

    class ProfileForm(forms.ModelForm):
        class Meta:
            model = UserProfile
            fields = ('photo',)

    def __init__(self, user, permissions, profile, data, files):
        self.user = self.UserForm(permissions=permissions, prefix='user', instance=user, data=data)
        self.profile = self.ProfileForm(prefix='profile', instance=profile, data=data, files=files)

    def is_valid(self):
        return self.user.is_valid() and self.profile.is_valid()


class AddForm(EditForm):
    class UserForm(EditForm.UserForm):
        def clean_email(self):
            email = self.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(self.error_messages['duplicated_email'])
            return email

        def save(self, commit=True):
            # Add user instance.
            user = super(AddForm.UserForm, self).save(commit=False)
            user.username = ''.join([choice(letters) for i in xrange(30)])
            user.set_password(self.cleaned_data.get('password1'))
            user.save()
            # Set user permissions.
            user.user_permissions = [
                Permission.objects.get(codename=permission)
                for permission in self.cleaned_data.get('permissions')
            ]
            user.save()
            # Done!
            return user

    class ProfileForm(EditForm.ProfileForm):
        def save(self, commit=True):
            pass

    def __init__(self, user, data=None, files=None):
        self.creator = user
        super(AddForm, self).__init__(user=User(), permissions=[], profile=UserProfile(), data=data, files=files)

    def save(self):
        user = self.user.save()
        profile = user.get_profile()
        profile.creator = self.creator
        profile.photo = self.profile.cleaned_data.get('photo')
        profile.save()


class UpdateForm(EditForm):
    class UserForm(EditForm.UserForm):
        def clean_email(self):
            email = self.cleaned_data.get('email')
            if User.objects.filter(email=email).exclude(id=self.instance.id).exists():
                raise forms.ValidationError(self.error_messages['duplicated_email'])
            return email

        def __init__(self, permissions=[], *args, **kwargs):
            super(UpdateForm.UserForm, self).__init__(permissions=permissions, *args, **kwargs)
            self.fields['password1'].required = False
            self.fields['password2'].required = False

        def save(self, commit=True):
            user = super(UpdateForm.UserForm, self).save(commit=False)
            if self.cleaned_data.get('password1') and self.cleaned_data.get('password2'):
                user.set_password(self.cleaned_data.get('password1'))
            # Update permissions.
            permissions = set(user.user_permissions.all())
            for permission in Permission.objects.filter(codename__in=PERMISSIONS.keys()):
                if permission.codename in self.cleaned_data.get('permissions'):
                    permissions.add(permission)
                else:
                    permissions.discard(permission)
            user.user_permissions = list(permissions)
            # Save.
            user.save()
            # Done!
            return user

    class ProfileForm(EditForm.ProfileForm):
        class Meta(EditForm.ProfileForm.Meta):
            fields = EditForm.ProfileForm.Meta.fields + ('revision',)

    def __init__(self, instance, data=None, files=None):
        permissions = instance.user_permissions.all().values_list('codename', flat=True)
        super(UpdateForm, self).__init__(user=instance, permissions=permissions, profile=instance.get_profile(), data=data, files=files)

    def save(self):
        # Save in a transaction as concurrent edition of the profile may raise an exception.
        with transaction.commit_on_success():
            self.user.save()
            self.profile.save()
