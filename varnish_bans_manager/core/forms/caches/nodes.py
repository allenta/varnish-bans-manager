# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django import forms
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.core.models import Group, Node


class AddForm(forms.ModelForm):
    group = forms.ModelChoiceField(
        Group.objects.all(),
        label=_('Group'),
        empty_label=_('- No group -')
    )

    class Meta():
        model = Node
        fields = ('name', 'host', 'port', 'secret', 'version', 'group',)
        widgets = {
            'host': forms.TextInput(attrs={'placeholder': 'Host name or IP address'}),
            'port': forms.TextInput(attrs={'placeholder': 'Port number'}),
        }
