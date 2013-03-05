# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
import simplejson as json
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.signals import post_delete
from django.db.utils import DatabaseError
from django.utils.translation import ugettext as _
from django.forms.widgets import HiddenInput
from south.modelsinspector import add_introspection_rules


class RevisionedQuerySet(models.query.QuerySet):
    """
    Makes sure revision has not been changed since data was last read from DB.
    """
    class RecordModifiedError(DatabaseError):
        pass

    def __init__(self, model=None, query=None, using=None):
        super(RevisionedQuerySet, self).__init__(model=model, query=query, using=using)
        self._revision_field = getattr(model, '_revision_field', None)

    def _update(self, values):
        if self._revision_field:
            # Get current revision value and increment it in the list of values to update.
            current_revision = None
            for i in range(0, len(values)):
                (field, model, value) = values[i]
                if field.attname == self._revision_field:
                    current_revision = value
                    values[i] = (field, model, F(self._revision_field) + 1)
            if current_revision is not None:
                # Ensure the revision value has not been changed and go on with the update.
                self.query.add_q(Q(**{self._revision_field: current_revision}))
                rows = super(RevisionedQuerySet, self)._update(values)
                # If no rows have been updated, revision number must have changed: raise an error.
                if rows == 0:
                    raise self.RecordModifiedError()
                return rows
            else:
                # No revision value has ben provided: raise an error.
                raise ValueError("Can't update this model without providing a revision value")
        else:
            return super(RevisionedQuerySet, self)._update(values)


class QuerySet(RevisionedQuerySet, models.query.QuerySet):
    """
    Custom QuerySet class for our models. Main added functionalities are:

      - RevisionField automatic checks during updates.

    """
    pass

##
## There are some subclasses of models.query.QuerySet (e.g. EmptyQuerySet)
## that are instanced by models.query.QuerySet methods (e.g. none()), resulting
## in QuerySets not extending our base QuerySet ==> dinamically change
## base of all those subclasses to our QuerySet implementation.
##

for cls in models.query.QuerySet.__subclasses__():
    if cls not in (QuerySet, RevisionedQuerySet):
        bases = list(cls.__bases__)
        bases[bases.index(models.query.QuerySet)] = QuerySet
        cls.__bases__ = tuple(bases)


###############################################################################


class Manager(models.Manager):
    """
    Custom Manager class for our models.
    """
    use_for_related_fields = True

    def get_query_set(self):
        return QuerySet(self.model, using=self._db)


###############################################################################


class Options(object):
    """
    Custom meta options class for our models.
    """
    _valid_options = ('trackable_field_names',)

    def __init__(self, cls, meta):
        # Extract values for all options.
        for attr_name in self._valid_options:
            setattr(self, attr_name, meta.__dict__.get(attr_name, getattr(meta, attr_name)))

        # Autocomplete trackable fields option with all
        # FileFields present in the class and build up a
        # list of available FileFields.
        self.file_field_names = []
        for field in cls._meta.fields:
            if isinstance(field, models.FileField):
                self.file_field_names.append(field.name)
                if field.name not in self.trackable_field_names:
                    self.trackable_field_names += (field.name,)


class ModelBase(models.base.ModelBase):
    """
    Custom metaclass.

    This metaclass parses custom options in VBMMeta and makes
    them available under the class attribute _vbm_meta. It has
    a similar behaviour than that of the Meta class offered
    by Django model classes (inheritance, etc.) but encapsulates
    our own custom options for all our models.
    """
    def __init__(cls, name, bases, attrs):
        super(ModelBase, cls).__init__(name, bases, attrs)
        vbm_meta = attrs.pop('VBMMeta', getattr(cls, 'VBMMeta'))
        cls.add_to_class('_vbm_meta', Options(cls, vbm_meta))
        # Connect to post_delete signal to automatically delete
        # FileFields if any is present in the model class. Instances
        # not allways get removed through a call to the delete method
        # (e.g. on delete cascade through relations), so this must be
        # done using Django's post_delete signal.
        if cls._vbm_meta.file_field_names:
            post_delete.connect(ModelBase.remove_files, sender=cls)
        # Set some useful attributes.
        cls.verbose_name = cls._meta.verbose_name
        cls.verbose_name_plural = cls._meta.verbose_name_plural

    @classmethod
    def remove_files(cls, sender, instance, **kwargs):
        for file_field_name in instance._vbm_meta.file_field_names:
            file = getattr(instance, file_field_name)
            if file:
                file.delete(save=False)


