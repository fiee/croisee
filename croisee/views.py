#!/usr/bin/env python
# -*- coding: utf-8 -*-
from feincms.views.base import handler

def home(request):
    """
    This is only a redirect to the 'home' page of feincms, handled by feincms.views.base.handler
    """
    return handler(request, '/home/')
