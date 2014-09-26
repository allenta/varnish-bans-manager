# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django import forms
from varnish_bans_manager.core.models import Group


class EditForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ('name',)


class AddForm(EditForm):
    pass


class UpdateForm(EditForm):
    pass