###############################################################################


class Model(models.Model):
    """
    Custom base model class.

    Added functionality:
        - Keep track of old values for fields coming from the
          persistence layer (only for those present in
          VBMMeta.trackable_field_names). This values will be
          accesible using the get_previous method.
        - Automatic file deletion on updates and deletes. For
          updates to work, FileField fields will always be
          automatically added to VBMMeta.trackable_field_names.
          See Options.__init__
    """
    __metaclass__ = ModelBase

    objects = Manager()

    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(*args, **kwargs)
        # Initialize old fields.
        self._refresh_old_fields()

    def get_previous(self, field):
        return self._old_fields.get(field, None)

    def save(self, *args, **kwargs):
        super(Model, self).save(*args, **kwargs)
        # Remove any old file no longer pointed by this instance.
        for file_field_name in self._vbm_meta.file_field_names:
            old_file = self.get_previous(file_field_name)
            new_file = getattr(self, file_field_name)
            if old_file and old_file != new_file:
                old_file.delete(save=False)
        # Refresh old fields.
        self._refresh_old_fields()

    def _reduced_state_black_list(self):
        # Define which custom attributes will not be used when pickling
        # the instance.
        return ['_old_fields']

    def _complete_state(self):
        # Reassign values for those attributes that were not pickled for
        # being in the reduced_state_black_list.
        self._refresh_old_fields()

    def _refresh_old_fields(self):
        self._old_fields = {}
        if self.id:
            for field in self._vbm_meta.trackable_field_names:
                self._old_fields[field] = getattr(self, field)

    def __reduce__(self):
        # Django doesn't call __getstate__ under certain circumstances (e.g.
        # under the presence of deferred attributes), so we need to modify
        # the current instance's __dict__ so that nothing extra gets pickled.
        # It's the only thing that's going to work for sure.
        full_dict = self.__dict__.copy()
        for attr in self._reduced_state_black_list():
            if attr in self.__dict__:
                del self.__dict__[attr]
        result = super(Model, self).__reduce__()
        self.__dict__ = full_dict
        return result

    def __setstate__(self, state):
        self.__dict__.update(state)
        self._complete_state()

    class Meta:
        app_label = 'core'
        abstract = True

    class VBMMeta:
        """
        Default values for all custom meta options.
        """
        trackable_field_names = ()


###############################################################################


class RevisionField(models.IntegerField):
    """
    Revision Field that returns a "unique" revision number for the record.
    """
    default_error_messages = {
        'modified': _(
            'This item has been updated by other user while you were editing '
            'it. Please reload the page and redo all necessary changes so no '
            'edition gets lost.')
    }

    def __init__(self, *args, **kwargs):
        defaults = {'default': 0}
        defaults.update(kwargs)
        super(RevisionField, self).__init__(*args, **defaults)

    def formfield(self, **kwargs):
        defaults = {'widget': HiddenInput}
        defaults.update(kwargs)
        return super(RevisionField, self).formfield(**defaults)

    def contribute_to_class(self, cls, name):
        super(RevisionField, self).contribute_to_class(cls, name)
        if getattr(cls, '_revision_field', None) is None:
            cls.clean = self._clean_with_revision_method_factory(cls.clean, name)
            cls._revision_field = name

    def _clean_with_revision_method_factory(self, original_clean, revision_field):
        def clean_with_revision(self, *args, **kwargs):
            # Check the record's revision number has not been modified since last read.
            if self.pk:
                current_revision = getattr(self, revision_field)
                filters = {'pk': self.pk, revision_field: current_revision}
                if not self.__class__.objects.filter(**filters).exists():
                    raise ValidationError(self.error_messages['modified'])
            # Continue with all other cleaning.
            return original_clean(self, *args, **kwargs)
        return clean_with_revision


add_introspection_rules([], ["^varnish_bans_manager\.core\.models\.base\.RevisionField"])


###############################################################################


class JSONField(models.Field):
    """
    Simple JSON field. See:

        - https://github.com/bradjasper/django-jsonfield
    """
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, basestring):
            try:
                return json.loads(value)
            except ValueError:
                pass
        return value

    def get_prep_value(self, value):
        if isinstance(value, basestring):
            return value
        if self.null and value is None:
            return None
        return json.dumps(value)

    def get_internal_type(self):
        return 'TextField'


add_introspection_rules([], ["^varnish_bans_manager\.core\.models\.base\.JSONField"])
