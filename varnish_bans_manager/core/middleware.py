# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
import time
import logging
import simplejson as json
from time import gmtime, strftime
from django.db import connection
from django.utils.datastructures import SortedDict
from django.conf import settings
from django.views.debug import get_safe_settings
from django.core.urlresolvers import resolve
from django.http import Http404, HttpResponse
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.utils.encoding import smart_unicode
from django.template import loader, Template, Context
from django.contrib.auth.decorators import login_required
from varnish_bans_manager import core
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.helpers.views import get_messages
from varnish_bans_manager.core.helpers import commands


def _replace_insensitive(string, target, replacement):
    """
    Similar to string.replace() but case insensitive.
    Code borrowed from:
    http://forums.devshed.com/python-programming-11/case-insensitive-string-replace-490921.html
    """
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target):]
    # No results so return the original string.
    else:
        return string


def _can_append_script(response):
    return isinstance(response, HttpResponse) and \
        response.status_code == 200 and \
        'gzip' not in response.get('Content-Encoding', '') and \
        response['Content-Type'].split(';')[0] in (
            'text/html', 'application/xhtml+xml')


def _append_script(response, script):
    response.content = _replace_insensitive(
        smart_unicode(response.content),
        u'</body>',
        smart_unicode(script + u'</body>'))
    if response.get('Content-Length', None):
        response['Content-Length'] = len(response.content)


class CustomizationsMiddleware:
    def process_request(self, request):
        # Request-level initializations.
        core.initialize_request()

        # Initialize page id.
        request.page_id = None

        # Use HTTP_X_FORWARDED_FOR header as REMOTE_ADDR if present.
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            # HTTP_X_FORWARDED_FOR can be a comma-separated list of IPs.
            # Take just the first one.
            request.META['REMOTE_ADDR'] = request.META['HTTP_X_FORWARDED_FOR'].split(",")[0]

        # Add custom is_iframe_upload method.
        request.is_iframe_upload = lambda: \
            request.method == 'POST' and \
            '_iframe_upload' in request.POST

        # Redefine is_ajax method.
        request.is_ajax = lambda: \
            request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' or \
            request.is_iframe_upload()

        # Add custom is_navigation method.
        request.is_navigation = lambda: \
            request.is_ajax() and \
            request.method == 'GET' and \
            request.META.get('HTTP_X_NAVIGATION') == '1'

        # Done!
        return None

    def process_view(self, request, view_func, view_args, view_kwargs):
        # TODO. Avoid duplicated resolve: use request.resolver_match.url_name on django 1.5.
        # https://github.com/django/django/pull/399
        request.page_id = resolve(request.path_info).url_name.replace('.', '-')
        return None


