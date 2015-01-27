# -*- coding: utf-8 -*-

from __future__ import absolute_import
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from varnish_bans_manager.core.models import User


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--add', dest='op', action='store_const', const='add'),
        make_option('--administrator', dest='administrator', default=False, action='store_const', const=True),
        make_option('--email', dest='email'),
        make_option('--password', dest='password'),
        make_option('--firstname', dest='firstname'),
        make_option('--lastname', dest='lastname'),
    )
    help = '''Usage,

    users --add [--administrator] --email <value> --password <value> --firstname <value> --lastname <value>
    '''

    def handle(self, *args, **options):
        # Check arguments.
        if options.get('op') != 'add' or \
           not options.get('email') or \
           not options.get('password') or \
           not options.get('firstname') or \
           not options.get('lastname'):
            raise CommandError(self.help)

        # Check duplicated e-mails.
        if User.objects.filter(email__iexact=options.get('email'), is_active=True).exists():
            raise CommandError(
                'There is already an user with that e-mail address.')

        # Choose user creation method (superuser vs normal user).
        create_user_method = getattr(
            User.objects,
            'create_superuser' if options.get('administrator') else 'create_user')

        # Add new user.
        create_user_method(
            email=options.get('email'),
            password=options.get('password'),
            first_name=options.get('firstname'),
            last_name=options.get('lastname'))
