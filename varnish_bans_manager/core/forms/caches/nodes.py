# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django import forms
from django.utils.translation import ugettext_lazy as _
from varnish_bans_manager.core.models import Group, Node


class EditForm(forms.ModelForm):
    group = forms.ModelChoiceField(
        Group.objects.all().order_by('weight', 'name'),
        label=_('Group'),
        empty_label=_('- No group -'),
        required=False
    )

    class Meta:
        model = Node
        fields = ('name', 'host', 'port', 'secret', 'version', 'group',)
        widgets = {
            'host': forms.TextInput(attrs={'placeholder': _('Host name or IP address')}),
            'port': forms.TextInput(attrs={'placeholder': _('Port number')}),
        }


class AddForm(EditForm):
    pass


class UpdateForm(EditForm):
    def save(self, *args, **kwargs):
        # Reset node weight if it has been assigned to a different group.
        if 'group' in self.changed_data:
            self.instance.weight = 0
        super(UpdateForm, self).save(*args, **kwargs)
