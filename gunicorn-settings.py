#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
#from croisee import settings
PROJECT_NAME='croisee'
rootrel = lambda p: os.path.normpath(os.path.join('/var/www', PROJECT_NAME, p))

bind = '127.0.0.1:8'+str(os.getuid())[1:]
workers = 2
#worker_class = 'eventlet'
#max_requests = 2048
pidfile = rootrel('logs/django.pid')
user = PROJECT_NAME
group = PROJECT_NAME
logfile = rootrel('logs/gunicorn.log')
#loglevel = 'info'
proc_name = 'gunicorn-'+PROJECT_NAME
