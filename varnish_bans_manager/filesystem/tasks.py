# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
import os
from django.db.models import get_model
from django.core.cache import cache
from celery import Task


class GenerateFileField(Task):
    ignore_result = True

    @classmethod
    def enqueue(cls, app_label, model_name, object_id, field_name, timeout=1200):
        # Generate custom task id.
        task_id = 'filesystem-file-generator-task:%s:%s:%s:%s' % (app_label, model_name, object_id, field_name)

        # Check if the task is already enqueued/running. Celery does
        # not provide any general support to check if a task id has
        # already been enqueued => use cache to implement that.
        if cache.add(cls._cache_key(task_id), 1, timeout=timeout):
            cls().apply_async(
                args=[app_label, model_name, object_id, field_name],
                task_id=task_id)

    def run(self, app_label, model_name, object_id, field_name):
        model = get_model(app_label, model_name)
        if model:
            try:
                instance = model.objects.get(pk=object_id)
                if hasattr(instance, field_name):
                    field = getattr(instance, field_name)
                    try:
                        # Remove previous file.
                        os.remove(field.path)
                    except:
                        # Ignore.
                        pass
                    finally:
                        # Generate new file.
                        field.field.contents_generator(field)
            except model.DoesNotExist:
                pass

    def on_success(self, retval, task_id, *args, **kwargs):
        cache.delete(GenerateFileField._cache_key(task_id))

    def on_failure(self, exc, task_id, *args, **kwargs):
        cache.delete(GenerateFileField._cache_key(task_id))

    @classmethod
    def _cache_key(cls, task_id):
        return 'celery:' + task_id


class CleanupTemporary(Task):
    ignore_result = True

    def run(self, filename):
        try:
            os.remove(filename)
        except Exception:
            pass
