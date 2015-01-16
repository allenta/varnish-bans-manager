# -*- coding: utf-8 -*-

'''
:copyright: (c) 2012 by Allenta Consulting, see AUTHORS.txt for more details.
:license: GPL, see LICENSE.txt for more details.
'''

from __future__ import absolute_import
import os
import sys
import simplejson
from cStringIO import StringIO
import ConfigParser
import getpass
from path import path
from varnish_bans_manager.runner import default_config

###############################################################################
## INITIALIZATIONS.
###############################################################################

ROOT = path(__file__).abspath().dirname()

# This is defined here as a do-nothing function because we can't import
# django.utils.translation -- that module depends on the settings.
ugettext = lambda s: s

# Django 1.7 deprecates the django.utils.simplejson module but the current last
# version for django-mediagenerator (1.11) still uses it. Until this package is
# updated, this hack can be used.
sys.modules['django.utils.simplejson'] = simplejson

###############################################################################
## USER CONFIG.
###############################################################################

_config_filename = os.environ.get(
    'VARNISH_BANS_MANAGER_CONF', '/etc/varnish-bans-manager.conf')
_config = ConfigParser.ConfigParser()
_config.readfp(StringIO(default_config()))
try:
    _config.read([_config_filename])
except:
    sys.exit("Error: failed to load configuration file '%s'." % _config_filename)

###############################################################################
## ENVIRONMENT & DEBUG.
###############################################################################

if _config.getboolean('misc', 'development'):
    ENVIRONMENT = 'development'
    USERNAME = getpass.getuser()
    IS_PRODUCTION = False
    DEBUG = True
    USER_SUFFIX = '-' + USERNAME
else:
    ENVIRONMENT = 'production'
    USERNAME = None
    IS_PRODUCTION = True
    DEBUG = False
    USER_SUFFIX = ''

###############################################################################
## MONKEY PATCHES & IMPORTS.
###############################################################################

from varnish_bans_manager.core.patches.base_management_command import *

from django.contrib.messages import constants as message_constants
import djcelery
from celery.schedules import crontab

###############################################################################
## DB.
###############################################################################

DATABASES = {
    'default': {
        'ENGINE': _config.get('database', 'engine'),
        'NAME': _config.get('database', 'name'),
        'USER': _config.get('database', 'user'),
        'PASSWORD': _config.get('database', 'password'),
        'HOST': _config.get('database', 'host'),
        'PORT': _config.getint('database', 'port'),
    }
}

###############################################################################
## CACHES.
###############################################################################

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache',
    }
}

###############################################################################
## SSL.
###############################################################################

HTTPS_ENABLED = _config.getboolean('ssl', 'enabled')
SECURE_PROXY_SSL_HEADER = (
    _config.get('ssl', 'secure_proxy_ssl_header_name'),
    _config.get('ssl', 'secure_proxy_ssl_header_value'),
)

###############################################################################
## TEMPLATES.
###############################################################################

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_DIRS = (
    ROOT / 'templates',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.csrf',
    'django.core.context_processors.request',
    'varnish_bans_manager.core.context_processors.messages',
    'varnish_bans_manager.core.context_processors.page_id',
    'varnish_bans_manager.core.context_processors.is_production',
)

###############################################################################
## MIDDLEWARE.
###############################################################################

MIDDLEWARE_CLASSES = (
    # GZip.
    'django.middleware.gzip.GZipMiddleware',

    # Timer.
    'varnish_bans_manager.core.middleware.TimerMiddleware',

    # Debug.
    'varnish_bans_manager.core.middleware.DebugMiddleware',

    # Customizations.
    'varnish_bans_manager.core.middleware.CustomizationsMiddleware',

    # Login redirection.
    'varnish_bans_manager.core.middleware.SecurityMiddleware',

    # HTTPS redirection.
    'varnish_bans_manager.core.middleware.SSLRedirectMiddleware',

    # See http://www.allbuttonspressed.com/projects/django-mediagenerator.
    'mediagenerator.middleware.MediaMiddleware',

    # Base.
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # Custom messaging.
    'django.contrib.messages.middleware.MessageMiddleware',
    'varnish_bans_manager.core.middleware.MessagingMiddleware',

    # Page id.
    'varnish_bans_manager.core.middleware.PageIdMiddleware',

    # Version.
    'varnish_bans_manager.core.middleware.VersionMiddleware',

    # AJAX redirect.
    'varnish_bans_manager.core.middleware.AjaxRedirectMiddleware',
)

