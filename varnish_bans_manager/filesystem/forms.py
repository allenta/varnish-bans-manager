# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
from django.forms import ImageField as BaseImageField
from django.forms.widgets import FileInput, CheckboxInput
from django.utils.safestring import mark_safe


class ImageFileInput(FileInput):
    def _clear_checkbox_name(self, name):
        '''
        Given the name of the file input, return the name of the clear hidden
        input.

        '''
        return name + '-clear'

    def render(self, name, value, attrs=None):
        output = []

        # Base content.
        output.append(super(ImageFileInput, self).render(name, value, attrs))

        if value and hasattr(value, "url"):
            # Add clear checkbox input.
            output.append(
                CheckboxInput().render(self._clear_checkbox_name(name), False, attrs={
                    'class': 'image-file-input-clear'
                }))

            # Add image preview with delete icon.
            output.append(('<ul class="thumbnails image-file-input-preview">'
                           '  <li>'
                           '    <a target="_blank" href="%s" class="thumbnail">'
                           '      <img src="%s" />'
                           '    </a>'
                           '    <a href="#" class="close image-file-input-delete">&times;</a>'
                           '  </li>'
                           '</ul>'
                           % (value.url, value.url)))

        # Render.
        return mark_safe('<div class="image-file-input">' + u''.join(output) + '</div>')

    def value_from_datadict(self, data, files, name):
        upload = super(ImageFileInput, self).value_from_datadict(data, files, name)

        # If no upload has been done and the clear checkbox has been checked,
        # clear the value.
        if not upload and CheckboxInput().value_from_datadict(
            data, files, self._clear_checkbox_name(name)):
            # False signals to clear any existing value, as opposed to just None.
            return False

        return upload


class ImageField(BaseImageField):
    widget = ImageFileInput
