# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

##
## APP BASED ON:
##
##   - https://github.com/johnsensible/django-sendfile
##   - https://github.com/Atomidata/django-private-files
##

from __future__ import absolute_import
import os.path
from urllib import unquote
from django.db.models import get_model
from django.views.generic import View
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from varnish_bans_manager.filesystem import signals, sendfile, find_public_file, find_temporary_file, find_static_file


@require_http_methods(['GET'])
def public_download(request, path):
    try:
        path = find_public_file(path)
        return sendfile(request, path, attachment=False, strong_caching=True)
    except:
        return HttpResponseNotFound()


@login_required
@require_http_methods(['GET'])
def temporary_download(request, token, filename):
    try:
        path, attachment_filename, mimetype = find_temporary_file(token)
        return sendfile(request, path, attachment=True, attachment_filename=attachment_filename, mimetype=mimetype)
    except:
        return HttpResponseNotFound()


@login_required
@require_http_methods(['GET'])
def private_download(request, app_label, model_name, object_id, field_name, filename):
    model = get_model(app_label, model_name)
    if model:
        instance = get_object_or_404(model, pk=unquote(object_id))
        if hasattr(instance, field_name):
            field = getattr(instance, field_name)
            if field.condition(request, instance):
                if field and os.path.exists(field.path):
                    signals.pre_private_download.send(sender=model, instance=instance, field_name=field_name, request=request)
                    return sendfile(
                        request,
                        field.path,
                        attachment=field.attachment,
                        attachment_filename=field.attachment_filename(request, instance, field),
                        strong_caching=field.strong_caching)
                else:
                    field.generate()
                    return HttpResponseNotFound()
            else:
                return HttpResponseForbidden()
        else:
            return HttpResponseNotFound()
    else:
        return HttpResponseNotFound()


class StaticDownload(View):
    def get(self, request, path):
        try:
            path = find_static_file(path)
            return sendfile(request, path, attachment=False, strong_caching=True)
        except:
            return HttpResponseNotFound()