###############################################################################
## APPS.
###############################################################################

INSTALLED_APPS = (
    # Base.
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',

    # See http://gunicorn.org.
    'gunicorn',

    # See http://www.allbuttonspressed.com/projects/django-mediagenerator.
    # See http://www.djangopackages.com/grids/g/asset-managers/.
    'mediagenerator',

    # See https://github.com/bradwhittington/django-templated-email.
    'templated_email',

    # See http://celeryproject.org.
    'djcelery',
    'kombu.transport.django',

    # VBM.
    'varnish_bans_manager.filesystem',
    'varnish_bans_manager.core',
)

###############################################################################
## SESSIONS & CSRF.
###############################################################################

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = 'sid'
SESSION_COOKIE_SECURE = HTTPS_ENABLED
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = False

CSRF_COOKIE_NAME = 'csrf'
CSRF_COOKIE_SECURE = HTTPS_ENABLED

###############################################################################
## AUTHENTICATION.
###############################################################################

AUTH_USER_MODEL = 'core.User'

LOGIN_URL = 'user-login'
LOGOUT_URL = 'user-logout'
LOGIN_REDIRECT_URL = 'home'

PASSWORD_RESET_TIMEOUT_DAYS = 3

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.UnsaltedMD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher',
)

###############################################################################
## MESSAGES.
###############################################################################

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
MESSAGE_LEVEL = message_constants.INFO

###############################################################################
## FILES.
###############################################################################

# Absolute filesystem path to the directory that will hold user-uploaded files.
MEDIA_ROOT = _config.get('filesystem', 'root')
# URL that handles the media served from MEDIA_ROOT.
MEDIA_URL = '/files/'

DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# List of upload handler classes to be applied in order.
FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

# Maximum size, in bytes, of a request before it will be streamed to the
# file system instead of into memory.
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # i.e. 2.5 MB

# Directory in which upload streamed files will be temporarily saved. A value of
# `None` will make Django use the operating system's default temporary directory
FILE_UPLOAD_TEMP_DIR = None

# The numeric mode to set newly-uploaded files to. The value should be a mode
# you'd pass directly to os.chmod.
FILE_UPLOAD_PERMISSIONS = 0644

# Filesystem sendfile implementation.
FILESYSTEM_SENDFILE_BACKEND = _config.get('filesystem', 'sendfile')
FILESYSTEM_SENDFILE_URL = '/sendfile'

###############################################################################
## MEDIAGENERATOR (http://www.allbuttonspressed.com/projects/django-mediagenerator).
###############################################################################

MEDIA_DEV_MODE = not IS_PRODUCTION
DEV_MEDIA_URL = '/dev/assets/'
PRODUCTION_MEDIA_URL = '/assets/'

GLOBAL_MEDIA_DIRS = (
    ROOT / 'static',
)

GENERATED_MEDIA_DIR = ROOT / 'assets'
GENERATED_MEDIA_NAMES_MODULE = 'varnish_bans_manager.assets_mapping'
GENERATED_MEDIA_NAMES_FILE = ROOT / 'assets_mapping.py'

COPY_MEDIA_FILETYPES = (
    'gif', 'jpg', 'jpeg', 'png', 'svg', 'svgz',
    'ico', 'swf', 'ttf', 'otf', 'eot', 'woff', 'json',
)

