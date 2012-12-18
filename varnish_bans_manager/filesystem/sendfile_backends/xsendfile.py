# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.http import HttpResponse


def sendfile(request, filename, **kwargs):
    response = HttpResponse()
    response['X-Sendfile'] = filename
    return response
