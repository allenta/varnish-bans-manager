# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.utils.translation import get_language
from django.core.signing import TimestampSigner, b64_encode, b64_decode
from celery.result import AsyncResult


def enqueue(request, task, *args, **kwargs):
    result = task.delay(language=get_language(), *args, **kwargs)
    signer = TimestampSigner(key=request.session.session_key, sep=':')
    return signer.sign(b64_encode(result.id))


def find(request, token):
    try:
        signer = TimestampSigner(key=request.session.session_key, sep=':')
        id = b64_decode(signer.unsign(token, max_age=86400).encode('utf-8'))
        return AsyncResult(id)
    except:
        return None
