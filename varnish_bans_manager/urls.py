# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.defaults import page_not_found, permission_denied, server_error
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from varnish_bans_manager.core.helpers import DEFAULT_ERROR_MESSAGE
from varnish_bans_manager.core import views as core_views
from varnish_bans_manager.filesystem import views as filesystem_views

##
## Custom options:
##
##    - 'login_required' (defaults to True)
##

###############################################################################
## '^user/' HANDLERS.
###############################################################################

user_patterns = patterns('varnish_bans_manager.core.views.user',
    url(r'^login/$',
        core_views.user.Login.as_view(),
        {'login_required': False},
        name="user-login"),
    url(r'^logout/$',
        core_views.user.Logout.as_view(),
        {'login_required': False},
        name="user-logout"),
    url(r'^password/reset/$',
        core_views.user.PasswordReset.as_view(),
        {'login_required': False},
        name="user-password-reset"),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        core_views.user.PasswordResetConfirm.as_view(),
        {'login_required': False},
        name="user-password-reset-confirm"),
    url(r'^profile/$',
        core_views.user.Profile.as_view(),
        name="user-profile"),
    url(r'^password/$',
        core_views.user.Password.as_view(),
        name="user-password"),
)

###############################################################################
## '^bans/' HANDLERS.
###############################################################################

bans_patterns = patterns('varnish_bans_manager.core.views.bans',
    url(r'^basic/$',
        core_views.bans.Basic.as_view(),
        name="bans-basic"),
    url(r'^advanced/$',
        core_views.bans.Advanced.as_view(),
        name="bans-advanced"),
    url(r'^expert/$',
        core_views.bans.Expert.as_view(),
        name="bans-expert"),
    url(r'^submissions/$',
        core_views.bans.Submissions.as_view(),
        name="bans-submissions"),
    url(r'^status/$',
        core_views.bans.Status.as_view(),
        name="bans-status"),
)

###############################################################################
## '^caches/' HANDLERS.
###############################################################################

caches_patterns = patterns('varnish_bans_manager.core.views.caches',
    url(r'^browse/$',
        core_views.caches.Browse.as_view(),
        name="caches-browse"),
    url(r'^groups/reorder$',
        core_views.caches.GroupsReorder.as_view(),
        name="caches-groups-reorder"),
)

###############################################################################
## '^users/' HANDLERS.
###############################################################################

users_patterns = patterns('varnish_bans_manager.core.views.users',
    url(r'^browse/$',
        core_views.users.Browse.as_view(),
        name="users-browse"),
    url(r'^bulk/$',
        core_views.users.Bulk.as_view(),
        name="users-bulk"),
    url(r'^add/$',
        core_views.users.Add.as_view(),
        name="users-add"),
    url(r'^(?P<id>\d+)/update/$',
        core_views.users.Update.as_view(),
        name="users-update"),
    url(r'^(?P<id>\d+)/delete/$',
        core_views.users.Delete.as_view(),
        name="users-delete"),
)

###############################################################################
## '^settings/' HANDLERS.
###############################################################################

settings_patterns = patterns('varnish_bans_manager.core.views.settings',
    url(r'^general/$',
        core_views.settings.General.as_view(),
        name="settings-general"),
)

###############################################################################
## '^files/' HANDLERS.
###############################################################################

filesystem_patterns = patterns('',
    url(r'^public/(?P<path>.*)$',
        'varnish_bans_manager.filesystem.views.public_download',
        {'login_required': False},
        name="filesystem-public-download"),
    url(r'^private/(?P<app_label>[0-9A-Za-z]+)/(?P<model_name>[0-9A-Za-z]+)/(?P<object_id>\d+)/(?P<field_name>[0-9A-Za-z]+)/(?P<filename>.*)$',
        'varnish_bans_manager.filesystem.views.private_download',
        name="filesystem-private-download"),
    url(r'^temporary/(?P<token>[0-9A-Za-z-:_]+)/(?P<filename>.*)$',
        'varnish_bans_manager.filesystem.views.temporary_download',
        name="filesystem-temporary-download"),
)

###############################################################################
## '^task/' HANDLERS.
###############################################################################

task_patterns = patterns('',
    url(r'^(?P<token>[0-9A-Za-z-:_]+)/progress/$',
        core_views.task.Progress.as_view(),
        name='task-progress'),
    url(r'^(?P<token>[0-9A-Za-z-:_]+)/cancel/$',
        core_views.task.Cancel.as_view(),
        name='task-cancel'),
)

###############################################################################
## ALL URL HANDLERS.
###############################################################################

urlpatterns = i18n_patterns('',
    url(r'^$',
        core_views.Index.as_view(),
        {'login_required': False},
        name='index'),
    url(r'^home/$',
        core_views.Home.as_view(),
        name="home"),
    url(r'^user/', include(user_patterns)),
    url(r'^bans/', include(bans_patterns)),
    url(r'^caches/', include(caches_patterns)),
    url(r'^users/', include(users_patterns)),
    url(r'^settings/', include(settings_patterns)),
    url(r'^task/', include(task_patterns)),
) + patterns('',
    url(r'^%s/(?P<path>.*)$' % settings.PRODUCTION_MEDIA_URL.lstrip('/').rstrip('/'),
        filesystem_views.StaticDownload.as_view(),
        {'login_required': False},
        name="filesystem-static.download"),
    url(r'^files/', include(filesystem_patterns)),
)


###############################################################################
## CUSTOM 403, 404, etc. HANDLERS.
###############################################################################


def _handler(default_handler, message):
    def fn(request, *args, **kwargs):
        # Standard 403/404/500 response?
        if request.path_info == '/' or request.path_info.startswith('/files/'):
            return default_handler(request, *args, **kwargs)
        else:
            # Message + 302.
            messages.error(request, message)
            if request.user.is_authenticated():
                return HttpResponseRedirect(reverse('home'))
            else:
                return HttpResponseRedirect(reverse('user-login'))
    return fn

handler403 = _handler(permission_denied, _('We are sorry, but you are not authorized to see the the requested contents.'))
handler404 = _handler(page_not_found, _('We are sorry, but the requested content could not be found.'))
handler500 = _handler(server_error, DEFAULT_ERROR_MESSAGE)
