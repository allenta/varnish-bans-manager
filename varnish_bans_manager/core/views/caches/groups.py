# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.contrib import messages
from django.core.urlresolvers import reverse
from varnish_bans_manager.core.models import Group
from varnish_bans_manager.core.helpers import commands
from varnish_bans_manager.core.helpers import DEFAULT_SUCCESS_MESSAGE, DEFAULT_FORM_ERROR_MESSAGE
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.forms.caches.groups import AddForm
from varnish_bans_manager.core.views.caches.base import Base


class Add(Base):
    def get(self, request):
        form = AddForm()
        return self._render(form)

    def post(self, request):
        form = AddForm(data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, DEFAULT_SUCCESS_MESSAGE)
            return HttpResponseAjax([
                commands.navigate(reverse('caches-browse')),
            ], request)
        else:
            messages.error(request, DEFAULT_FORM_ERROR_MESSAGE)
            return self._render(form)

    def _render(self, form):
        return {'template': 'varnish-bans-manager/core/caches/groups/add.html', 'context': {
            'form': form,
        }}


class Reorder(Base):
    def post(self, request):
        ids = [int(id) for id in request.POST.getlist('ids')]
        for group in Group.objects.all():
            try:
                group.weight = ids.index(group.id) + 1
            except ValueError:
                group.weight = 0
            group.save()
        return HttpResponseAjax()
