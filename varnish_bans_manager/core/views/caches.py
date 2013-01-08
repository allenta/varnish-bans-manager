# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from abc import ABCMeta
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from varnish_bans_manager.core.models import Group, Node
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.helpers.views import ajaxify


class Base(View):
    __metaclass__ = ABCMeta

    @method_decorator(login_required)
    @method_decorator(permission_required('core.can_access_caches_management'))
    @method_decorator(ajaxify)
    def dispatch(self, *args, **kwargs):
        return super(Base, self).dispatch(*args, **kwargs)


class Browse(Base):
    def get(self, request):
        orphan_nodes_group = Group(name=_('Individual cache nodes'), weight=0)
        orphan_nodes = Node.objects.filter(group__isnull=True).order_by('weight', 'created_at')
        caches = [(orphan_nodes_group, orphan_nodes)]
        groups = Group.objects.all().order_by('weight', 'created_at')
        caches.extend((group, group.nodes.all().order_by('weight', 'created_at')) for group in groups)
        return {'template': 'varnish-bans-manager/core/caches/browse.html', 'context': {
            'caches': caches,
        }}


class GroupsReorder(Base):
    def post(self, request):
        ids = [int(id) for id in request.POST.getlist('ids')]
        for group in Group.objects.all():
            try:
                group.weight = ids.index(group.id)
            except ValueError:
                group.weight = 0
            group.save()
        return HttpResponseAjax()
