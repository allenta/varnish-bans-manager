# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
import random
import string
import os
import posixpath
import time
from urllib import unquote
from django.utils.http import http_date
from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from mimetypes import guess_type
from tempfile import NamedTemporaryFile
from django.core.urlresolvers import reverse
from django.core.signing import TimestampSigner, b64_encode, b64_decode
from varnish_bans_manager.filesystem.tasks import CleanupTemporary


TEMPORARY_FILE_TTL = 86400


def _lazy_load(fn):
    _cached = []

    def _decorated():
        if not _cached:
            _cached.append(fn())
        return _cached[0]

    def clear():
        while _cached:
            _cached.pop()
    _decorated.clear = clear
    return _decorated


@_lazy_load
def _get_sendfile():
    from django.utils.importlib import import_module
    from django.core.exceptions import ImproperlyConfigured

    backend = getattr(settings, 'FILESYSTEM_SENDFILE_BACKEND', None)
    if not backend:
        raise ImproperlyConfigured('You must specify a valued for FILESYSTEM_SENDFILE_BACKEND')
    module = import_module(backend)
    return module.sendfile


def sendfile(request, filename, attachment=False, attachment_filename=None, mimetype=None, encoding=None, strong_caching=True):
    '''
    Create a response to send file using backend configured in FILESYSTEM_SENDFILE_BACKEND

    If attachment is True the content-disposition header will be set with either
    the filename given or else the attachment_filename (of specified).  This
    will typically prompt the user to download the file, rather than view it.

    If no mimetype or encoding are specified, then they will be guessed via the
    filename (using the standard python mimetypes module)
    '''
    _sendfile = _get_sendfile()

    guessed_mimetype, guessed_encoding = guess_type(filename)
    if mimetype is None:
        if guessed_mimetype:
            mimetype = guessed_mimetype
        else:
            mimetype = 'application/octet-stream'

    response = _sendfile(request, filename, mimetype=mimetype)
    if attachment:
        attachment_filename = attachment_filename or os.path.basename(filename)
        response['Content-Disposition'] = 'attachment; filename="%s"' % attachment_filename

    response['Content-length'] = os.path.getsize(filename)
    response['Content-Type'] = mimetype
    if not encoding:
        encoding = guessed_encoding
    if encoding:
        response['Content-Encoding'] = encoding

    if strong_caching:
        response['Last-Modified'] = 'Sat, 01 Jan 2000 00:00:00 GMT'
        response['Cache-Control'] = 'private,max-age=31104000'
        response['Expires'] = http_date(time.time() + 31104000)
    else:
        response['Cache-Control'] = 'private'

    return response


def randomize_filename(filename, length=32, prefix=''):
    splitted = os.path.splitext(filename)
    if isinstance(prefix, bool):
        prefix = (splitted[0] + '.') if prefix else ''
    return \
        prefix +\
        ''.join(random.choice(string.ascii_letters + string.digits) for x in range(length)) + \
        splitted[1]


def open_public_file(name, mode='w'):
    dir = secure_join(settings.MEDIA_ROOT, 'public', os.path.dirname(name))
    if not os.path.exists(dir):
        os.makedirs(dir)
    return open(secure_join(settings.MEDIA_ROOT, 'public', name), mode)


def find_public_file(path):
    return secure_join(settings.MEDIA_ROOT, 'public', path)


def new_temporary_file(filename, mimetype, prefix=''):
    dir = secure_join(settings.MEDIA_ROOT, 'temporary')
    if not os.path.exists(dir):
        os.makedirs(dir)
    f = NamedTemporaryFile(
        mode='wb',
        prefix=prefix,
        suffix=os.path.splitext(filename)[1],
        delete=False,
        dir=dir)
    CleanupTemporary().apply_async((f.name,), countdown=TEMPORARY_FILE_TTL)
    signer = TimestampSigner(sep=':')
    url = reverse('filesystem-temporary-download', kwargs={
        'token': signer.sign(b64_encode('%s,%s,%s' % (os.path.basename(f.name), filename, mimetype))),
        'filename': filename,
    })
    return f, url


def find_temporary_file(token):
    signer = TimestampSigner(sep=':')
    filename, attachment_filename, mimetype = b64_decode(signer.unsign(token, max_age=TEMPORARY_FILE_TTL).encode('utf-8')).split(',')
    return secure_join(settings.MEDIA_ROOT, 'temporary', filename), attachment_filename, mimetype


def find_static_file(path):
    return secure_join(settings.GENERATED_MEDIA_DIR, path)


def secure_join(root, *paths):
    result = ''
    for path in paths:
        newpath = ''
        path = posixpath.normpath(unquote(path))
        path = path.lstrip('/')
        for part in path.split('/'):
            if not part:
                # Strip empty path components.
                continue
            drive, part = os.path.splitdrive(part)
            head, part = os.path.split(part)
            if part in (os.curdir, os.pardir):
                # Strip '.' and '..' in path.
                continue
            newpath = os.path.join(newpath, part).replace('\\', '/')
        if newpath and path != newpath:
            raise SuspiciousOperation()
        result = os.path.join(result, newpath)
    return os.path.join(root, result)
