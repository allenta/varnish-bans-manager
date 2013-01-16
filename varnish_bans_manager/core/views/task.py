# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from abc import ABCMeta
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.views.generic import View
from celery.task.control import revoke
from varnish_bans_manager.core.helpers.http import HttpResponseAjax
from varnish_bans_manager.core.helpers import commands
from varnish_bans_manager.core import tasks
from varnish_bans_manager.core.helpers import DEFAULT_ERROR_MESSAGE
from varnish_bans_manager.core.helpers.views import ajax_required


class Base(View):
    __metaclass__ = ABCMeta

    @method_decorator(login_required)
    @method_decorator(ajax_required)
    def dispatch(self, *args, **kwargs):
        return super(Base, self).dispatch(*args, **kwargs)


class Progress(Base):
    def get(self, request, token):
        async_result = tasks.find(request, token)
        if async_result:
            if async_result.successful():
                cmds = [commands.hide_progress()]
                if 'callback' in async_result.result:
                    fn = async_result.result['callback']['fn']
                    # Transform 'fn' in a callable.
                    if isinstance(fn, tuple) and len(fn) == 2:
                        (path, static_method) = fn
                        index = path.rfind('.')
                        classname = path[index + 1:len(path)]
                        module = __import__(path[0:index], fromlist=[classname])
                        klass = getattr(module, classname)
                        callable = getattr(klass, static_method)
                    else:
                        callable = None
                    # Call callable.
                    if callable:
                        cmds.extend(callable.__call__(
                            request,
                            async_result.result['result'],
                            async_result.result['callback']['context']
                        ))
                async_result.forget()
                return HttpResponseAjax(cmds, request)
            elif async_result.failed():
                async_result.forget()
                messages.error(request, DEFAULT_ERROR_MESSAGE)
                return HttpResponseAjax([
                    commands.hide_progress(),
                ], request)
            elif async_result.status == 'PROGRESS':
                return HttpResponseAjax([
                    commands.update_progress(async_result.result['value']),
                ], request)
            else:
                return HttpResponseAjax([
                    commands.update_progress(),
                ], request)
        else:
            messages.error(request, DEFAULT_ERROR_MESSAGE)
            return HttpResponseAjax([
                commands.hide_progress(),
            ], request)


class Cancel(Base):
    def post(self, request, token):
        async_result = tasks.find(request, token)
        if async_result and async_result.task_id:
            revoke(async_result.task_id, terminate=True, signal='SIGKILL')
            messages.info(request, _("The task execution has been aborted."))
        else:
            messages.error(request, DEFAULT_ERROR_MESSAGE)
        return HttpResponseAjax([
            commands.hide_progress(),
        ], request)
