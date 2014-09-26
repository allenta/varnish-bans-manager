#!/usr/bin/env python

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import os
import sys
import random
import string
from path import path


def default_config():
    return '''
# HTTP server settings. All Gunicorn server settings are supported. Check
# out Gunicorn documentation (http://docs.gunicorn.org/en/latest/configure.html)
# for further details and for a full list of options. Note that 'debug' and
# 'secure_scheme_headers' Gunicorn settings will always be overriden
# by VBM internal settings.
[http]
base_url: http://varnish-bans-manager.domain.com
bind: 0.0.0.0:9000
worker_class: eventlet
forwarded_allow_ips: 127.0.0.1
x_forwarded_for_header: X-FORWARDED-FOR

# SSL settings. Enable SSL only for proxied VBM deployments.
[ssl]
enabled: false
secure_proxy_ssl_header_name: HTTP_X_FORWARDED_PROTO
secure_proxy_ssl_header_value: https

# Relational database settings. Check out Django documentation for
# more information about alternative database engines (PostgreSQL,
# Oracle, etc.).
[database]
engine: django.db.backends.mysql
name: varnish_bans_manager
user: bob
password: s3cr3t
host: 127.0.0.1
port: 3306

# Filesytem settings. VBM internally generated files and user
# uploaded files will be stored in some folder inside the
# 'root' path.
#
# Publicly accessible files will be stored under 'root'/public/,
# so, when using a reverse proxy, remember to setup it to serve
# those files directly.
#
# Files under 'root'/private/ and 'root'/temporary/ require some
# app-level access control checks. Never serve those files
# directly from the reverse proxy.
#
# Depending on what reverse proxy you are using, you can boost
# performance using the adequate sendfile backend:
#
#      nginx: varnish_bans_manager.filesystem.sendfile_backends.nginx
#      Apache: varnish_bans_manager.filesystem.sendfile_backends.xsendfile
[filesystem]
root: /var/www/varnish-bans-manager/files/
sendfile: varnish_bans_manager.filesystem.sendfile_backends.stream

# Mailing settings.
[email]
host: 127.0.0.1
port: 25
user:
password:
tls: false
from: noreply@varnish-bans-manager.domain.com
subject_prefix: [VBM]
contact: info@varnish-bans-manager.domain.com
notifications: you@varnish-bans-manager.domain.com

# i18n settings. English (en) and Spanish (es) are the available
# languages at the moment.
[i18n]
default: en

# Misc settings.
[misc]
# Service timezone.
timezone: Europe/Madrid

# Internal secret key.
secret_key: %(secret_key)s

# For development purposes only. Always keep this value to false, or,
# even better, remove it from the configuration file.
development: false
    ''' % {
        'secret_key': ''.join(
            random.choice(string.ascii_letters + string.digits) for i in range(64))
    }


def main():
    if len(sys.argv) == 1:
        sys.exit('Usage: varnish-bans-manager [command] [options]')
    elif len(sys.argv) == 2 and sys.argv[1] == 'init':
        print default_config()
        sys.exit()
    else:
        sys.path.append(str(path(__file__).abspath().dirname().dirname()))
        os.environ['DJANGO_SETTINGS_MODULE'] = 'varnish_bans_manager.settings'
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
