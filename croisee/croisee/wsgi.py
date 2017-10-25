#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WSGI config for croisée project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

import dotenv
current_dir = os.path.dirname(__file__)
try:
    # django-dotenv-rw (Python 2.7)
    try:
        dotenv.load_dotenv(os.path.join(current_dir, '.env'))
    except UserWarning:
        dotenv.load_dotenv(os.path.abspath(os.path.join(current_dir, '../../..', '.env')))
except AttributeError:
    # django-dotenv (Python 3)
    try:
        dotenv.read_dotenv(os.path.join(current_dir, '.env'))
    except UserWarning:
        dotenv.read_dotenv(os.path.abspath(os.path.join(current_dir, '../../..', '.env')))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
