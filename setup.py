#!/usr/bin/env python
"""
Varnish Bans Manager
====================

Varnish Bans Manager (VBM) is a simple server and web UI designed to ease
management of bans in complex Varnish (https://www.varnish-cache.org)
deployments. Check out https://github.com/dot2code/varnish-bans-manager
for a detailed description of VBM, extra documentation, some script samples,
and other useful information.

:copyright: (c) 2012 by the dot2code Team, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
"""

from __future__ import absolute_import
from setuptools import setup, find_packages

setup(
    name='varnish-bans-manager',
    version='0.4',
    author='dot2code Technologies',
    author_email='info@dot2code.com',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/dot2code/varnish-bans-manager',
    description='Varnish Bans Manager.',
    long_description=__doc__,
    license='GPL',
    entry_points={
        'console_scripts': [
            'varnish-bans-manager = varnish_bans_manager.runner:main',
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        "django >= 1.4.3",
        "django-celery >= 3.0.11",
        "django-mediagenerator >= 1.11",
        "django-templated-email >= 0.4.7",
        "gunicorn >= 0.14.6",
        "eventlet >= 0.9.17",
        "simplejson >= 2.1.6",
        "path.py >= 2.4.1",
        "ordereddict >= 1.1",
        "pytz",
        "pil",
    ],
)
