# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from varnish_bans_manager.core.models import Group
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.views.caches.base import Base


class Reorder(Base):
    def post(self, request):
        ids = [int(id) for id in request.POST.getlist('ids')]
        for group in Group.objects.all():
            try:
                group.weight = ids.index(group.id)
            except ValueError:
                group.weight = 0
            group.save()
        return HttpResponseAjax()
