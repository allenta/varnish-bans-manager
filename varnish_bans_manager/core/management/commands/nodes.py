# -*- coding: utf-8 -*-

from __future__ import absolute_import
from optparse import make_option
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from varnish_bans_manager.core.models import Node, Group


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--list', dest='op', action='store_const', const='list'),
        make_option('--add', dest='op', action='store_const', const='add'),
        make_option('--delete', dest='op', action='store_const', const='delete'),
        make_option('--id', dest='id', type='int'),
        make_option('--host', dest='host'),
        make_option('--port', dest='port', type='int'),
        make_option('--secret-file', dest='secret-file'),
        make_option('--legacy', dest='version', default=Node.VERSION_30, action='store_const', const=Node.VERSION_21),
        make_option('--name', dest='name'),
        make_option('--group', dest='group', type='int'),
    )
    help = '''Usage,

    nodes --list
    nodes --add --host <host> --port <port> [--secret-file <value>] [--legacy] [--name <value>] [--group <group>]
    nodes --delete --id <value>
    '''

    def handle(self, *args, **options):
        # --list
        if options.get('op') == 'list':
            return self._list()

        # --add
        elif options.get('op') == 'add' and \
           options.get('host') is not None and \
           options.get('port') is not None:
            return self._add(
                options.get('host'),
                options.get('port'),
                secret_file=options.get('secret-file'),
                version=options.get('version'),
                name=options.get('name'),
                group=self._get_object_or_command_error(Group, options.get('group'))
            )

        # --delete
        elif options.get('op') == 'delete' and \
             options.get('id') is not None:
            return self._delete(
                self._get_object_or_command_error(Node, options.get('id'))
            )

        raise CommandError(self.help)

    def _list(self):
        self.stdout.write('id, host, port, name, group\n')
        for node in Node.objects.order_by('weight', 'created_at').all():
            self.stdout.write('%d, %s, %d, %s, %s\n' % (
                node.id,
                node.host,
                node.port,
                node.name or '-',
                node.group.name if node.group else '-'
            ))

    def _add(self, host, port, secret_file=None, version=None, name=None, group=None):
        # Fetch shared secret.
        secret = None
        if secret_file is not None:
            try:
                with open(secret_file, 'r') as f:
                    secret = f.read()
            except:
                raise CommandError('Failed while while reading secret file.')

        # Validate & add new instance.
        try:
            node = Node(host=host, port=port, secret=secret, version=version, name=name, group=group)
            node.full_clean()
            node.save()
        except ValidationError:
            raise CommandError('Failed while validating new cache node.')

    def _delete(self, node):
        node.delete()

    def _get_object_or_command_error(self, model, pk=None):
        if pk is not None:
            try:
                return model.objects.get(pk=pk)
            except:
                raise CommandError('Failed to load %s instance with identifier %d.' % (model.__name__, pk,))
        else:
            return None
