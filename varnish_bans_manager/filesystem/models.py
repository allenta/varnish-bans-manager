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


def _wrapped_contents_generator(contents_generator):
    def wrapped(field):
        buffer = contents_generator(field.instance)
        # Update instance (only file field!).
        filename = os.path.basename(field.field.path_generator(field.instance))
        field.save(filename, ContentFile(buffer.getvalue()), save=True)
        field.instance.save(force_update=True)
    return wrapped


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


###############################################################################


class FieldFileMixin(BaseFieldFile):
    """
    Mixin that adds support for public/private filesystems and file
    contents auto-generation, as well as some useful properties.
    """
    @property
    def attachment(self):
        return self.field.attachment

    @property
    def attachment_filename(self):
        return self.field.attachment_filename

    @property
    def condition(self):
        return self.field.condition

    @property
    def strong_caching(self):
        return self.field.strong_caching

    @property
    def url(self):
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

    def generate(self):
        if self.field.contents_generator:
            tasks.GenerateFileField.enqueue(
                self.instance._meta.app_label,
                self.instance._meta.object_name.lower(),
                self.instance.pk,
                self.field.name)


class FileFieldMixin(BaseFileField):
    default_error_messages = {
        'file_invalid': _('Invalid file.'),
        'file_type_not_supported': _('File type not supported.'),
        'file_too_big': _('Please keep filesize under %(max)s. Current filesize %(current)s.')
    }

    def __init__(self, **kwargs):
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
        kwargs['upload_to'] = _wrapped_upload_to(kwargs.pop('upload_to', ''), self.private, self.path_generator)
        super(FileFieldMixin, self).__init__(**kwargs)

    def clean(self, *args, **kwargs):
        data = super(FileFieldMixin, self).clean(*args, **kwargs)
        try:
            if self.content_types and not data.file.content_type in self.content_types:
                raise forms.ValidationError(self.error_messages['file_type_not_supported'])
            elif self.max_upload_size and data.file._size > self.max_upload_size:
                raise forms.ValidationError(self.error_messages['file_too_big'] % {'max': filesizeformat(self.max_upload_size), 'current': filesizeformat(data.file._size)})
        except IOError:
            raise forms.ValidationError(self.error_messages['file_invalid'])
        except AttributeError:
            pass
        return data

    def pre_save(self, model_instance, add):
        file = super(FileFieldMixin, self).pre_save(model_instance, add)
        # Launch file generation (for self-generated contents).
        if add:
            file.generate()
        return file


###############################################################################


class FieldFile(FieldFileMixin, BaseFieldFile):
    pass


class FileField(FileFieldMixin, BaseFileField):
    attr_class = FieldFile


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


class ImageFieldFile(FieldFileMixin, BaseImageFieldFile):
    """
    Adds our custom mixin as well as support for resizing the image if it
    surpases the bounding box defined by the field.
    """
    def save(self, name, content, save=True):
        # Resize to the bounding box if necessary.
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


class ImageField(FileFieldMixin, BaseImageField):
    attr_class = ImageFieldFile

    def __init__(self, verbose_name=None, name=None, width_field=None,
            height_field=None, max_width=None, max_height=None, **kwargs):
        # Extract bounding box definition.
        self.max_width = max_width
        self.max_height = max_height
        super(ImageField, self).__init__(
            verbose_name=verbose_name, name=name, width_field=width_field,
            height_field=height_field, **kwargs)

    def formfield(self, **kwargs):
        # Set a custom FormImageField as default form field.
        kwargs.setdefault('form_class', FormImageField)
        return super(ImageField, self).formfield(**kwargs)


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
