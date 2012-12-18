# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.dispatch import Signal

# Arguments:
#   - sender: HttpRequest()
#   - type: int() (@see varnish_bans_manager.core.models.redirection.TYPE)
#   - name: None | str()
#   - code: None | varnish_bans_manager.core.code.models.Code()
#   - asset: None | varnish_bans_manager.core.code.models.Asset()
redirection = Signal(providing_args=['type', 'name', 'code', 'asset'])
