# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from varnish_bans_manager.core.models import Node
from varnish_bans_manager.core.tasks.base import MonitoredTask


class Submit(MonitoredTask):
    def irun(self, type, expression, node_ids):
        submissions = 0
        misses = 0
        errors = []
        for index, node_id in enumerate(node_ids):
            try:
                node = Node.objects.get(pk=node_id)
                try:
                    node.ban(expression)
                    submissions = submissions + 1
                except Exception as e:
                    errors.append({
                        'id': node.id,
                        'name': node.human_name,
                        'message': str(e),
                    })
            except Node.DoesNotExist:
                misses += 1
            self.set_progress(index + 1, len(node_ids))
        return {
            'submissions': submissions,
            'misses': misses,
            'errors': errors
        }
