# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import


def initialize_command():
    _initialize_umask()


def initialize_request():
    _initialize_umask()


def initialize_task():
    _initialize_umask()


def initialize_worker():
    # Media generator URLs need to be refreshed on development mode.
    # This is mainly needed for sending e-mails with images.
    from mediagenerator.settings import MEDIA_DEV_MODE
    from mediagenerator.utils import _refresh_dev_names
    if MEDIA_DEV_MODE:
        _refresh_dev_names()


def _initialize_umask():
    # Set permissions for created folders.
    import os
    os.umask(0022)
