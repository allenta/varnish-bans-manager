# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.utils import timezone
from django.contrib.sessions.models import Session
from varnish_bans_manager.core.tasks.base import SingleInstanceTask


class PurgeExpired(SingleInstanceTask):
    ignore_result = True
    soft_time_limit = 600  # 10 minutes.

    def irun(self):
        Session.objects.filter(expire_date__lt=timezone.now()).delete()
