# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import json
from django.http import HttpResponse
from varnish_bans_manager.core.helpers.commands import is_redirection


class HttpResponseAjax(HttpResponse):

    def __init__(self, commands=None, request=None):
        self.commands = commands if commands is not None else []
        self.is_iframe_upload = \
            request.is_iframe_upload() if request else False
        super(HttpResponseAjax, self).__init__(
            self.dumps(),
            content_type=(
                'text/html' if self.is_iframe_upload else 'application/json'))

    def add_command(self, command):
        self.commands.append(command)
        self.content = self.dumps()

    def contains_redirection(self):
        return any(is_redirection(command) for command in self.commands)

    def dumps(self):
        contents = json.dumps(self.commands)
        # See http://jquery.malsup.com/form/#file-upload.
        if self.is_iframe_upload:
            return '<textarea>' + contents + '</textarea>'
        else:
            return contents
