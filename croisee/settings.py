#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
from django.utils.translation import ugettext_lazy as _

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = os.path.split(PROJECT_ROOT)[-1]

rel = lambda p: os.path.join(PROJECT_ROOT, p) # this is release and virtualenv dependent
rootrel = lambda p: os.path.join('/var/www', PROJECT_NAME, p) # this is not

sys.path += [PROJECT_ROOT, os.path.join(PROJECT_ROOT,'lib/python2.5/site-packages')]

# ==============================================================================
# debug settings
# ==============================================================================

DEBUG = False
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1',)
if DEBUG:
    TEMPLATE_STRING_IF_INVALID = _(u'STRING_NOT_SET')

# ==============================================================================
# cache settings
# ==============================================================================

CACHE_BACKEND = 'file:///var/tmp/django_cache/%s' % PROJECT_NAME
CACHE_MIDDLEWARE_KEY_PREFIX = '' # %s_' % PROJECT_NAME
CACHE_MIDDLEWARE_SECONDS = 600
USE_ETAGS = True

# ==============================================================================
# email and error-notify settings
# ==============================================================================

ADMINS = (
    ('Henning Hraban Ramm', 'hraban@fiee.net'),
)

MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = '%s@fiee.net' % PROJECT_NAME
SERVER_EMAIL = 'error-notify@fiee.net'

EMAIL_SUBJECT_PREFIX = '[%s] ' % PROJECT_NAME
EMAIL_HOST = 'mail.fiee.net'
EMAIL_PORT = 25
EMAIL_HOST_USER = PROJECT_NAME
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False

# ==============================================================================
# auth settings
# ==============================================================================

LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
LOGIN_REDIRECT_URL = '/'

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
    }
}

# ==============================================================================
# i18n and url settings
# ==============================================================================

TIME_ZONE = 'Europe/Zurich'
LANGUAGE_CODE = 'de'
#LANGUAGES = (('en', _(u'English')),
#             ('de', _(u'German')))
USE_I18N = True
USE_L10N = True

SITE_ID = 1

MEDIA_ROOT = rel('static')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/django_admin_media/'

ROOT_URLCONF = '%s.urls' % PROJECT_NAME

# ==============================================================================
# application and middleware settings
# ==============================================================================

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    #'django.contrib.humanize',
    #'django.contrib.sitemaps',
    'south',
    #'tagging',
    PROJECT_NAME,
]

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware', # first
    'django.middleware.gzip.GZipMiddleware', # second after UpdateCache
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.csrf.CsrfResponseMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.doc.XViewMiddleware', # for local IPs
    'django.middleware.cache.FetchFromCacheMiddleware', # last
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
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

# ==============================================================================
# host specific settings
# ==============================================================================

try:
    from settings_local import *
except ImportError:
    pass
if DEBUG:
    INSTALLED_APPS.append('django.contrib.admindocs')
