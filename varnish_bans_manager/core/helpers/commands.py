# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _

DEFAULT_WEIGHT = 50
MAX_WEIGHT = 100


def is_redirection(command):
    return command['cmd'] in ['navigate', 'redirect', 'reload']


def navigate(url):
    return {
        'cmd': 'navigate',
        'args': [url],
        'weight': 0,
    }


def redirect(url):
    return {
        'cmd': 'redirect',
        'args': [url],
        'weight': 0,
    }


def reload(request):
    return {
        'cmd': 'navigate',
        'args': [request.path_info],
        'weight': 0,
    }


def update_page_id(request):
    return {
        'cmd': 'update_page_id',
        'args': [request.page_id],
        'weight': 1,
    }


def check_version():
    return {
        'cmd': 'check_version',
        'args': [settings.VERSION],
        'weight': 5,
    }


def set_content(contents):
    return {
        'cmd': 'set_content',
        'args': [contents],
        'weight': 10,
    }


def download(url):
    return {
        'cmd': 'download',
        'args': [url],
        'weight': DEFAULT_WEIGHT,
    }


def alert(message):
    return {
        'cmd': 'alert',
        'args': [message],
        'weight': DEFAULT_WEIGHT,
    }


def show_progress(token, timeout=1000, title=_('Applying changes...')):
    return {
        'cmd': 'show_progress',
        'args': [
            reverse('task-progress', kwargs={'token': token}),
            reverse('task-cancel', kwargs={'token': token}),
            timeout,
            title,
        ],
        'weight': DEFAULT_WEIGHT,
    }


def update_progress(value=None, timeout=1000):
    return {
        'cmd': 'update_progress',
        'args': [value, timeout],
        'weight': DEFAULT_WEIGHT,
    }


def hide_progress():
    return {
        'cmd': 'hide_progress',
        'args': [],
        'weight': DEFAULT_WEIGHT,
    }


def modal(template, context, context_instance):
    return {
        'cmd': 'modal',
        'args': [render_to_string(template, context, context_instance=context_instance)],
        'weight': DEFAULT_WEIGHT,
    }


def close_modal():
    return {
        'cmd': 'close_modal',
        'args': [],
        'weight': DEFAULT_WEIGHT,
    }


def notify(messages):
    return {
        'cmd': 'notify',
        'args': [messages],
        'weight': DEFAULT_WEIGHT,
    }


def timer(time):
    return {
        'cmd': 'timer',
        'args': ["%.3f" % time],
        'weight': MAX_WEIGHT,
    }


def debug(report):
    return {
        'cmd': 'debug',
        'args': [report],
        'weight': MAX_WEIGHT,
    }
