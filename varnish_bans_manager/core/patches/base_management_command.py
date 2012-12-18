# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.core.management import base
from varnish_bans_manager import core

base_execute = base.BaseCommand.execute


def execute(self, *args, **options):
    core.initialize()
    base_execute(self, *args, **options)


base.BaseCommand.execute = execute