class SecurityMiddleware:
    """
    Extra check to force authentication for all views by default. Therefore, 'login_required'
    decorator is not required, but it's recommended (documentation, extra check if this
    middleware is disabled, etc.).
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        is_login_required = view_kwargs.pop('login_required', True)
        if is_login_required and not request.user.is_authenticated():
            return login_required(view_func)(request, *view_args, **view_kwargs)
        return None


class SSLRedirectMiddleware:
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not settings.HTTPS_ENABLED == request.is_secure():
            return self._redirect(request, settings.HTTPS_ENABLED)
        return None

    def _redirect(self, request, secure):
        protocol = secure and "https" or "http"
        url = "%s://%s%s" % (protocol, get_host(request), request.get_full_path())
        if settings.DEBUG and request.method == 'POST':
            raise RuntimeError(
                """Django can't perform a redirect while maintaining POST data.
                Please structure your views so that redirects only occur during GETs.""")
        if request.is_ajax():
            return HttpResponseAjax([commands.redirect(url)])
        else:
            return HttpResponseRedirect(url)


class MessagingMiddleware:
    def process_response(self, request, response):
        if isinstance(response, HttpResponseAjax):
            if (not response.contains_redirection()):
                messages = get_messages(request)
                if len(messages) > 0:
                    response.add_command(commands.notify(messages))
        return response


class PageIdMiddleware:
    def process_response(self, request, response):
        if isinstance(response, HttpResponseAjax):
            if request.is_navigation():
                response.add_command(commands.update_page_id(request))
        return response


class VersionMiddleware:
    def process_response(self, request, response):
        if isinstance(response, HttpResponseAjax):
            response.add_command(commands.check_version())
        return response


class DebugMiddleware:

    HEADER_FILTER = (
        'CONTENT_TYPE',
        'HTTP_ACCEPT',
        'HTTP_ACCEPT_CHARSET',
        'HTTP_ACCEPT_ENCODING',
        'HTTP_ACCEPT_LANGUAGE',
        'HTTP_CACHE_CONTROL',
        'HTTP_CONNECTION',
        'HTTP_HOST',
        'HTTP_KEEP_ALIVE',
        'HTTP_REFERER',
        'HTTP_USER_AGENT',
        'QUERY_STRING',
        'REMOTE_ADDR',
        'REMOTE_HOST',
        'REQUEST_METHOD',
        'SCRIPT_NAME',
        'SERVER_NAME',
        'SERVER_PORT',
        'SERVER_PROTOCOL',
        'SERVER_SOFTWARE',
    )

    def process_response(self, request, response):
        if settings.DEBUG:
            # Request report.
            req_report = {
                'path': request.path_info,
                'get': [(k, request.GET.getlist(k)) for k in request.GET],
                'post': [(k, request.POST.getlist(k)) for k in request.POST],
                'cookies': [(k, request.COOKIES.get(k)) for k in request.COOKIES],
                'view': {
                    'func': '<no view>',
                    'args': 'None',
                    'kwargs': 'None',
                    'url': 'None',
                },
                'headers': dict(
                    [(k, request.META[k]) for k in self.HEADER_FILTER if k in request.META]
                ),
                'settings': SortedDict(sorted(get_safe_settings().items(), key=lambda s: s[0])),
            }

            try:
                match = resolve(request.path)
                func, args, kwargs = match
                req_report['view']['func'] = self._get_name_from_obj(func)
                req_report['view']['args'] = args
                req_report['view']['kwargs'] = kwargs
                req_report['view']['url'] = getattr(match, 'url_name', '<unavailable>')
            except Http404:
                req_report['view']['func'] = request.path
                pass

            if hasattr(request, 'session'):
                req_report['session'] = [
                    (k, request.session.get(k))
                    for k in request.session.iterkeys()
                ]

            # MySQL report.
            mysql_report = {
                'time': sum([float(q['time']) for q in connection.queries]),
                'log': [{'time': q['time'], 'sql': q['sql']} for q in connection.queries],
            }

            # Log.
            context = Context({'req': req_report, 'mysql': mysql_report})
            if settings.DEBUG:
                logging.\
                    getLogger('vbm').\
                    debug(loader.get_template('varnish-bans-manager/partials/_debug.txt').render(context))
            report = loader.get_template('varnish-bans-manager/partials/_debug.html').render(context)
            if isinstance(response, HttpResponseAjax):
                response.add_command(commands.debug(report))
            elif _can_append_script(response):
                script = '<script type="text/javascript">(function ($) { vbm.ready(function(context) { vbm.commands.debug(%s); });})(jQuery);</script>' % (json.dumps(report))
                _append_script(response, script)

        return response

    def _get_name_from_obj(self, obj):
        if hasattr(obj, '__name__'):
            name = obj.__name__
        elif hasattr(obj, '__class__') and hasattr(obj.__class__, '__name__'):
            name = obj.__class__.__name__
        else:
            name = '<unknown>'
        if hasattr(obj, '__module__'):
            module = obj.__module__
            name = '%s.%s' % (module, name)
        return name


class TimerMiddleware:
    def process_request(self, request):
        if settings.DEBUG:
            # Save start time.
            request.start_time = time.time()

            # Console log.
            template = Template('=' * 80 + '\n{{tst}}: {{method}} {{path|safe}}\n' + '=' * 80)
            logging.getLogger('vbm').debug(template.render(Context({'tst': strftime('%Y/%m/%d @ %H:%M:%S', gmtime()), 'method': request.method, 'path': request.path})))

        # Done!
        return None

    def process_response(self, request, response):
        # Console & client log.
        if settings.DEBUG:
            # Calculate total time.
            total_time = time.time() - request.start_time

            # Console log.
            template = Template('\n=> Total time: {{time}}s\n')
            logging.getLogger('vbm').debug(template.render(Context({'time': total_time})))

            # Client output.
            if isinstance(response, HttpResponseAjax):
                response.add_command(commands.timer(total_time))
            elif _can_append_script(response):
                script = '<script type="text/javascript">(function ($) { vbm.ready(function(context) { vbm.commands.timer(%f); });})(jQuery);</script>' % (total_time)
                _append_script(response, script)

        return response


class AjaxRedirectMiddleware:
    """
    Intercepts standard HTTP redirections replacing them by AJAX commands when required.
    """
    def process_response(self, request, response):
        if request.is_ajax():
            if isinstance(response, HttpResponseRedirect) or \
               isinstance(response, HttpResponsePermanentRedirect):
                return HttpResponseAjax([commands.redirect(response['Location'])])
        return response
