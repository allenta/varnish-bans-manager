# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from abc import ABCMeta
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.core.exceptions import SuspiciousOperation
from django.utils.decorators import method_decorator
from django.utils.translation import ungettext, ugettext as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.views.generic import View
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.helpers.views import ajaxify
from varnish_bans_manager.core.helpers import commands
from varnish_bans_manager.core.forms.users import BrowseForm, BulkForm, AddForm, UpdateForm
from varnish_bans_manager.core.helpers import DEFAULT_SUCCESS_MESSAGE, DEFAULT_ERROR_MESSAGE, DEFAULT_FORM_ERROR_MESSAGE
from varnish_bans_manager.core import tasks
from varnish_bans_manager.core.tasks.users import Delete as DeleteTask
from varnish_bans_manager.core.tasks.users import DownloadCSV as DownloadCSVTask


class Base(View):
    __metaclass__ = ABCMeta

    @method_decorator(login_required)
    @method_decorator(permission_required('core.can_access_users_management'))
    @method_decorator(ajaxify)
    def dispatch(self, *args, **kwargs):
        if 'id' in kwargs:
            user = get_object_or_404(User, id=kwargs['id'], is_active=True)
            del kwargs['id']
            kwargs['user'] = user
        return super(Base, self).dispatch(*args, **kwargs)


class Browse(Base):
    def get(self, request):
        form = BrowseForm(data=request.GET)
        if form.is_valid():
            form.execute()
            return {'template': 'varnish-bans-manager/core/users/browse.html', 'context': {
                'form': form,
            }}
        else:
            raise SuspiciousOperation()


class Bulk(Base):
    def post(self, request):
        form = BulkForm(data=request.POST)
        if form.is_valid():
            form.execute()
            method = getattr(self, '_%s' % form.cleaned_data.get('op'))
            return method(request, form)
        else:
            raise SuspiciousOperation()

    def _delete(self, request, form):
        return self._launch_task(
            request, form,
            DeleteTask(), _('Removing users...'),
            form.get_url(reset_page=True))

    def _download_csv(self, request, form):
        return self._launch_task(
            request, form,
            DownloadCSVTask(), _('Generating CSV...'),
            None)

    def _launch_task(self, request, form, task, title, destination):
        token = tasks.enqueue(
            request, task, form.ids,
            callback={
                'fn': ('varnish_bans_manager.core.views.users.Bulk', '%s_callback' % form.cleaned_data.get('op')),
                'context': {
                    'destination': destination,
                }
            }
        )
        return HttpResponseAjax([
            commands.show_progress(token, title=title),
        ], request)

    @classmethod
    def delete_callback(cls, request, result, context):
        if result['errors'] == 0:
            messages.success(request, ungettext(
                '%(count)d user has been successfully deleted.',
                '%(count)d users have been successfully deleted.',
                result['deleted']) % {'count': result['deleted']})
        else:
            messages.error(request, ungettext(
                'Failed to delete %(count)d user.',
                'Failed to delete %(count)d users.',
                result['errors']) % {'count': result['errors']})
        return [
            commands.navigate(context['destination']),
        ]

    @classmethod
    def download_csv_callback(cls, request, result, context):
        instructions = _("You should now see a popup window that asks where to save the exported file in your computer. If not, you can download it manually by simply clicking <a href=\"%(url)s\" target=\"_blank\">this link</a>.") % {
            'url': result['url'],
        }
        if result['errors'] == 0:
            messages.success(request, (ungettext(
                '%(count)d user has been successfully exported.',
                '%(count)d users have been successfully exported.',
                result['exported']) % {'count': result['exported']}) + ' ' + instructions)
        else:
            messages.error(request, (ungettext(
                'Failed to export %(count)d user.',
                'Failed to export %(count)d users.',
                result['errors']) % {'count': result['errors']}) + ' ' + instructions)
        return [
            commands.redirect(result['url']),
        ]


class Add(Base):
    def get(self, request):
        form = AddForm(request.user)
        return self.__render(form)

    def post(self, request):
        form = AddForm(request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, DEFAULT_SUCCESS_MESSAGE)
            return HttpResponseAjax([
                commands.navigate(reverse('users-browse')),
            ], request)
        else:
            messages.error(request, DEFAULT_FORM_ERROR_MESSAGE)
            return self.__render(form)

    def __render(self, form):
        return {'template': 'varnish-bans-manager/core/users/add.html', 'context': {
            'form': form,
        }}


class Update(Base):
    def get(self, request, user):
        form = UpdateForm(user)
        return self._render(form, user)

    def post(self, request, user):
        form = UpdateForm(user, data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, DEFAULT_SUCCESS_MESSAGE)
            return HttpResponseAjax([
                commands.navigate(reverse('users-browse')),
            ], request)
        else:
            messages.error(request, DEFAULT_FORM_ERROR_MESSAGE)
            return self._render(form, user)

    def _render(self, form, user):
        return {'template': 'varnish-bans-manager/core/users/update.html', 'context': {
            'form': form,
            'instance': user,
        }}


class Delete(Base):
    def post(self, request, user):
        token = tasks.enqueue(
            request, DeleteTask(), [user.id],
            callback={
                'fn': ('varnish_bans_manager.core.views.users.Delete', 'callback'),
                'context': {
                    'destination': reverse('users-browse'),
                }
            }
        )
        return HttpResponseAjax([
            commands.show_progress(token, title=_('Removing user...')),
        ], request)

    @classmethod
    def callback(cls, request, result, context):
        if result['deleted'] == 1:
            messages.success(request, _('The user has been successfully deleted.'))
        else:
            messages.error(request, DEFAULT_ERROR_MESSAGE)
        return [
            commands.navigate(context['destination']),
        ]
