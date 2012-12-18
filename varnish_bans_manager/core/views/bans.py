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
from django.http import HttpResponseForbidden
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.utils.translation import ungettext, ugettext as _
from django.views.generic import View
from varnish_bans_manager.core import tasks
from varnish_bans_manager.core.helpers import commands, DEFAULT_FORM_ERROR_MESSAGE
from varnish_bans_manager.core.helpers.views import ajaxify
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.forms.bans import BasicForm, AdvancedForm, ExpertForm
from varnish_bans_manager.core.tasks.bans import Submit as SubmitTask


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
        return self._render(form=self._form())

    def post(self, request):
        form = self._form(data=request.POST)
        if form.is_valid():
            token = tasks.enqueue(
                request,
                SubmitTask(),
                form.expression,
                [cache.id for cache in form.cleaned_data.get('target')],
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

    def _form(self, *args, **kwargs):
        raise NotImplementedError('Please implement this method')

    @classmethod
    def callback(cls, request, result, context):
        destination = reverse(context['destination'])
        if result['errors']:
            return [
                commands.modal('varnish-bans-manager/core/bans/submit_errors.html', {
                    'expression': context['expression'],
                    'submissions': result['submissions'],
                    'misses': result['misses'],
                    'errors': result['errors'],
                    'destination': destination,
                }, context_instance=RequestContext(request))
            ]
        else:
            messages.success(request, ungettext(
                'Your ban has been successfully submitted to %(count)d cache.',
                'Your ban has been successfully submitted to %(count)d caches.',
                result['submissions']) % {'count': result['submissions']})
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
        return {'template': 'varnish-bans-manager/core/bans/submissions.html', 'context': {}}


class Status(Base):
    @method_decorator(permission_required('core.can_access_bans_status'))
    def dispatch(self, *args, **kwargs):
        return super(Status, self).dispatch(*args, **kwargs)

    def get(self, request):
        return {'template': 'varnish-bans-manager/core/bans/status.html', 'context': {}}
