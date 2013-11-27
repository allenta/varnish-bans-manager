# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import os.path
from django.views.static import serve


def sendfile(request, filename, **kwargs):
    dirname = os.path.dirname(filename)
    basename = os.path.basename(filename)
    return serve(request, basename, dirname)
