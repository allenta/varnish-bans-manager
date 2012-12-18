# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import


def initialize():
    __initialize_umask()


def __initialize_umask():
    # Set permissions for created folders.
    import os
    os.umask(0022)
