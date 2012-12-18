# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from varnish_bans_manager.core.models import Cache
from varnish_bans_manager.core.tasks.base import MonitoredTask


class Submit(MonitoredTask):
    def irun(self, expression, cache_ids):
        submissions = 0
        misses = 0
        errors = []
        for index, cache_id in enumerate(cache_ids):
            try:
                cache = Cache.objects.get(pk=cache_id)
                try:
                    cache.ban(expression)
                    submissions = submissions + 1
                except Exception as e:
                    errors.append({
                        'id': cache.id,
                        'name': cache.human_name,
                        'message': str(e),
                    })
            except Cache.DoesNotExist:
                misses += 1
            self.set_progress(index + 1, len(cache_ids))
        return {
            'submissions': submissions,
            'misses': misses,
            'errors': errors
        }
