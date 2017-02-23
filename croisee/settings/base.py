#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""
import os
import sys
from django.core.exceptions import ImproperlyConfigured
# translation needed for date and time format setup
from django.utils.translation import ugettext_lazy as _
import dotenv
import logging
logging.captureWarnings(True)  # dotenv uses warnings

def get_env_variable(var_name):
    """Get the environment variable or return exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        error_msg = _('Set the %s environment variable.') % var_name
        raise ImproperlyConfigured(error_msg)


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # get out of settings
PROJECT_NAME = os.path.split(PROJECT_ROOT)[-1]


def rel(p):
    # this is release and virtualenv dependent
    return os.path.normpath(os.path.join(PROJECT_ROOT, p))


def rootrel(p):
    # this is not
    return os.path.normpath(os.path.join('/var/www', PROJECT_NAME, p))


dotenv.read_dotenv(rootrel('.env'))


# sys.path += [PROJECT_ROOT, os.path.join(PROJECT_ROOT, 'lib/python3.5/site-packages')]


# ==============================================================================
# debug settings
# ==============================================================================

DEBUG = False
INTERNAL_IPS = ('127.0.0.1',)

# logging: see
# http://docs.djangoproject.com/en/dev/topics/logging/
# http://docs.python.org/library/logging.html

# import logging
# logger = logging.getLogger(__name__)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'  # %(process)d %(thread)d 
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
         'require_debug_false': {
             '()': 'django.utils.log.RequireDebugFalse'
         }
     },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'verbose',
            'filename': rootrel('logs/info.log'),
            'when': 'D',
            'interval': 7,
            'backupCount': 4,
            # rotate every 7 days, keep 4 old copies
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'verbose',
            'filename': rootrel('logs/error.log'),
            'when': 'D',
            'interval': 7,
            'backupCount': 4,
            # rotate every 7 days, keep 4 old copies
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        }
    },
    'loggers': {
        'django': {  # django is the catch-all logger. No messages are posted directly to this logger.
            'handlers': ['null', 'error_file'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.request': {  # Log messages related to the handling of requests. 5XX responses are raised as ERROR messages; 4XX responses are raised as WARNING messages.
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        PROJECT_NAME: {
            'handlers': ['console', 'file', 'error_file', 'mail_admins'],
            'level': 'INFO',
            # 'filters': ['special']
        }
    }
}

# ==============================================================================
# cache settings
# ==============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache/%s' % PROJECT_NAME,
        'TIMEOUT': 30,
    }
}

USE_ETAGS = True

# ==============================================================================
# email and error-notify settings
# ==============================================================================

# PLEASE CHANGE THIS IF YOU CLONE croisée!
YOUR_DOMAIN = 'fiee.net'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.10/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
                 'localhost',
                 'croisee.' + YOUR_DOMAIN,
                 'croisee.' + YOUR_DOMAIN + '.',  # FQDN (see above doc link)
                 ] + list(INTERNAL_IPS)

ADMINS = (
    ('Henning Hraban Ramm', 'hraban@fiee.net'), # don't send your errors to me!
    #('You', 'root@%s' % YOUR_DOMAIN),
)

MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = '%s@%s' % (PROJECT_NAME, YOUR_DOMAIN)
SERVER_EMAIL = 'error-notify@%s' % YOUR_DOMAIN

EMAIL_SUBJECT_PREFIX = '[%s] ' % PROJECT_NAME
EMAIL_HOST = 'mail.%s' % YOUR_DOMAIN
EMAIL_PORT = 587
EMAIL_HOST_USER = '%s@%s' % (PROJECT_NAME, YOUR_DOMAIN)
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = get_env_variable('EMAIL_PASSWORD')
EMAIL_USE_TLS = True

# ==============================================================================
# database settings
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': PROJECT_NAME,  # Or path to database file if using sqlite3.
        'USER': PROJECT_NAME,  # Not used with sqlite3.
        'PASSWORD': get_env_variable('DATABASE_PASSWORD'),  # Not used with sqlite3.
        'HOST': 'localhost',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
        'ATOMIC_REQUESTS': True,  # Wrap everything in transactions.
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ==============================================================================
# i18n and url settings
# ==============================================================================

TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de'
LANGUAGES = (('en', _(u'English')),
             ('de', _(u'German')))
USE_I18N = True
USE_L10N = True
# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

SHORT_DATE_FORMAT = _('d/m/Y')
SHORT_DATETIME_FORMAT = _('d/m/Y H:m')
TIME_FORMAT = _('H:m')

LOCALE_PATHS = (
    rel('locale/'),
)

SITE_ID = 1

ROOT_URLCONF = '%s.urls' % PROJECT_NAME

# Python dotted path to the WSGI application used by Django's runserver.
# WSGI_APPLICATION = '%s.wsgi.application' % PROJECT_NAME

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
# don’t use /media/! FeinCMS’ media library uses MEDIA_ROOT/medialibrary
MEDIA_ROOT = rootrel('')
# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/'

# setup Django 1.3+ staticfiles
# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'
STATIC_ROOT = rel('static_collection')
STATICFILES_DIRS = (
    rel('static'),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)
# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# ==============================================================================
# application and middleware settings
# ==============================================================================

INSTALLED_APPS = [
    #'admin_tools',
    #'admin_tools.theming',
    #'admin_tools.menu',
    #'admin_tools.dashboard',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #'django.contrib.sites',
    #'django.contrib.humanize',
    #'django.contrib.sitemaps',
    'gunicorn', # not with fcgi
    'rest_framework', # RESTful API - optional, just comment
    #'registration',  # not necessary
    'guardian',
    'tagging',
    PROJECT_NAME,
]

MIDDLEWARE_CLASSES = [
    'django.middleware.cache.UpdateCacheMiddleware',  # first
    'django.middleware.gzip.GZipMiddleware',  # second after UpdateCache
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    '%s.middleware.Http403Middleware' % PROJECT_NAME,
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',  # for local IPs
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',  # last
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, 'templates'), ],
        # 'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', (
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                    # 'admin_tools.template_loaders.Loader',
                )),
            ],
        },
    },
]


SECRET_KEY = get_env_variable('SECRET_KEY')

# ==============================================================================
# croisee
# ==============================================================================

CROISEE_GRIDMIN_X =   4 # minimum rows in puzzle grid
CROISEE_GRIDMIN_Y =   4 # minimum lines in puzzle grid
CROISEE_GRIDMAX_X =  20 # maximum rows in puzzle grid
CROISEE_GRIDMAX_Y =  20 # maximum lines in puzzle grid
CROISEE_GRIDDEF_X =  12 # default rows in puzzle grid
CROISEE_GRIDDEF_Y =  12 # default lines in puzzle grid
CROISEE_QUERYMAX  = 100 # maximum query results
CROISEE_XQUERYMAX = 1024 # maximum cross query results
CROISEE_DEFAULT_OWNER_ID = 1

# ==============================================================================
# third party
# ==============================================================================

# ..third party app settings here

# auth/registration
LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
LOGIN_REDIRECT_URL = '/'
ANONYMOUS_USER_ID = -1  # guardian
ACCOUNT_ACTIVATION_DAYS = 7  # registration

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # default
    'guardian.backends.ObjectPermissionBackend',
)

# admin_tools
ADMIN_TOOLS_MENU = '%s.menu.CustomMenu' % PROJECT_NAME
ADMIN_TOOLS_INDEX_DASHBOARD = '%s.dashboard.CustomIndexDashboard' % PROJECT_NAME
ADMIN_TOOLS_APP_INDEX_DASHBOARD = '%s.dashboard.CustomAppIndexDashboard' % PROJECT_NAME

# django-secure
SECURE_SSL_REDIRECT = False  # if all non-SSL requests should be permanently redirected to SSL.
SECURE_HSTS_SECONDS = 60  # integer number of seconds, if you want to use HTTP Strict Transport Security
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # if you want to use HTTP Strict Transport Security
SECURE_FRAME_DENY = True  # if you want to prevent framing of your pages and protect them from clickjacking.
SECURE_CONTENT_TYPE_NOSNIFF = True  # if you want to prevent the browser from guessing asset content types.
SECURE_BROWSER_XSS_FILTER = True  # if you want to enable the browser's XSS filtering protections.
SESSION_COOKIE_SECURE = False  # if you are using django.contrib.sessions
SESSION_COOKIE_HTTPONLY = True  # if you are using django.contrib.sessions
