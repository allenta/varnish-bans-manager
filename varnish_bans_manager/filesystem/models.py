# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from PIL import Image
from cStringIO import StringIO
import os.path
import re
from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models.fields.files import FileField as BaseFileField
from django.db.models.fields.files import FieldFile as BaseFieldFile
from django.db.models.fields.files import ImageField as BaseImageField
from django.db.models.fields.files import ImageFieldFile as BaseImageFieldFile
from django.template.defaultfilters import filesizeformat
from django.core.urlresolvers import reverse
from django.forms import forms
from django.utils.translation import ugettext_lazy as _
from south.modelsinspector import add_introspection_rules
from varnish_bans_manager.filesystem.forms import ImageField as FormImageField
from varnish_bans_manager.filesystem import tasks


def _default_condition(request, instance):
    return (not request.user.is_anonymous()) and request.user.is_authenticated


def _default_attachment_filename(request, instance, field):
    return os.path.basename(field.path)


###############################################################################


def _set_common_options(self, kwargs):
    self.private = kwargs.pop('private', True)
    self.condition = kwargs.pop('condition', _default_condition)
    self.attachment = kwargs.pop('attachment', False)
    self.attachment_filename = kwargs.pop('attachment_filename', _default_attachment_filename)
    self.content_types = kwargs.pop('content_types', None)
    self.max_upload_size = kwargs.pop('max_upload_size', None)
    self.strong_caching = kwargs.pop('strong_caching', True)
    self.path_generator = kwargs.pop('path_generator', None)
    self.original_contents_generator = kwargs.pop('contents_generator', None)
    self.contents_generator = _wrapped_contents_generator(self.original_contents_generator) if self.original_contents_generator else None


def _clean_content_types_and_max_upload_size(self, data):
    try:
        file = data.file
        if self.content_types and not file.content_type in self.content_types:
            raise forms.ValidationError(_('File type not supported.'))
        elif self.max_upload_size and file._size > self.max_upload_size:
            raise forms.ValidationError(_('Please keep filesize under %(max)s. Current filesize %(current)s.') % {
                'max': filesizeformat(self.max_upload_size),
                'current': filesizeformat(file._size),
            })
    except IOError:
        raise forms.ValidationError(_('Invalid file.'))
    except AttributeError:
        pass
    return data


def _wrapped_upload_to(upload_to, private, path_generator):
    if path_generator:
        def internal_upload_to(instance, filename):
            return path_generator(instance)
        upload_to = internal_upload_to
    folder = 'private' if private else 'public'
    if isinstance(upload_to, str):
        return '%s/%s' % (folder, upload_to,)
    else:
        def wrapped(instance, filename):
            return '%s/%s' % (folder, upload_to(instance, filename))
        return wrapped


def _wrapped_contents_generator(contents_generator):
    def wrapped(field):
        buffer = contents_generator(field.instance)
        # Update instance (only file field!).
        filename = os.path.basename(field.field.path_generator(field.instance))
        field.save(filename, ContentFile(buffer.getvalue()), save=True)
        field.instance.save(force_update=True)  # TODO: add update_fields=['file'] on django 1.5.
    return wrapped


def _generate(field):
    if field.field.contents_generator:
        tasks.GenerateFileField.enqueue(
            field.instance._meta.app_label,
            field.instance._meta.object_name.lower(),
            field.instance.pk,
            field.field.name)


def _get_url(self):
    if not self and self.field.path_generator and self.field.contents_generator:
        path = self.field.path_generator(self.instance)
    else:
        path = self.path
    if self.field.private:
        return reverse('filesystem-private-download', kwargs={
            'app_label': self.instance._meta.app_label,
            'model_name': self.instance._meta.object_name.lower(),
            'object_id': self.instance.pk,
            'field_name': self.field.name,
            'filename': os.path.basename(path)
        })
    else:
        return reverse('filesystem-public-download', kwargs={
            'path': re.compile(r'^%s/?public/' % settings.MEDIA_ROOT).sub('', path)
        })


def _get_condition(self):
    return self.field.condition


def _get_attachment(self):
    return self.field.attachment


