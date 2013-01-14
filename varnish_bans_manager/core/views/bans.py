# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from abc import ABCMeta
from django.core.exceptions import SuspiciousOperation
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import ungettext, ugettext as _
from django.views.generic import View
from varnish_bans_manager.core import tasks
from varnish_bans_manager.core.helpers import commands, DEFAULT_FORM_ERROR_MESSAGE
from varnish_bans_manager.core.helpers.views import ajaxify
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.forms.bans import BasicForm, AdvancedForm, ExpertForm, SubmissionsForm, StatusForm
from varnish_bans_manager.core.models import BanSubmission
from varnish_bans_manager.core.tasks.bans import Submit as SubmitTask
from varnish_bans_manager.core.tasks.bans import Status as StatusTask


class Base(View):
    __metaclass__ = ABCMeta

    @method_decorator(login_required)
    @method_decorator(ajaxify)
    def dispatch(self, *args, **kwargs):
        return super(Base, self).dispatch(*args, **kwargs)


class Submit(Base):
    __metaclass__ = ABCMeta

    def dispatch(self, request, *args, **kwargs):
        if self.permission is None or request.user.has_perm(self.permission):
            return super(Submit, self).dispatch(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    def get(self, request):
        return self._render(form=self._form(request.user))

    def post(self, request):
        form = self._form(request.user, data=request.POST)
        if form.is_valid():
            token = tasks.enqueue(
                request,
                SubmitTask(),
                form.ban_submission,
                callback={
                    'fn': ('varnish_bans_manager.core.views.bans.Submit', 'callback'),
                    'context': {
                        'expression': form.expression,
                        'destination': self.destination,
                    }
                }
            )
            return HttpResponseAjax([
                commands.show_progress(token, title=_('Submitting ban...')),
            ], request)
        else:
            messages.error(request, DEFAULT_FORM_ERROR_MESSAGE)
            return self._render(form=form)

    def _render(self, **kwargs):
        return {'template': self.template, 'context': kwargs}

    def _form(self, user, *args, **kwargs):
        raise NotImplementedError('Please implement this method')

    @classmethod
    def callback(cls, request, result, context):
        destination = reverse(context['destination'])
        ban_submission = BanSubmission.objects.get(pk=result)
        ban_submission_items = ban_submission.items.all()
        successful_items_count = len([item for item in ban_submission_items if item.success])
        if successful_items_count < len(ban_submission_items):
            return [
                commands.modal('varnish-bans-manager/core/bans/submit_errors.html', {
                    'expression': ban_submission.expression,
                    'submissions': successful_items_count,
                    'errors': [item for item in ban_submission_items if not item.success],
                    'destination': destination,
                }, context_instance=RequestContext(request))
            ]
        else:
            messages.success(request, ungettext(
                'Your ban has been successfully submitted to %(count)d cache.',
                'Your ban has been successfully submitted to %(count)d caches.',
                successful_items_count) % {'count': successful_items_count})
            return [
                commands.navigate(destination),
            ]


class Basic(Submit):
    permission = None
    template = 'varnish-bans-manager/core/bans/basic.html'
    destination = 'bans-basic'

    def _form(self, *args, **kwargs):
        return BasicForm(*args, **kwargs)


class Advanced(Submit):
    permission = 'core.can_access_advanced_ban_submission'
    template = 'varnish-bans-manager/core/bans/advanced.html'
    destination = 'bans-advanced'

    def _form(self, *args, **kwargs):
        return AdvancedForm(*args, **kwargs)


class Expert(Submit):
    permission = 'core.can_access_expert_ban_submission'
    template = 'varnish-bans-manager/core/bans/expert.html'
    destination = 'bans-expert'

    def _form(self, *args, **kwargs):
        return ExpertForm(*args, **kwargs)


class Submissions(Base):
    @method_decorator(permission_required('core.can_access_bans_submissions'))
    def dispatch(self, *args, **kwargs):
        return super(Submissions, self).dispatch(*args, **kwargs)

    def get(self, request):
        form = SubmissionsForm(data=request.GET)
        if form.is_valid():
            form.execute()
            return {'template': 'varnish-bans-manager/core/bans/submissions.html', 'context': {
                'form': form,
            }}
        else:
            raise SuspiciousOperation()


class Status(Base):
    @method_decorator(permission_required('core.can_access_bans_status'))
    def dispatch(self, *args, **kwargs):
        return super(Status, self).dispatch(*args, **kwargs)

    def get(self, request):
        return self._render(form=StatusForm())

    def post(self, request):
        form = StatusForm(data=request.POST)
        if form.is_valid():
            token = tasks.enqueue(
                request,
                StatusTask(),
                form.cleaned_data.get('cache'),
                callback={
                    'fn': ('varnish_bans_manager.core.views.bans.Status', 'callback'),
                    'context': {},
                }
            )
            return HttpResponseAjax([
                commands.show_progress(token, title=_('Fetching lists of bans...')),
            ], request)
        else:
            messages.error(request, DEFAULT_FORM_ERROR_MESSAGE)
            return self._render(form=form)

    def _render(self, form):
        return {'template': 'varnish-bans-manager/core/bans/status.html', 'context': {
            'form': form,
            'cache': None,
            'bans': None,
        }}

    @classmethod
    def callback(cls, request, result, context):
        return [
            commands.set_content(render_to_string(
                'varnish-bans-manager/core/bans/status.html', {
                    'form': StatusForm(cache=result['cache']),
                    'cache': result['cache'],
                    'bans': result['bans'],
                },
                context_instance=RequestContext(request)))
        ]
