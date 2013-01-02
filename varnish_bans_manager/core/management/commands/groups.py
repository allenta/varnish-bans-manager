# -*- coding: utf-8 -*-

from __future__ import absolute_import
from optparse import make_option
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from varnish_bans_manager.core.models import Group


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--list', dest='op', action='store_const', const='list'),
        make_option('--add', dest='op', action='store_const', const='add'),
        make_option('--delete', dest='op', action='store_const', const='delete'),
        make_option('--id', dest='id', type='int'),
        make_option('--name', dest='name'),
    )
    help = """Usage,

    groups --list
    groups --add --name <value>
    groups --delete --id <value>
    """

    def handle(self, *args, **options):
        # --list
        if options.get('op') == 'list':
            return self._list()

        # --add
        elif options.get('op') == 'add' and \
             options.get('name') is not None:
            return self._add(
                options.get('name'),
            )

        # --delete
        elif options.get('op') == 'delete' and \
             options.get('id') is not None:
            return self._delete(
                self._get_object_or_command_error(Group, options.get('id'))
            )

        raise CommandError(self.help)

    def _list(self):
        self.stdout.write('id, name\n')
        for group in Group.objects.order_by('weight', 'created_at').all():
            self.stdout.write('%d, %s\n' % (
                group.id,
                group.name,
            ))

    def _add(self, name):
        try:
            group = Group(name=name)
            group.full_clean()
            group.save()
        except ValidationError:
            raise CommandError('Failed while validating new caching group.')

    def _delete(self, group):
        group.delete()

    def _get_object_or_command_error(self, model, pk=None):
        if pk is not None:
            try:
                return model.objects.get(pk=pk)
            except:
                raise CommandError('Failed to load %s instance with identifier %d.' % (model.__name__, pk,))
        else:
            return None
