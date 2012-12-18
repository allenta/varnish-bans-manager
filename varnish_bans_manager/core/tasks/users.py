# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from varnish_bans_manager.core.tasks.base import MonitoredTask
from varnish_bans_manager.filesystem import new_temporary_file
from varnish_bans_manager.core.helpers.csv import UnicodeWriter


class Delete(MonitoredTask):
    def irun(self, ids):
        deleted = 0
        errors = 0
        for index, id in enumerate(ids):
            try:
                User.objects.get(pk=id).delete()
                deleted = deleted + 1
            except:
                errors = errors + 1
            self.set_progress(index + 1, len(ids))
        return {
            'deleted': deleted,
            'errors': errors,
        }


class DownloadCSV(MonitoredTask):
    def irun(self, ids):
        exported = 0
        errors = 0
        file, url = new_temporary_file(_('users.csv'), mimetype='text/csv', prefix='users-download-csv')
        with file as f:
            writer = UnicodeWriter(f)
            writer.writerow([
                _('Identifier'),
                _('e-mail address'),
                _('First name'),
                _('Last name'),
            ])
            for index, id in enumerate(ids):
                try:
                    user = User.objects.get(pk=id)
                    writer.writerow([
                        str(user.id),
                        user.email,
                        user.first_name,
                        user.last_name,
                    ])
                    exported = exported + 1
                except:
                    errors = errors + 1
                self.set_progress(index + 1, len(ids))
        return {
            'exported': exported,
            'errors': errors,
            'url': url,
        }
