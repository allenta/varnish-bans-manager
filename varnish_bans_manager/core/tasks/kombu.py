# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from kombu.transport.django.models import Message
from varnish_bans_manager.core.tasks.base import SingleInstanceTask


class PurgeInvisible(SingleInstanceTask):
    ignore_result = True
    soft_time_limit = 600  # 10 minutes.

    def irun(self):
        Message.objects.cleanup()
