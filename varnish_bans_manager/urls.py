# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

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
from varnish_bans_manager.core.views import bans as core_bans_views
from varnish_bans_manager.core.views import caches as core_caches_views
from varnish_bans_manager.core.views.caches import groups as core_caches_groups_views
from varnish_bans_manager.core.views.caches import nodes as core_caches_nodes_views
from varnish_bans_manager.core.views import settings as core_settings_views
from varnish_bans_manager.core.views import task as core_task_views
from varnish_bans_manager.core.views import user as core_user_views
from varnish_bans_manager.core.views import users as core_users_views
from varnish_bans_manager.filesystem import views as filesystem_views

##
## Custom options:
##
##    - 'login_required' (defaults to True)
##

###############################################################################
## '^user/' HANDLERS.
###############################################################################

user_patterns = patterns(
    '',
    url(r'^login/$',
        core_user_views.Login.as_view(),
        {'login_required': False},
        name='user-login'),
    url(r'^logout/$',
        core_user_views.Logout.as_view(),
        {'login_required': False},
        name='user-logout'),
    url(r'^password/reset/$',
        core_user_views.PasswordReset.as_view(),
        {'login_required': False},
        name='user-password-reset'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        core_user_views.PasswordResetConfirm.as_view(),
        {'login_required': False},
        name='user-password-reset-confirm'),
    url(r'^profile/$',
        core_user_views.Profile.as_view(),
        name='user-profile'),
    url(r'^password/$',
        core_user_views.Password.as_view(),
        name='user-password'),
)

###############################################################################
## '^bans/' HANDLERS.
###############################################################################

bans_patterns = patterns(
    '',
    url(r'^basic/$',
        core_bans_views.Basic.as_view(),
        name='bans-basic'),
    url(r'^advanced/$',
        core_bans_views.Advanced.as_view(),
        name='bans-advanced'),
    url(r'^expert/$',
        core_bans_views.Expert.as_view(),
        name='bans-expert'),
    url(r'^submissions/$',
        core_bans_views.Submissions.as_view(),
        name='bans-submissions'),
    url(r'^status/$',
        core_bans_views.Status.as_view(),
        name='bans-status'),
)

###############################################################################
## '^caches/' HANDLERS.
###############################################################################

caches_patterns = patterns(
    '',
    url(r'^browse/$',
        core_caches_views.Browse.as_view(),
        name='caches-browse'),
    url(r'^groups/add/$',
        core_caches_groups_views.Add.as_view(),
        name='caches-groups-add'),
    url(r'^groups/(?P<id>\d+)/update/$',
        core_caches_groups_views.Update.as_view(),
        name='caches-groups-update'),
    url(r'^groups/(?P<id>\d+)/delete/$',
        core_caches_groups_views.Delete.as_view(),
        name='caches-groups-delete'),
    url(r'^groups/reorder/$',
        core_caches_groups_views.Reorder.as_view(),
        name='caches-groups-reorder'),
    url(r'^nodes/add/$',
        core_caches_nodes_views.Add.as_view(),
        name='caches-nodes-add'),
    url(r'^nodes/(?P<id>\d+)/update/$',
        core_caches_nodes_views.Update.as_view(),
        name='caches-nodes-update'),
    url(r'^nodes/(?P<id>\d+)/delete/$',
        core_caches_nodes_views.Delete.as_view(),
        name='caches-nodes-delete'),
    url(r'^nodes/reorder/$',
        core_caches_nodes_views.Reorder.as_view(),
        name='caches-nodes-reorder'),
)

###############################################################################
## '^users/' HANDLERS.
###############################################################################

users_patterns = patterns(
    '',
    url(r'^browse/$',
        core_users_views.Browse.as_view(),
        name='users-browse'),
    url(r'^bulk/$',
        core_users_views.Bulk.as_view(),
        name='users-bulk'),
    url(r'^add/$',
        core_users_views.Add.as_view(),
        name='users-add'),
    url(r'^(?P<id>\d+)/update/$',
        core_users_views.Update.as_view(),
        name='users-update'),
    url(r'^(?P<id>\d+)/delete/$',
        core_users_views.Delete.as_view(),
        name='users-delete'),
)

###############################################################################
## '^settings/' HANDLERS.
###############################################################################

settings_patterns = patterns(
    '',
    url(r'^general/$',
        core_settings_views.General.as_view(),
        name='settings-general'),
)

###############################################################################
## '^files/' HANDLERS.
###############################################################################

filesystem_patterns = patterns(
    '',
    url(r'^public/(?P<path>.*)$',
        filesystem_views.PublicDownload.as_view(),
        {'login_required': False},
        name='filesystem-public-download'),
    url(r'^private/(?P<app_label>[0-9A-Za-z]+)/(?P<model_name>[0-9A-Za-z]+)/(?P<object_id>\d+)/(?P<field_name>[0-9A-Za-z]+)/(?P<filename>.*)$',
        filesystem_views.PrivateDownload.as_view(),
        name='filesystem-private-download'),
    url(r'^temporary/(?P<token>[0-9A-Za-z-:_]+)/(?P<filename>.*)$',
        filesystem_views.TemporaryDownload.as_view(),
        name='filesystem-temporary-download'),
)

###############################################################################
## '^task/' HANDLERS.
###############################################################################

task_patterns = patterns(
    '',
    url(r'^(?P<token>[0-9A-Za-z-:_]+)/progress/$',
        core_task_views.Progress.as_view(),
        name='task-progress'),
    url(r'^(?P<token>[0-9A-Za-z-:_]+)/cancel/$',
        core_task_views.Cancel.as_view(),
        name='task-cancel'),
)

###############################################################################
## ALL URL HANDLERS.
###############################################################################

urlpatterns = i18n_patterns(
    '',
    url(r'^$',
        core_views.Index.as_view(),
        {'login_required': False},
        name='index'),
    url(r'^home/$',
        core_views.Home.as_view(),
        name='home'),
    url(r'^user/', include(user_patterns)),
    url(r'^bans/', include(bans_patterns)),
    url(r'^caches/', include(caches_patterns)),
    url(r'^users/', include(users_patterns)),
    url(r'^settings/', include(settings_patterns)),
    url(r'^task/', include(task_patterns)),
) + patterns(
    '',
    url(r'^%s/(?P<path>.*)$' % settings.PRODUCTION_MEDIA_URL.lstrip('/').rstrip('/'),
        filesystem_views.StaticDownload.as_view(),
        {'login_required': False},
        name='filesystem-static.download'),
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
