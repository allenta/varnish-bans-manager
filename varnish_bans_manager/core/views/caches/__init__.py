# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from varnish_bans_manager.core.models import Group, Node
from varnish_bans_manager.core.views.caches.base import Base


class Browse(Base):
    def get(self, request):
        orphan_nodes_group = Group(weight=0)
        orphan_nodes = Node.objects.filter(group__isnull=True).order_by('weight', 'created_at')
        caches = [(orphan_nodes_group, orphan_nodes)]
        groups = Group.objects.all().order_by('weight', 'created_at')
        caches.extend((group, group.nodes.all().order_by('weight', 'created_at')) for group in groups)
        return {'template': 'varnish-bans-manager/core/caches/browse.html', 'context': {
            'caches': caches,
        }}
