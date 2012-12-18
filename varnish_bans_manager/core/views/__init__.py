# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.views.generic import View
from varnish_bans_manager.core.helpers.views import ajaxify
from varnish_bans_manager.core.views import bans, caches, users, settings, task, user


class Index(View):
    @method_decorator(ajaxify)
    def get(self, request):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('home'))
        else:
            return HttpResponseRedirect(reverse('user-login'))


class Home(View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return bans.Basic.as_view()(request)
