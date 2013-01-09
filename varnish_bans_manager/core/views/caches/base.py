# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from abc import ABCMeta
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from varnish_bans_manager.core.helpers.views import ajaxify


class Base(View):
    __metaclass__ = ABCMeta

    @method_decorator(login_required)
    @method_decorator(permission_required('core.can_access_caches_management'))
    @method_decorator(ajaxify)
    def dispatch(self, *args, **kwargs):
        return super(Base, self).dispatch(*args, **kwargs)
