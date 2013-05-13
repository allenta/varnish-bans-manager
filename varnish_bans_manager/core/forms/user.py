# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django import forms
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.http import int_to_base36
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import UNUSABLE_PASSWORD
from templated_email import send_templated_mail
from django.contrib.auth.tokens import default_token_generator
from varnish_bans_manager.core.models import User, UserProfile


class LoginForm(forms.Form):
    email = forms.EmailField(
        label=_('e-mail address'),
        widget=forms.TextInput(attrs={'placeholder': _('e-mail address')}),
        max_length=64)
    password = forms.CharField(
        label=_('password'),
        widget=forms.PasswordInput(attrs={'placeholder': _('password')}))
    destination = forms.CharField(
        widget=forms.HiddenInput())

    error_messages = {
        'invalid_login': _(
            "Please enter a correct e-mail and password. "
            "Note that both fields are case-sensitive."),
        'inactive': _(
            "This account is inactive."),
    }

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user = authenticate(email=email, password=password)
            if self.user is None:
                raise forms.ValidationError(self.error_messages['invalid_login'])
            elif not self.user.is_active:
                raise forms.ValidationError(self.error_messages['inactive'])
        return self.cleaned_data


class PasswordResetForm(forms.Form):
    email = forms.EmailField(
        label=_('e-mail address'),
        widget=forms.TextInput(attrs={'placeholder': _('e-mail address')}),
        max_length=64)

    error_messages = {
        'unknown': _(
            "That e-mail address doesn't have an associated "
            "user account. Are you sure you've registered?"),
        'unusable': _(
            "The user account associated with this e-mail "
            "address cannot reset the password."),
    }

    def __init__(self, *args, **kwargs):
        super(PasswordResetForm, self).__init__(*args, **kwargs)
        self.user = None

    def clean_email(self):
        """
        Validates that an active user exists with the given email address.
        """
        email = self.cleaned_data.get('email')
        try:
            self.user = User.objects.filter(email__iexact=email, is_active=True).order_by('date_joined')[:1].get()
            if self.user.password == UNUSABLE_PASSWORD:
                raise forms.ValidationError(self.error_messages['unusable'])
            else:
                return email
        except User.DoesNotExist:
            raise forms.ValidationError(self.error_messages['unknown'])

    def save(self, request):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        host = request.get_host()
        send_templated_mail(
            template_name='varnish-bans-manager/core/user/password_reset',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.user.email],
            bcc=settings.DEFAULT_BCC_EMAILS,
            context={
                'name': self.user.first_name or self.user.email,
                'base_url': "http://%s" % host,
                'reset_url':
                    (settings.HTTPS_ENABLED and 'https' or 'http') + '://' +
                    host +
                    reverse('user-password-reset-confirm', kwargs={
                        'uidb36': int_to_base36(self.user.id),
                        'token': default_token_generator.make_token(self.user),
                    }),
            },
        )


class PasswordResetConfirmationForm(forms.Form):
    new_password1 = forms.CharField(
        label=_('new password'),
        widget=forms.PasswordInput(attrs={'placeholder': _('new password')}))
    new_password2 = forms.CharField(
        label=_('new password confirmation'),
        widget=forms.PasswordInput(attrs={'placeholder': _('new password confirmation')}))

    error_messages = {
        'password_mismatch': _(
            "The two password fields didn't match."),
    }

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(PasswordResetConfirmationForm, self).__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'])
        return password2

    def save(self):
        self.user.set_password(self.cleaned_data.get('new_password1'))
        self.user.save()


class ProfilePreferencesForm():
    class UserForm(forms.ModelForm):
        first_name = forms.CharField(
            widget=forms.TextInput(attrs={'placeholder': _('first name')}),
            max_length=30)
        last_name = forms.CharField(
            widget=forms.TextInput(attrs={'placeholder': _('last name')}),
            max_length=30)

        class Meta:
            model = User
            fields = ('first_name', 'last_name')

    class ProfileForm(forms.ModelForm):
        class Meta:
            model = UserProfile
            exclude = ('secret', 'user', 'creator', 'revision')

    def __init__(self, user, data=None, files=None):
        self.user = self.UserForm(prefix='user', instance=user, data=data)
        self.profile = self.ProfileForm(prefix='profile', instance=user.profile, data=data, files=files)

    def is_valid(self):
        return self.user.is_valid() and self.profile.is_valid()

    def save(self):
        self.user.save()
        self.profile.save()


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label=_('Old password'),
        widget=forms.PasswordInput(attrs={'placeholder': _('current password')}))
    new_password1 = forms.CharField(
        label=_('New password'),
        widget=forms.PasswordInput(attrs={'placeholder': _('new password')}))
    new_password2 = forms.CharField(
        label=_('New password confirmation'),
        widget=forms.PasswordInput(attrs={'placeholder': _('confirm new password')}))

    error_messages = {
        'password_incorrect': _(
            "Your old password was entered incorrectly. "
            "Please enter it again."),
        'password_mismatch': _(
            "The two password fields didn't match."),
    }

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(PasswordChangeForm, self).__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'])
        return old_password

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'])
        return password2

    def save(self):
        self.user.set_password(self.cleaned_data.get('new_password1'))
        self.user.save()
