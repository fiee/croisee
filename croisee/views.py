#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.shortcuts import render_to_response
from croisee.models import Dictionary, Word, cleanword

def index(request, *args, **kwargs):
    dictionaries = Dictionary.objects.all()
    forbidden_dicts = []
    context = {
        'MEDIA_URL':    settings.MEDIA_URL,
        'dictionaries': dictionaries,
        'posted':       False,
        'results':      [],
        'resultcount':  0,
        'searchterm':   '',
    }
    if request.POST:
        context['posted'] = True
        for d in dictionaries:
            if 'dic_%d' % d.id not in request.POST:
                d.disabled = True
                forbidden_dicts.append(d.id)
    try:
        searchterm = cleanword(request.POST['searchterm'], False).upper()
        # REGEX search
        #internal = searchterm.replace('?','.').replace('_','.').replace('*','.+').replace('%','.+')
        #results = Word.objects.filter(word__regex=r'^%s$' % internal)
        # EXTRA search
        internal = searchterm.replace('?','_').replace('*','%').replace('%','%%')
        results = Word.objects.extra(where=['word LIKE "'+internal+'"']).exclude(dictionary__id__in=forbidden_dicts)
        # TODO: dictionaries in selected
        context['resultcount'] = len(results)
        context['results'] = results
        context['searchterm'] = searchterm
    except (KeyError, Word.DoesNotExist), ex:
        pass
    return render_to_response('index.html', context)
