# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.core.management import call_command
from django.db import connections, DEFAULT_DB_ALIAS


class Command(NoArgsCommand):
    help = 'Upgrades Varnish Bans Manager DB.'

    def handle_noargs(self, **options):
        # Apply pending migrations.
        call_command('migrate')

        # Create cache table if needed.
        self._createcachetable()

    def _createcachetable(self):
        # Check if any of the referenced DB tables in the CACHES setting does
        # not exist. If so, call the "createcachetable" command.
        tables = connections[DEFAULT_DB_ALIAS].introspection.table_names()
        if any(cache for cache in settings.CACHES.itervalues()
               if (cache.get('BACKEND') == 'django.core.cache.backends.db.DatabaseCache' and
                   cache.get('LOCATION') not in tables)):
            self.stdout.write('Creating missing cache tables')
            call_command('createcachetable')
