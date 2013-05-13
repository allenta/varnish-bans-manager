# -*- coding: utf-8 -*-

"""
:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from django.core.paginator import Paginator as BasePaginator
from django.core.paginator import Page as BasePage


class Paginator(BasePaginator):

    def __init__(self, page=1, expander=None, *args, **kwargs):
        super(Paginator, self).__init__(*args, **kwargs)
        self.expander = expander
        self.current_page = self.page(page)

    def page_range_slice(self):
        left = self.current_page.number - 2
        right = self.current_page.number + 2
        overflow_left = max(0, (-1 * left) + 1)
        overflow_right = max(0, right - self.num_pages)
        left = max(left - overflow_right, 1)
        right = min(right + overflow_left, self.num_pages)
        return range(left, right + 1)

    def page(self, number):
        """
        TODO: this method is a copy & paste of supperclass method due to
        the poor Django 1.5 implementation. On 1.6, a '_get_page' factory
        method is provided to overcome this.
        """
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return Page(self.object_list[bottom:top], number, self)


class Page(BasePage):
    def __init__(self, *args, **kwargs):
        super(Page, self).__init__(*args, **kwargs)
        if self.paginator.expander:
            self.object_list = [
                self.paginator.expander(item) for item in self.object_list
            ]
