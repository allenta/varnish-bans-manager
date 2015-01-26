# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import multiprocessing
import os
import tempfile
from optparse import make_option
from pprint import pprint
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
        make_option('--log-file', dest='log_file', default=settings.VBM_HTTP.get('log_file', '-')),
    )

    help = 'Launches Varnish Bans Manager HTTP frontend.'

    def handle(self, *args, **options):
        # Do any necessary upgrades in the DB.
        print 'Doing any required upgrades before service startup...'
        call_command('upgrade')

        # Process options.
        opts = {
            'log_level': 'debug' if settings.DEBUG else 'info',
            'secure_scheme_headers': {
                settings.SECURE_PROXY_SSL_HEADER[0]:
                    settings.SECURE_PROXY_SSL_HEADER[1],
            }
        }
        opts.update(settings.VBM_HTTP)
        opts.update(dict(
            (option, value) for option, value in options.iteritems()
            if option not in [op.dest for op in BaseCommand.option_list]
        ))

        # Extract "log_file" option. In order to be able to use the special
        # value "-", this option must be passed as an argument to gunicorn
        # instead of adding it to the config file.
        log_file = opts.pop('log_file')

        # Update Gunicorn's config file. This is the only current way to
        # pass certain settings like the "secure_scheme_headers".
        config_file = os.path.join(
            tempfile.gettempdir(), 'varnish-bans-manager-gunicorn.conf');
        with open(config_file, 'w') as f:
            for option, value in opts.iteritems():
                f.write('%s=' % option)
                pprint(value, f)

        # Run!
        os.execvp('gunicorn', [
            'gunicorn',
            '--log-file=' + log_file,
            '--config=' + config_file,
            'varnish_bans_manager.wsgi:application'])