MEDIA_BUNDLES = (
    (
        'bundle.css',
        'varnish-bans-manager/js/plugins/jquery-ui/css/ui-lightness/jquery-ui-1.9.2.custom.css',
        'varnish-bans-manager/css/main.scss',
    ),
    (
        'bundle.js',
        'varnish-bans-manager/js/plugins/jquery.once.js',
        'varnish-bans-manager/js/plugins/jquery.form.js',
        'varnish-bans-manager/js/plugins/jquery.notify.js',
        'varnish-bans-manager/js/plugins/history/history.adapter.jquery.js',
        'varnish-bans-manager/js/plugins/history/history.js',
        'varnish-bans-manager/js/plugins/history/history.html4.js',
        'varnish-bans-manager/js/main.js',
        'varnish-bans-manager/js/notifications.js',
        'varnish-bans-manager/js/ajax.js',
        'varnish-bans-manager/js/navigation.js',
        'varnish-bans-manager/js/behaviors.js',
        'varnish-bans-manager/js/commands.js',
        'varnish-bans-manager/js/partials.js',
    ),
    (
        'bootstrap.js',
        {'filter': 'mediagenerator.filters.i18n.I18N'},
        {'filter': 'mediagenerator.filters.media_url.MediaURL'},
        'varnish-bans-manager/js/plugins/jquery.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-transition.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-alert.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-button.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-carousel.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-collapse.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-dropdown.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-modal.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-scrollspy.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-tab.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-tooltip.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-popover.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-typeahead.js',
        'varnish-bans-manager/js/bootstrap/bootstrap-affix.js',
        'varnish-bans-manager/js/plugins/jquery-ui/jquery.ui.js',
        'varnish-bans-manager/js/bootstrap.js',
    ),
)

ROOT_MEDIA_FILTERS = {
    'js': 'mediagenerator.filters.yuicompressor.YUICompressor',
    'css': 'mediagenerator.filters.yuicompressor.YUICompressor',
}

SASS_FRAMEWORKS = (
    'compass',
)

YUICOMPRESSOR_PATH = os.environ.get('YUICOMPRESSOR_PATH', None)

###############################################################################
## LOGGING.
###############################################################################

SQL_LOGGING = DEBUG
TEMPLATE_DEBUG = DEBUG

INTERNAL_IPS = ()


def _require_production_environment(request):
    return IS_PRODUCTION


