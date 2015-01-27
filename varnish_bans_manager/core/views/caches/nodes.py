# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from abc import ABCMeta
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.core.models import Group, Node
from varnish_bans_manager.core.helpers import commands
from varnish_bans_manager.core.helpers import DEFAULT_SUCCESS_MESSAGE, DEFAULT_ERROR_MESSAGE, DEFAULT_FORM_ERROR_MESSAGE
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.forms.caches.nodes import AddForm, UpdateForm
from varnish_bans_manager.core.views.caches.base import Base as CachesBase


class Base(CachesBase):
    __metaclass__ = ABCMeta

    def _process_kwargs(self, kwargs):
        kwargs = super(Base, self)._process_kwargs(kwargs)
        if 'id' in kwargs:
            kwargs['node'] = get_object_or_404(Node, id=kwargs.pop('id'))
        return kwargs

    def _fill_context(self, context, kwargs):
        context = super(Base, self)._fill_context(context, kwargs)
        context['node'] = kwargs.get('node', None)
        return context


class Add(Base):
    def get(self, request):
        form = AddForm(initial={'group': request.GET.get('group', None)})
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
        return {
            'template': 'varnish-bans-manager/core/caches/nodes/add.html',
            'context': {
                'form': form,
            }
        }


class Update(Base):
    def get(self, request, node):
        form = UpdateForm(instance=node)
        return self._render(form)

    def post(self, request, node):
        form = UpdateForm(data=request.POST, instance=node)
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
        return {
            'template': 'varnish-bans-manager/core/caches/nodes/update.html',
            'context': {
                'form': form,
            }
        }


class Delete(Base):
    def post(self, request, node):
        try:
            node.delete()
            messages.success(request, _('The node has been deleted.'))
        except:
            messages.error(request, DEFAULT_ERROR_MESSAGE)
        return HttpResponseAjax([
            commands.navigate(reverse('caches-browse')),
        ], request)


class Reorder(Base):
    def post(self, request):
        node_ids = [int(id) for id in request.POST.getlist('node_ids')]
        print node_ids
        # Rearrange all nodes in the group following
        # the order set by node_ids.
        if request.POST.get('group_id'):
            group = Group.objects.get(pk=int(request.POST.get('group_id')))
            nodes_in_group = group.nodes.all()
        else:
            group = None
            nodes_in_group = Node.objects.filter(group_id__isnull=True)
        for node in nodes_in_group:
            try:
                node.weight = node_ids.index(node.id) + 1
            except ValueError:
                node.weight = 0
            node.save()
        # Add to the group any other given node that was not yet on it.
        node_ids_in_group = [node.id for node in nodes_in_group]
        print node_ids_in_group
        for node_id in node_ids:
            if node_id not in node_ids_in_group:
                node = Node.objects.get(pk=node_id)
                node.group = group
                node.weight = node_ids.index(node.id) + 1
                node.save()
        return HttpResponseAjax()
