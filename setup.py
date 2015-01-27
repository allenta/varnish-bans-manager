#!/usr/bin/env python
'''
Varnish Bans Manager
====================

Varnish Bans Manager (VBM) is a simple server and web UI designed to ease
management of bans in complex Varnish (https://www.varnish-cache.org)
deployments. Check out https://github.com/allenta/varnish-bans-manager
for a detailed description of VBM, extra documentation, some script samples,
and other useful information.

:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import sys
import os
from setuptools import setup, find_packages

if sys.version_info < (2, 7):
    raise Exception('VBM requires Python 2.7 or higher.')

with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')) as file:
    install_requires = file.read().splitlines()

extra = {}

if sys.version_info[0] == 3:
    extra['use_2to3'] = True

setup(
    name='varnish-bans-manager',
    version='0.6.1',
    author='Allenta Consulting',
    author_email='info@allenta.com',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/allenta/varnish-bans-manager',
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
    install_requires=install_requires,
    **extra
)