def _require_development_environment(request):
    return not IS_PRODUCTION


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'handlers': ['mail_admins'],
        'level': 'ERROR',
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_production_environment': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': _require_production_environment,
        },
        'require_development_environment': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': _require_development_environment,
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_production_environment'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'logfile': {
            'level': 'DEBUG',
            'filters': ['require_development_environment'],
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '/dev/null' if IS_PRODUCTION else '/tmp/varnish-bans-manager' + USER_SUFFIX + '.log',
        },
    },
    'loggers': {
        'vbm': {
            'handlers': ['logfile'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}

###############################################################################
## TESTS.
###############################################################################

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

###############################################################################
## I18N.
###############################################################################

LOCALE_PATHS = (
    ROOT / 'locale',
)
LANGUAGE_CODE = _config.get('i18n', 'default')

LANGUAGES = (
    ('es', ugettext('Spanish')),
    ('en', ugettext('English')),
)

###############################################################################
## EMAIL.
###############################################################################

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = _config.get('email', 'host')
EMAIL_PORT = _config.getint('email', 'port')
EMAIL_HOST_USER = _config.get('email', 'user')
EMAIL_HOST_PASSWORD = _config.get('email', 'password')
EMAIL_USE_TLS = _config.getboolean('email', 'tls')

DEFAULT_FROM_EMAIL = _config.get('email', 'from')
DEFAULT_BCC_EMAILS = []

SERVER_EMAIL = _config.get('email', 'from')

EMAIL_SUBJECT_PREFIX = _config.get('email', 'subject_prefix') + ' '

###############################################################################
## TEMPLATED EMAIL (https://github.com/bradwhittington/django-templated-email).
###############################################################################

TEMPLATED_EMAIL_BACKEND = 'templated_email.backends.vanilla_django.TemplateBackend'
TEMPLATED_EMAIL_TEMPLATE_DIR = 'emails/'

###############################################################################
## POWER USERS.
###############################################################################

# People who get code error notifications.
ADMINS = [('VBM notifications', _config.get('email', 'notifications'))]

# Not-necessarily-technical managers of the site. They get broken link
# notifications and other various emails.
MANAGERS = ADMINS

###############################################################################
## VERSION.
###############################################################################

VERSION = {
    'assets': {'major': 1, 'minor': 1},
    'js':     {'major': 1, 'minor': 1},
    'css':    {'major': 1, 'minor': 1},
}

###############################################################################
## VBM.
###############################################################################

VBM_HTTP = dict(_config.items('http'))
VBM_EMAIL_SUBJECT_PREFIX = _config.get('email', 'subject_prefix') + ' '
VBM_CONTACT_EMAIL = _config.get('email', 'contact')
VBM_NOTIFICATIONS_EMAIL = _config.get('email', 'notifications')
VBM_BASE_URL = VBM_HTTP.pop('base_url').rstrip('/')
if not VBM_BASE_URL.startswith('http'):
    VBM_BASE_URL = 'http://%s' % VBM_BASE_URL

###############################################################################
## MISC.
###############################################################################

ALLOWED_HOSTS = ['*']

ROOT_URLCONF = 'varnish_bans_manager.urls'
WSGI_APPLICATION = 'varnish_bans_manager.wsgi.application'

TIME_ZONE = _config.get('misc', 'timezone')
USE_I18N = True
USE_L10N = True
USE_THOUSAND_SEPARATOR = True
USE_TZ = True
USE_ETAGS = False

SECRET_KEY = _config.get('misc', 'secret_key')

# Default content type and charset to use for all HttpResponse objects, if a
# MIME type isn't manually specified. These are used to construct the
# Content-Type header.
DEFAULT_CONTENT_TYPE = 'text/html'
DEFAULT_CHARSET = 'utf-8'

# Encoding of files read from disk (template and initial SQL files).
FILE_CHARSET = 'utf-8'

# Whether to send broken-link emails.
SEND_BROKEN_LINK_EMAILS = False

###############################################################################
## CELERY (http://docs.celeryproject.org/en/latest/configuration.html).
###############################################################################

djcelery.setup_loader()

# See http://docs.celeryproject.org/en/latest/getting-started/brokers/django.html.
BROKER_URL = 'django://'
CELERY_DISABLE_RATE_LIMITS = True
CELERYD_TASK_SOFT_TIME_LIMIT = 3600  # 1 hour.
CELERYD_TASK_TIME_LIMIT = None

CELERY_IMPORTS = (
    'varnish_bans_manager.filesystem.tasks',
    'varnish_bans_manager.core.tasks.bans',
    'varnish_bans_manager.core.tasks.kombu',
    'varnish_bans_manager.core.tasks.sessions',
    'varnish_bans_manager.core.tasks.users',
)

CELERY_TIMEZONE = TIME_ZONE

CELERY_SEND_TASK_ERROR_EMAILS = IS_PRODUCTION

CELERYD_HIJACK_ROOT_LOGGER = True

# See http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html
CELERYBEAT_SCHEDULE = {
    'bans.notify_submissions': {
        'task': 'varnish_bans_manager.core.tasks.bans.NotifySubmissions',
        'schedule': crontab(minute='*/10'),
    },
    'sessions.purge_expired': {
        'task': 'varnish_bans_manager.core.tasks.sessions.PurgeExpired',
        'schedule': crontab(minute=0, hour='*/1'),
    },
    'kombu.purge_invisible': {
        'task': 'varnish_bans_manager.core.tasks.kombu.PurgeInvisible',
        'schedule': crontab(minute=0, hour='*/1'),
    },
}
