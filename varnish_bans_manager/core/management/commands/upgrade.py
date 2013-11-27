# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
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
        self._syncdb()
        self._createcachetable()

    def _syncdb(self):
        # Synchronize DB.
        call_command('syncdb')
        # And apply all pending migrations.
        call_command('migrate')

    def _createcachetable(self):
        # Check cache is enabled in settings.
        if settings.CACHES and 'default' in settings.CACHES:
            cache_settings = settings.CACHES['default']
            cache_backend = cache_settings.get('BACKEND')
            # Using DB backend?
            if cache_backend == 'django.core.cache.backends.db.DatabaseCache':
                tablename = cache_settings.get('LOCATION')
                connection = connections[DEFAULT_DB_ALIAS]
                # Make sure cache table exists.
                if tablename not in connection.introspection.table_names():
                    print 'Creating %s table ...' % tablename
                    call_command('createcachetable', tablename)
