#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.shortcuts import render_to_response
from croisee.models import Dictionary, Word, cleanword

def index(request, *args, **kwargs):
    dictionaries = Dictionary.objects.all()
    try:
        searchterm = cleanword(request.POST['searchterm'], False).upper()
        posted = True
        # REGEX search
        #internal = searchterm.replace('?','.').replace('_','.').replace('*','.+').replace('%','.+')
        #results = Word.objects.filter(word__regex=r'^%s$' % internal)
        # EXTRA search
        internal = searchterm.replace('?','_').replace('*','%').replace('%','%%')
        results = Word.objects.extra(where=['word LIKE "' + internal + '"'])
        # TODO: dictionaries in selected
    except (KeyError, Word.DoesNotExist):
        searchterm = ''
        results = None
        posted= False
    return render_to_response('index.html', {
        'MEDIA_URL':    settings.MEDIA_URL,
        'dictionaries': dictionaries,
        'searchterm':   searchterm,
        'results':      results,
        'posted':       posted
    })
