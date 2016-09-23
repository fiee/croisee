#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
#from django.utils.translation import ugettext_lazy as _
# docs say: don't import translation in settings, but it works...
_ = lambda s: s

BASE_DIR = PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = os.path.split(PROJECT_ROOT)[-1]

rel = lambda p: os.path.normpath(os.path.join(PROJECT_ROOT, p)) # this is release and virtualenv dependent
rootrel = lambda p: os.path.normpath(os.path.join('/var/www', PROJECT_NAME, p)) # this is not

sys.path += [PROJECT_ROOT, os.path.join(PROJECT_ROOT,'lib/python2.7/site-packages')]

# ==============================================================================
# debug settings
# ==============================================================================

DEBUG = False
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1',)
if DEBUG:
    TEMPLATE_STRING_IF_INVALID = _(u'STRING_NOT_SET')

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
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s' # %(process)d %(thread)d 
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
#    'filters': {
#        'special': {
#            '()': 'project.logging.SpecialFilter',
#            'foo': 'bar',
#        }
#    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file':{
            'level':'INFO',
            'class':'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'verbose',
            'filename': rootrel('logs/info.log'),
            'when': 'D',
            'interval': 7,
            'backupCount': 4,
            # rotate every 7 days, keep 4 old copies
        },
        'error_file':{
            'level':'ERROR',
            'class':'logging.handlers.TimedRotatingFileHandler',
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
            #'filters': ['special']
        }
    },
    'loggers': {
        'django': { # django is the catch-all logger. No messages are posted directly to this logger.
            'handlers':['null', 'error_file'],
            'propagate': True,
            'level':'INFO',
        },
        'django.request': { # Log messages related to the handling of requests. 5XX responses are raised as ERROR messages; 4XX responses are raised as WARNING messages.
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        PROJECT_NAME: {
            'handlers': ['console', 'file', 'error_file', 'mail_admins'],
            'level': 'INFO',
            #'filters': ['special']
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
        'TIMEOUT': 600,
    }
}

USE_ETAGS = True

# ==============================================================================
# email and error-notify settings
# ==============================================================================

# PLEASE CHANGE THIS IF YOU CLONE croisée!
YOUR_DOMAIN = 'fiee.net'

ALLOWED_HOSTS = ['croisee.'+YOUR_DOMAIN, 'croisee.'+YOUR_DOMAIN+'.', ] + list(INTERNAL_IPS)

ADMINS = (
    ('Henning Hraban Ramm', 'hraban@%s' % YOUR_DOMAIN),
)

MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = '%s@%s' % (PROJECT_NAME, YOUR_DOMAIN)
SERVER_EMAIL = 'error-notify@%s' % YOUR_DOMAIN

EMAIL_SUBJECT_PREFIX = '[%s] ' % PROJECT_NAME
EMAIL_HOST = 'mail.%s' % YOUR_DOMAIN
EMAIL_PORT = 25
EMAIL_HOST_USER = '%s@%s' % (PROJECT_NAME, YOUR_DOMAIN)
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

# ==============================================================================
# database settings
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'OPTIONS': {'init_command': 'SET storage_engine=INNODB'}, # mysql only
        'NAME': PROJECT_NAME,                      # Or path to database file if using sqlite3.
        'USER': PROJECT_NAME,                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        'ATOMIC_REQUESTS': True,                  # Wrap everything in transactions.
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

LOCALE_PATHS = (
    rel('locale/'),
)

SITE_ID = 1

ROOT_URLCONF = '%s.urls' % PROJECT_NAME

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = '%s.wsgi.application' % PROJECT_NAME

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
STATICFILES_DIRS = (rel('static'), ) #'.../feincms/media',
# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)
ADMIN_MEDIA_PREFIX = '%sadmin/' % STATIC_URL # Don’t know if that’s still used

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
    #'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles', # Django 1.3
    #'django.contrib.humanize',
    #'django.contrib.sitemaps',
    #'gunicorn', # not with fcgi
    'south',
    'rest_framework', # RESTful API - optional, just comment
    'registration',
    'guardian',
    #'tagging',
    PROJECT_NAME,
]

MIDDLEWARE_CLASSES = [
    'django.middleware.cache.UpdateCacheMiddleware', # first
    'django.middleware.gzip.GZipMiddleware', # second after UpdateCache
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    '%s.middleware.Http403Middleware' % PROJECT_NAME,
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.doc.XViewMiddleware', # for local IPs
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware', # last
]

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth', # Django 1.3
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.core.context_processors.static', # Django 1.3 staticfiles
    'django.contrib.messages.context_processors.messages',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
#       'django.template.loaders.eggs.Loader',
    )),
)

# ==============================================================================
# the secret key
# ==============================================================================

try:
    SECRET_KEY
except NameError:
    if DEBUG:
        SECRET_FILE = rel('secret.txt')
    else:
        SECRET_FILE = rootrel('secret.txt')
    try:
        SECRET_KEY = open(SECRET_FILE).read().strip()
    except IOError:
        try:
            from random import choice
            SECRET_KEY = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
            secret = file(SECRET_FILE, 'w')
            secret.write(SECRET_KEY)
            secret.close()
        except IOError:
            Exception(_(u'Please create a %s file with random characters to generate your secret key!' % SECRET_FILE))

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
ANONYMOUS_USER_ID = -1 # guardian
ACCOUNT_ACTIVATION_DAYS = 7 # registration

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # default
    'guardian.backends.ObjectPermissionBackend',
)

# admin_tools
ADMIN_TOOLS_MENU = '%s.menu.CustomMenu' % PROJECT_NAME
ADMIN_TOOLS_INDEX_DASHBOARD = '%s.dashboard.CustomIndexDashboard' % PROJECT_NAME
ADMIN_TOOLS_APP_INDEX_DASHBOARD = '%s.dashboard.CustomAppIndexDashboard' % PROJECT_NAME

# ==============================================================================
# host specific settings
# ==============================================================================

try:
    from settings_local import *
    # database password is defined in settings_webserver.py (that gets copied to settings_local.py by fab)
    DATABASES['default']['PASSWORD'] = DATABASE_PASSWORD
except ImportError:
    pass
if DEBUG:
    INSTALLED_APPS.append('django.contrib.admindocs')
    #INSTALLED_APPS.append('debug_toolbar')
    #MIDDLEWARE_CLASSES.append('debug_toolbar.middleware.DebugToolbarMiddleware') # see also http://github.com/robhudson/django-debug-toolbar/blob/master/README.rst
    LOGGING['handlers']['file'] = {
                'level':'INFO',
                'class':'logging.FileHandler',
                'formatter': 'verbose',
                'filename': rootrel('logs/info.log'),
            }
    LOGGING['handlers']['error_file'] = {
                'level':'ERROR',
                'class':'logging.FileHandler',
                'formatter': 'verbose',
                'filename': rootrel('logs/error.log'),
            }
