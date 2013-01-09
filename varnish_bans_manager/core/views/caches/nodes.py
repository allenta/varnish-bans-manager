# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from varnish_bans_manager.core.models import Node
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.views.caches.base import Base


class Reorder(Base):
    def post(self, request):
        group_id = int(request.POST.get('group_id')) if request.POST.get('group_id') else None
        node_ids = [int(id) for id in request.POST.getlist('node_ids')]
        for node in Node.objects.filter(group_id=group_id):
            try:
                node.weight = node_ids.index(node.id)
            except ValueError:
                node.weight = 0
            node.save()
        return HttpResponseAjax()
