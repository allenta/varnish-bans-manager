# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from abc import ABCMeta
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.core.models import Group
from varnish_bans_manager.core.helpers import commands
from varnish_bans_manager.core.helpers import DEFAULT_SUCCESS_MESSAGE, DEFAULT_ERROR_MESSAGE, DEFAULT_FORM_ERROR_MESSAGE
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.forms.caches.groups import AddForm, UpdateForm
from varnish_bans_manager.core.views.caches.base import Base as CachesBase


class Base(CachesBase):
    __metaclass__ = ABCMeta

    def _process_kwargs(self, kwargs):
        kwargs = super(Base, self)._process_kwargs(kwargs)
        if 'id' in kwargs:
            kwargs['group'] = get_object_or_404(Group, id=kwargs.pop('id'))
        return kwargs

    def _fill_context(self, context, kwargs):
        context = super(Base, self)._fill_context(context, kwargs)
        context['group'] = kwargs.get('group', None)
        return context


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


class Update(Base):
    def get(self, request, group):
        form = UpdateForm(instance=group)
        return self._render(form)

    def post(self, request, group):
        form = UpdateForm(data=request.POST, instance=group)
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
        return {'template': 'varnish-bans-manager/core/caches/groups/update.html', 'context': {
            'form': form,
        }}


class Delete(Base):
    def post(self, request, group):
        try:
            group.delete()
            messages.success(request, _('The group has been successfully deleted. Its nodes are no longer assigned to any group.'))
        except:
            messages.error(request, DEFAULT_ERROR_MESSAGE)
        return HttpResponseAjax([
            commands.navigate(reverse('caches-browse')),
        ], request)


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
