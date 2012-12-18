# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.core.paginator import Paginator as BasePaginator


class Paginator(BasePaginator):

    def __init__(self, page=1, *args, **kwargs):
        super(Paginator, self).__init__(*args, **kwargs)
        self.current_page = self.page(page)

    def page_range_slice(self):
        left = self.current_page.number - 2
        right = self.current_page.number + 2
        overflow_left = max(0, (-1 * left) + 1)
        overflow_right = max(0, right - self.num_pages)
        left = max(left - overflow_right, 1)
        right = min(right + overflow_left, self.num_pages)
        return range(left, right + 1)