def _get_attachment_filename(self):
    return self.field.attachment_filename


def _get_strong_caching(self):
    return self.field.strong_caching


###############################################################################


class FieldFile(BaseFieldFile):
    ##
    ## PRIVATE FILE SYSTEM.
    ##

    def generate(self):
        _generate(self)

    url = property(_get_url)
    condition = property(_get_condition)
    attachment = property(_get_attachment)
    attachment_filename = property(_get_attachment_filename)
    strong_caching = property(_get_strong_caching)


class FileField(BaseFileField):
    attr_class = FieldFile

    def __init__(self, verbose_name=None, name=None, upload_to='', **kwargs):
        _set_common_options(self, kwargs)
        upload_to = _wrapped_upload_to(upload_to, self.private, self.path_generator)
        super(FileField, self).__init__(verbose_name, name, upload_to, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(FileField, self).clean(*args, **kwargs)
        return _clean_content_types_and_max_upload_size(self, data)


add_introspection_rules([(
        (FileField, ),
        [],
        {
            'private': ['private', {}],
            'attachment': ['attachment', {}],
            'content_types': ['content_types', {}],
            'max_upload_size': ['max_upload_size', {}],
            'strong_caching': ['strong_caching', {}],
            'path_generator': ['path_generator', {}],
            'contents_generator': ['original_contents_generator', {}],
            # These args accept a callable and therefore can
            # not be included in south introspection rules:
            # attachment_filename, condition, upload_to.
        },
    )], ["^varnish_bans_manager\.filesystem\.models\.FileField"])


###############################################################################


class ImageFieldFile(BaseImageFieldFile):
    ##
    ## PRIVATE FILE SYSTEM.
    ##

    def generate(self):
        _generate(self)

    url = property(_get_url)
    condition = property(_get_condition)
    attachment = property(_get_attachment)
    attachment_filename = property(_get_attachment_filename)
    strong_caching = property(_get_strong_caching)

    ##
    ## BOUNDING BOX.
    ##

    def save(self, name, content, save=True):
        if self.field.max_width and self.field.max_height:
            new_content = StringIO()
            content.file.seek(0)
            img = Image.open(content.file)
            img.thumbnail((
                self.field.max_width,
                self.field.max_height
                ), Image.ANTIALIAS)
            img.save(new_content, format=img.format)
            new_content = ContentFile(new_content.getvalue())
            super(ImageFieldFile, self).save(name, new_content, save)
        else:
            super(ImageFieldFile, self).save(name, content, save)


class ImageField(BaseImageField):
    attr_class = ImageFieldFile

    def __init__(self, verbose_name=None, name=None, upload_to='', max_width=None, max_height=None, **kwargs):
        _set_common_options(self, kwargs)
        upload_to = _wrapped_upload_to(upload_to, self.private, self.path_generator)
        self.max_width = max_width
        self.max_height = max_height
        super(ImageField, self).__init__(verbose_name, name, upload_to=upload_to, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(ImageField, self).clean(*args, **kwargs)
        return _clean_content_types_and_max_upload_size(self, data)

    def formfield(self, **kwargs):
        defaults = {'form_class': FormImageField}
        defaults.update(kwargs)
        return super(ImageField, self).formfield(**defaults)

    def pre_save(self, model_instance, add):
        file = super(ImageField, self).pre_save(model_instance, add)
        if add:
            file.generate()
        return file


add_introspection_rules([(
        (ImageField, ),
        [],
        {
            'private': ['private', {}],
            'attachment': ['attachment', {}],
            'content_types': ['content_types', {}],
            'max_upload_size': ['max_upload_size', {}],
            'strong_caching': ['strong_caching', {}],
            'path_generator': ['path_generator', {}],
            'contents_generator': ['original_contents_generator', {}],
            'max_width': ['max_width', {}],
            'max_height': ['max_height', {}],
            # These args accept a callable and therefore can
            # not be included in south introspection rules:
            # attachment_filename, condition, upload_to.
        },
    )], ["^varnish_bans_manager\.filesystem\.models\.ImageField"])
