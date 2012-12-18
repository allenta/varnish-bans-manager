# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
import os.path
from django.conf import settings
from django.http import HttpResponse


def _convert_file_to_url(filename):
    relpath = os.path.relpath(filename, settings.MEDIA_ROOT)
    return settings.FILESYSTEM_SENDFILE_URL + relpath


def sendfile(request, filename, **kwargs):
    response = HttpResponse()
    response['X-Accel-Redirect'] = _convert_file_to_url(filename)
    return response
