# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.utils import timezone
from varnish_bans_manager.core.tasks.base import MonitoredTask
from varnish_bans_manager.core.models import BanSubmissionItem


class Submit(MonitoredTask):
    def irun(self, ban_submission):
        ban_submission.launched_at = timezone.now()
        ban_submission.save()
        num_items = len(ban_submission.target.items)
        for index, node in enumerate(ban_submission.target.items):
            # Build ban submission item with the result of the
            # current operation.
            ban_submission_item = BanSubmissionItem(node=node)
            try:
                node.ban(ban_submission.expression)
                ban_submission_item.success = True
            except Exception as e:
                ban_submission_item.success = False
                ban_submission_item.message = str(e)
            # Save ban submission item and update progress.
            ban_submission.items.add(ban_submission_item)
            self.set_progress(index + 1, num_items)
        return ban_submission.id
