#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
# import os
from .base import *

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# PROJECT_NAME = os.path.split(PROJECT_ROOT)[-1]

SECRET_KEY = '123'

rel = lambda p: os.path.join(PROJECT_ROOT, p)
rootrel = lambda p: os.path.join(PROJECT_ROOT, '..', p)

DEBUG = True
CROISEE_DEFAULT_OWNER_ID = -1

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': rel('dev.db'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        'ATOMIC_REQUESTS': True,                  # Wrap everything in transactions.
    }
}

MEDIA_ROOT = rel('media')

if DEBUG:
    # INSTALLED_APPS.append('django.contrib.admindocs')
    # INSTALLED_APPS.append('debug_toolbar')
    # MIDDLEWARE_CLASSES.append('debug_toolbar.middleware.DebugToolbarMiddleware')  # see also http://github.com/robhudson/django-debug-toolbar/blob/master/README.rst
    LOGGING['handlers']['file'] = {
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'formatter': 'verbose',
                'filename': rootrel('logs/info.log'),
            }
    LOGGING['handlers']['error_file'] = {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'formatter': 'verbose',
                'filename': rootrel('logs/error.log'),
            }

SECURE_SSL_REDIRECT = False  # if all non-SSL requests should be permanently redirected to SSL.
SESSION_COOKIE_SECURE = False  # if you are using django.contrib.sessions (True blocks admin login)

import warnings
warnings.filterwarnings(
        'error', r"DateTimeField .* received a naive datetime",
        RuntimeWarning, r'django\.db\.models\.fields')
