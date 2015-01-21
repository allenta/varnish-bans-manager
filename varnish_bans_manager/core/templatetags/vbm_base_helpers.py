# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import re
import json
from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.http import HttpRequest

register = template.Library()

###############################################################################


@register.simple_tag
def active(value, pattern):
    '''
    See http://gnuvince.wordpress.com/2007/09/14/a-django-template-tag-for-the-current-active-page/.
    See http://110j.wordpress.com/2009/01/25/django-template-tag-for-active-class/.

    '''
    if isinstance(value, HttpRequest):
        prefix = '/%s' % value.LANGUAGE_CODE
        value = value.path_info
        value = value[len(prefix):] if value.startswith(prefix) else value
    if re.search(pattern, value):
        return 'active'
    return ''


###############################################################################


@register.simple_tag
def hidden(value, pattern):
    if isinstance(value, HttpRequest):
        prefix = '/%s' % value.LANGUAGE_CODE
        value = value.path_info
        value = value[len(prefix):] if value.startswith(prefix) else value
    if not re.search(pattern, value):
        return 'display: none;'
    return ''


###############################################################################


@register.filter(is_safe=True)
@stringfilter
def classify(value):
    return re.sub(r'_', '-', value)

###############################################################################


@register.filter(is_safe=True)
def jsonify(value):
    return json.dumps(value)


###############################################################################


@register.filter
def key(dict, key):
    try:
        return dict[key]
    except:
        return settings.TEMPLATE_STRING_IF_INVALID


###############################################################################


@register.simple_tag
def settings_value(name, encoding='raw'):
    '''
    Access some raw settings value.

    '''
    try:
        value = getattr(settings, name)
        return json.dumps(value) if encoding == 'json' else value
    except AttributeError:
        return ''


###############################################################################


@register.tag
def capture(parser, token):
    '''
    Capture contents of block into context.

    Use case: variable accessing based on current variable values.

    {% capture foo %}{{ foo.value }}-suffix{% endcapture %}
    {% if foo in bar %}{% endif %}

    '''
    nodelist = parser.parse(('endcapture',))
    parser.delete_first_token()
    varname = token.contents.split()[1]
    return CaptureNode(nodelist, varname)


class CaptureNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        context[self.varname] = self.nodelist.render(context)
        return ''
