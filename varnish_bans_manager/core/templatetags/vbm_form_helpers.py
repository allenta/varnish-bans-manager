# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
import re
from django import template

register = template.Library()

###############################################################################


@register.simple_tag
def form_errors(form):
    result = ''
    for error in form.non_field_errors():
        result = result + (
            '<div class="alert alert-error">'
            '  <a class="close" data-dismiss="alert">&times;</a>%s'
            '</div>') % error
    return result

###############################################################################


@register.simple_tag
def form_ferrors(field, mode='block'):
    result = ''
    for error in field.errors:
        result = result + \
            '<span class="help-%s">%s</span>' % (mode, error)
    return result

###############################################################################


@register.tag
def form_cgroup(parser, token):
    nodelist = parser.parse(('endform_cgroup',))
    parser.delete_first_token()
    p = re.compile(r'''^form_cgroup (?P<field_variables>[^"']*)(?: (?:["'](?P<classes>.*)["']))?$''')
    m = p.search(token.contents)
    field_variables = m.group('field_variables').split()
    classes = m.group('classes')
    return CaptureNode(nodelist, field_variables, classes)


class CaptureNode(template.Node):
    def __init__(self, nodelist, field_variables, classes):
        self.nodelist = nodelist
        self.field_variables = []
        for field_variable in field_variables:
            self.field_variables.append(template.Variable(field_variable))
        self.classes = classes

    def render(self, context):
        error = False
        required = False
        for field_variable in self.field_variables:
            field = field_variable.resolve(context)
            error = error or len(field.errors) > 0
            required = required or field.field.required
        return (
            '<div class="control-group %s %s %s">'
            '%s'
            '</div>') % (
                'error' if error else '',
                'required' if required else '',
                self.classes,
                self.nodelist.render(context))
