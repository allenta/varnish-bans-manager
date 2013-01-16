# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.conf import settings
from django.utils import timezone
from templated_email import send_templated_mail
from varnish_bans_manager.core.tasks.base import MonitoredTask, SingleInstanceTask
from varnish_bans_manager.core.models import BanSubmission, BanSubmissionItem, Setting


class NotifySubmissions(SingleInstanceTask):
    """
    Send a notification to the administrator with a report
    of all bans submited lately.
    """
    ignore_result = True
    soft_time_limit = 600  # 10 minutes.

    def irun(self):
        # Recover current state to go on where we ended last time,
        # or start from the beginning.
        if Setting.notify_bans and settings.VBM_NOTIFICATIONS_EMAIL:
            ban_submissions = BanSubmission.objects.filter(launched_at__isnull=False)
            if Setting.notify_bans_task_status is not None:
                ban_submissions = ban_submissions.filter(pk__gt=Setting.notify_bans_task_status)
            # Prepare data.
            submissions_log = [{
                    'id': ban_submission.id,
                    'launched_at': ban_submission.launched_at,
                    'user': ban_submission.user.human_name,
                    'ban_type': ban_submission.human_ban_type_name,
                    'expression': ban_submission.expression,
                    'target_type': ban_submission.target.human_class_name,
                    'target': ban_submission.target.human_name,
                    'items': ban_submission.items.all(),
                } for ban_submission in ban_submissions.iterator()]
            if len(submissions_log) > 0:
                # Send e-mail.
                send_templated_mail(
                    template_name='varnish-bans-manager/core/bans/submissions',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.VBM_NOTIFICATIONS_EMAIL],
                    bcc=settings.DEFAULT_BCC_EMAILS,
                    context={
                        'base_url': settings.VBM_BASE_URL,
                        'submissions_log': submissions_log,
                    },
                )
                # Store last seen id to keep track of our position.
                Setting.notify_bans_task_status = submissions_log[-1]['id']


class Submit(MonitoredTask):
    """
    Perform a ban submission.
    """
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


class Status(MonitoredTask):
    """
    Fetches & merges lists of bans.
    """
    def irun(self, cache):
        # Init result.
        result = {
            'cache': cache,
            'bans': {
                'shared': [],
                'differences': [],
            },
            'errors': [],
        }

        # Fetch expressions.
        bans = []
        num_items = len(cache.items)
        for index, node in enumerate(cache.items):
            try:
                bans.append((node, set(node.ban_list())))
            except Exception as e:
                result['errors'].append((node.human_name, unicode(e)))
            self.set_progress(index + 1, num_items)

        # Merge expressions.
        if bans:
            shared = set.intersection(*[expressions for (node, expressions) in bans])
            for (node, expressions) in bans:
                difference = expressions.difference(shared)
                if difference:
                    result['bans']['differences'].append((node.human_name, sorted(list(difference))))
            result['bans']['shared'] = sorted(list(shared))

        # Done!
        return result
