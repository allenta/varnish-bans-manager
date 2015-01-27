# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import urlparse
from abc import ABCMeta
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.http import base36_to_int
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.generic import View
from varnish_bans_manager.core.helpers import commands, DEFAULT_SUCCESS_MESSAGE, DEFAULT_FORM_ERROR_MESSAGE
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.helpers.views import ajaxify
from varnish_bans_manager.core.forms.user import LoginForm, PasswordResetForm, PasswordResetConfirmationForm, ProfilePreferencesForm, PasswordChangeForm
from varnish_bans_manager.core.models import User


class Base(View):
    __metaclass__ = ABCMeta

    @method_decorator(ajaxify)
    def dispatch(self, *args, **kwargs):
        return super(Base, self).dispatch(*args, **kwargs)


class AnonymousBase(Base):
    __metaclass__ = ABCMeta

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return super(AnonymousBase, self).dispatch(
                request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('home'))


class AuthenticatedBase(Base):
    __metaclass__ = ABCMeta

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AuthenticatedBase, self).dispatch(
            request, *args, **kwargs)


class Login(AnonymousBase):
    def get(self, request):
        # Destination?
        destination = request.GET.get(
            auth.REDIRECT_FIELD_NAME, reverse('home'))

        # Don't allow redirection to a different host.
        netloc = urlparse.urlparse(destination)[1]
        if netloc and netloc != request.get_host():
            destination = reverse('home')

        # Done!
        form = LoginForm(initial={'destination': destination})
        return self._render(form)

    def post(self, request):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            # Log user in.
            auth.login(request, form.user)

            # Done!
            messages.info(request, _('Welcome back!'))
            return HttpResponseAjax([
                commands.redirect(form.cleaned_data.get('destination')),
            ], request)
        else:
            return self._render(form)

    def _render(self, form):
        return {
            'template': 'varnish-bans-manager/core/user/login.html',
            'context': {
                'form': form,
            },
        }


class Logout(Base):
    def get(self, request):
        auth.logout(request)
        messages.success(request, _(
            'You have been disconnected. See you soon!'))
        return HttpResponseRedirect(reverse('index'))


class PasswordReset(AnonymousBase):
    def get(self, request):
        form = PasswordResetForm()
        return self._render(form)

    def post(self, request):
        form = PasswordResetForm(data=request.POST)
        if form.is_valid():
            # Save.
            form.save(request)

            # Done!
            messages.success(request, _(
                'An e-mail with password reset instructions has been '
                'delivered to %(email)s. Please, check your inbox and '
                'follow the instructions.') % {
                    'email': form.user.email
                })
            return HttpResponseAjax([
                commands.navigate(reverse('user-login')),
            ], request)
        else:
            return self._render(form)

    def _render(self, form):
        return {
            'template': 'varnish-bans-manager/core/user/password_reset.html',
            'context': {
                'form': form,
            },
        }


class PasswordResetConfirm(AnonymousBase):
    def dispatch(self, request, uidb36=None, token=None, *args, **kwargs):
        # Check input.
        assert uidb36 is not None and token is not None

        # Fetch user.
        try:
            uid_int = base36_to_int(uidb36)
            user = User.objects.get(id=uid_int)
        except (ValueError, User.DoesNotExist):
            user = None

        # Valid link?
        if user is not None and \
           default_token_generator.check_token(user, token):
            kwargs['user'] = user
            return super(PasswordResetConfirm, self).dispatch(
                request, *args, **kwargs)
        else:
            messages.error(request, _(
                'The password reset link is not valid anymore. Please, '
                'request a new one.'))
            return HttpResponseRedirect(reverse('user-password-reset'))

    def get(self, request, user):
        form = PasswordResetConfirmationForm(user)
        return self._render(form, request)

    def post(self, request, user):
        form = PasswordResetConfirmationForm(user, data=request.POST)
        if form.is_valid():
            # Save.
            form.save()

            # Done!
            messages.success(request, _('Your password has been updated.'))
            return HttpResponseAjax([
                commands.navigate(reverse('user-login')),
            ], request)
        else:
            return self._render(form, request)

    def _render(self, form, request):
        return {
            'template':
                'varnish-bans-manager/core/user/password_reset_confirm.html',
            'context': {
                'form': form,
                'url': request.path,
            },
        }


class Profile(AuthenticatedBase):
    def get(self, request):
        form = ProfilePreferencesForm(request.user)
        return self._render(form)

    def post(self, request):
        form = ProfilePreferencesForm(
            request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, DEFAULT_SUCCESS_MESSAGE)
            return HttpResponseAjax([
                commands.reload(request),
            ], request)
        else:
            messages.error(request, DEFAULT_FORM_ERROR_MESSAGE)
            return self._render(form)

    def _render(self, form):
        return {
            'template': 'varnish-bans-manager/core/user/profile.html',
            'context': {
                'form': form,
            },
        }


class Password(AuthenticatedBase):
    def get(self, request):
        form = PasswordChangeForm(request.user)
        return self._render(form)

    def post(self, request):
        form = PasswordChangeForm(request.user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Your password has been updated.'))
            return HttpResponseAjax([
                commands.reload(request),
            ], request)
        else:
            messages.error(request, DEFAULT_FORM_ERROR_MESSAGE)
            return self._render(form)

    def _render(self, form):
        return {
            'template': 'varnish-bans-manager/core/user/password.html',
            'context': {
                'form': form,
            },
        }
