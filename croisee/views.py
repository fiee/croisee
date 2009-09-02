#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.shortcuts import render_to_response

def home(request, *args, **kwargs):
    return render_to_response('root.html', {'MEDIA_URL':settings.MEDIA_URL})
