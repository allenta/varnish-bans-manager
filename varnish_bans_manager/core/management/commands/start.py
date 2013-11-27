# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import multiprocessing
from optparse import make_option
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--daemon', dest='daemon', default=settings.VBM_HTTP.get('daemon', False), action='store_const', const=True),
        make_option('--workers', dest='workers', default=settings.VBM_HTTP.get('workers', multiprocessing.cpu_count() * 2 + 1), type=int),
        make_option('--pid', dest='pidfile', default=settings.VBM_HTTP.get('pidfile', None)),
        make_option('--user', dest='user', default=settings.VBM_HTTP.get('user', None)),
        make_option('--group', dest='group', default=settings.VBM_HTTP.get('group', None)),
    )
    help = 'Launches Varnish Bans Manager HTTP frontend.'

    def handle(self, *args, **options):
        # Do any necessary upgrades in the DB.
        print 'Doing any required upgrades before service startup...'
        call_command('upgrade')

        # Run!
        opts = settings.VBM_HTTP
        opts.update(options)
        opts['debug'] = settings.DEBUG
        opts['secure_scheme_headers'] = {
            settings.SECURE_PROXY_SSL_HEADER[0]: settings.SECURE_PROXY_SSL_HEADER[1],
        }
        call_command('run_gunicorn', **opts)
