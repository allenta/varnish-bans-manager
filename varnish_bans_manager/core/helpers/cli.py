# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
import re
from telnetlib import Telnet
from hashlib import sha256
from django.utils.translation import ugettext_lazy as _


class Varnish(Telnet):
    """
    Simple CLI to access a Varnish caching node management port. See:

        - https://www.varnish-cache.org/trac/wiki/CLI
        - https://www.varnish-cache.org/docs/3.0/tutorial/purging.html
        - https://www.varnish-cache.org/docs/2.1/tutorial/purging.html
        - https://www.varnish-cache.org/docs/3.0/reference/varnish-cli.html
        - https://github.com/justquick/python-varnish
        - http://code.google.com/p/pyvarnishmport/
    """
    error_messages = {
        'missing_secret': _(
            'Cache has requested authentication but a secret key was not provided.'),
        'failed_connection': _(
            'Connection to cache failed with status %(status)d.'),
        'failed_command': _(
            "Execution of command failed with status %(status)d: '%(text)s'."),
    }

    def __init__(self, host, port, name, secret=None, version=30, timeout=5):
        # Try to establish connection.
        Telnet.__init__(self, host, port, timeout)
        self.name = name
        self.version = version
        (status, length), content = self._read()

        # Authentication requested?
        if status == 107:
            if secret:
                self._auth(secret, content)
            else:
                raise Varnish.Exception(self.error_messages['missing_secret'])
        # Failed connection?
        elif status != 200:
            raise Varnish.Exception(self.error_messages['failed_connection'] % {
                'status': status,
            })

    def ban(self, expression):
        """
        (ban|purge) field operator argument [&& field operator argument [...]]

            Invalidates all documents matching the ban expression.
        """
        self._fetch('%s %s' % (
            'purge' if self.version < 30 else 'ban',
            expression,
        ))

    def ban_list(self):
        """
        (ban|purge).list

            Fetches the list of bans.
        """
        # Fetch list of bans.
        content = self._fetch('%s.list' % (
            'purge' if self.version < 30 else 'ban',
        ))[1]

        # Parse bans & build result.
        result = []
        parser = re.compile(r'^(?P<address>[^\s]+)\s+(?P<time>\d+\.\d+)\s+(?P<pointers>\d+G?)\s+(?P<ban>.*)$')
        for line in content.split('\n'):
            match = parser.match(line)
            if match:
                address, time, pointers, ban = match.groups()
                result.append(ban)

        # Done!
        return result

    def quit(self):
        """
        quit

            Closes the connection to the Varnish CLI.
        """
        self.close()

    def _read(self):
        (status, length), content = map(int, self.read_until('\n').split()), ''
        while len(content) < length:
            content += self.read_some()
        return (status, length), content[:-1]

    def _auth(self, secret, content):
        challenge = content[:32]
        response = sha256('%s\n%s\n%s\n' % (challenge, secret, challenge))
        self._fetch('auth %s' % response.hexdigest())

    def _fetch(self, command):
        """
        Runs a command on a Varnish caching node and return the result.
        Return value is a tuple of ((status, length), content).
        """
        self.write(('%s\n' % command).encode("utf8"))
        while 1:
            buffer = self.read_until('\n').strip()
            if len(buffer):
                break
        status, length = map(int, buffer.split())
        if status == 200:
            content = ''
            while len(content) < length:
                content += self.read_until('\n')
            self.read_eager()
            return (status, length), content
        else:
            raise Varnish.Exception(self.error_messages['failed_command'] % {
                'status': status,
                'text': self.read_until('\n').strip(),
            })

    class Exception(Exception):
        pass
