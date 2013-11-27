# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import simplejson as json
from django.conf import settings
from varnish_bans_manager.core.helpers.views import get_messages


def messages(request):
    '''
    Returns a lazy 'messages' context variable (JSON string).

    '''
    return {'messages': json.dumps(get_messages(request))}


def page_id(request):
    return {'page_id': request.page_id}


def is_production(request):
    return {'is_production': settings.IS_PRODUCTION}
