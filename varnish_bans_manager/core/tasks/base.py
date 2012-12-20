# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.utils import translation
from django.core.cache import cache
from celery import Task
from celery.signals import task_prerun
from varnish_bans_manager import core


@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, *args, **kwargs):
    core.initialize()


class MonitoredTask(Task):
    """
    Depending on the specific task, subclasses can, for example,
    implement cleanup logic overriding on_failure, on_retry, etc.
    methods.
    """
    abstract = True

    def run(self, *args, **kwargs):
        # Extract & remove special 'callback' argument.
        if 'callback' in kwargs:
            callback = kwargs['callback']
            del kwargs['callback']
        # Extract & remove special 'language' argument.
        language = 'en'
        if 'language' in kwargs:
            language = kwargs['language']
            del kwargs['language']
        # Switch language.
        prev_language = translation.get_language()
        translation.activate(language)
        # Execute task & restore language.
        try:
            result = self.irun(*args, **kwargs)
        finally:
            translation.activate(prev_language)
        # Encapsulate result.
        return {
            'id': self.request.id,
            'callback': callback,
            'result': result,
        }

    def set_progress(self, count, total):
        self.update_state(state='PROGRESS', meta={
            'value': int((float(min(count, total)) / float(total)) * 100),
        })

    def irun(self, *args, **kwargs):
        raise NotImplementedError('Please implement this method')


class SingleInstanceTask(Task):
    """
    Child classes are reponsible to complete as much work as possible and
    finish before lock expiration. Once expired, worker will be killed.

    See:
        - http://ask.github.com/celery/cookbook/tasks.html
        - http://stackoverflow.com/questions/4095940/running-unique-tasks-with-celery.
    """
    abstract = True

    def __init__(self, *args, **kwargs):
        # Set default time limits if not provided.
        self.soft_time_limit = self.soft_time_limit if self.soft_time_limit else 300
        self.time_limit = None

        # Complete instantiation.
        super(SingleInstanceTask, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        if self._acquire_lock():
            return self.irun(*args, **kwargs)
        else:
            raise SingleInstanceTaskLocked()

    def irun(self, *args, **kwargs):
        raise NotImplementedError('Please implement this method')

    def on_success(self, retval, task_id, *args, **kwargs):
        self._release_lock()

    def on_failure(self, exc, task_id, *args, **kwargs):
        if not isinstance(exc, SingleInstanceTaskLocked):
            self._release_lock()

    def _acquire_lock(self):
        return cache.add(self._lock_id(), 1, self.soft_time_limit)

    def _release_lock(self):
        return cache.delete(self._lock_id())

    def _lock_id(self):
        return "celery-single-instance:lock:%s" % self.name


class SingleInstanceTaskLocked(Exception):
    pass
