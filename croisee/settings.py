#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
from django.utils.translation import ugettext_lazy as _

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_NAME = os.path.split(PROJECT_ROOT)[-1]

rel = lambda p: os.path.join(PROJECT_ROOT, p) # this is release and virtualenv dependent
rootrel = lambda p: os.path.join('/var/www', PROJECT_NAME, p) # this is not

sys.path += [PROJECT_ROOT, os.path.join(PROJECT_ROOT,'lib/python2.5/site-packages'), '/var/www/python']

# ==============================================================================
# debug settings
# ==============================================================================

DEBUG = False
TEMPLATE_DEBUG = DEBUG
INTERNAL_IPS = ('127.0.0.1')
if DEBUG:
    TEMPLATE_STRING_IF_INVALID = _(u'STRING_NOT_SET')

# ==============================================================================
# cache settings
# ==============================================================================

CACHE_BACKEND = 'locmem://'
CACHE_MIDDLEWARE_KEY_PREFIX = '%s_' % PROJECT_NAME
CACHE_MIDDLEWARE_SECONDS = 600

# ==============================================================================
# email and error-notify settings
# ==============================================================================

ADMINS = (
    ('Henning Hraban Ramm', 'hraban@fiee.net'),
)

MANAGERS = ADMINS

DEFAULT_FROM_EMAIL = 'website@fiee.net'
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

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = PROJECT_NAME #os.path.join(PROJECT_ROOT, 'dev.db')
DATABASE_USER = PROJECT_NAME
DATABASE_PASSWORD = ''
DATABASE_HOST = 'localhost'
DATABASE_PORT = ''

# ==============================================================================
# i18n and url settings
# ==============================================================================

TIME_ZONE = 'Europe/Zurich'
LANGUAGE_CODE = 'de'
#LANGUAGES = (('en', _(u'English')),
#             ('de', _(u'German')))
USE_I18N = True

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
    'django.contrib.admin',
    #'django.contrib.humanize',
    #'django.contrib.sitemaps',
    #'tagging',
    PROJECT_NAME,
]

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
#    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.csrf.middleware.CsrfMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.common.CommonMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
)

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'templates'),
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#    'django.template.loaders.eggs.load_template_source',
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
# third party
# ==============================================================================

# ..third party app settings here

# ==============================================================================
# host specific settings
# ==============================================================================

try:
    from settings_local import *
except ImportError:
    pass
if DEBUG:
    INSTALLED_APPS.append('django.contrib.admindocs')
