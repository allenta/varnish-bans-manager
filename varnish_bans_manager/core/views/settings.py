# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from abc import ABCMeta
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.helpers.views import ajaxify
from varnish_bans_manager.core.helpers import DEFAULT_SUCCESS_MESSAGE, DEFAULT_FORM_ERROR_MESSAGE
from varnish_bans_manager.core.forms.settings import GeneralForm
from varnish_bans_manager.core.helpers import commands


class Base(View):
    __metaclass__ = ABCMeta

    @method_decorator(login_required)
    @method_decorator(permission_required('core.can_access_settings'))
    @method_decorator(ajaxify)
    def dispatch(self, *args, **kwargs):
        return super(Base, self).dispatch(*args, **kwargs)


class General(Base):
    def get(self, request):
        form = GeneralForm()
        return self._render(form=form)

    def post(self, request):
        form = GeneralForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, DEFAULT_SUCCESS_MESSAGE)
            return HttpResponseAjax([
                commands.navigate(reverse('settings-general')),
            ], request)
        else:
            messages.error(request, DEFAULT_FORM_ERROR_MESSAGE)
            return self._render(form=form)

    def _render(self, form=None):
        return {'template': 'varnish-bans-manager/core/settings/general.html', 'context': {
            'form': form,
        }}
