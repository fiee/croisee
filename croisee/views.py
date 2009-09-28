#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response
from croisee.models import Dictionary, Word, cleanword
import sets

def _get_dictionaries(request):
    """
    get all dictionaries that the user may access and didn't disable
    
    requires:
    request.POST
    
    returns: tuple
        queryset of dictionaries,
        list of disabled dictionary ids 
    """
    dictionaries = Dictionary.objects.filter(public=True)
    if request.method != 'POST':
        return (dictionaries, [])
    disabled_dicts = []
    for d in dictionaries:
        if 'dic_%d' % d.id not in request.POST:
            d.disabled = True
            disabled_dicts.append(d.id)
    return (dictionaries, disabled_dicts)

def _search(request, searchterm, limit=settings.CROISEE_QUERYMAX):
    """
    search after a searchterm
    
    wildcards allowed: * % ? _
    
    returns: dict
        dictionaries: queryset of Dictionaries
        results: list of matching Words
        resultcount: number of matches
        searchterm: cleaned searchterm
    """
    dictionaries = _get_dictionaries(request)
    context = {
        'dictionaries': dictionaries[0],
        'results':      [],
        'resultcount':  0,
        'searchterm':   '',
    }
    try:
        searchterm = cleanword(searchterm, False).upper()
        internal = searchterm.replace('?','_').replace('*','%').replace('%','%%')
        if not ('_' in internal or '%%' in internal): # without wildcards = no search needed
            context['results'] = Word.objects.filter(word=internal, dictionary__public=True).exclude(dictionary__id__in=dictionaries[1])[:limit]
            if not context['results']: # new word
                context['results'] = [ Word(word=internal, description=searchterm.title()) ]
        else:
            context['results'] = Word.objects.extra(where=['word LIKE "'+internal+'"']).filter(dictionary__public=True).exclude(dictionary__id__in=dictionaries[1])[:limit]
        # TODO: dictionaries in selected
        context['resultcount'] = len(context['results'])
        context['searchterm'] = searchterm
    except (KeyError, Word.DoesNotExist), ex:
        pass
    return context


def index(request, *args, **kwargs):
    context = {
        'MEDIA_URL':    settings.MEDIA_URL,
        'posted':       (request.method == 'POST'),
    }
    if request.method == 'POST':
        context.update(_search(request, request.POST['searchterm']))
    else:
        context['dictionaries'] = _get_dictionaries(request)[0]
    return render_to_response('index.html', context)

def grid(request, *args, **kwargs):
    puzzle = None
    if request.method == 'POST':
        maxrow = int(request.POST['maxx'])
        maxline = int(request.POST['maxy'])
        if maxrow < settings.CROISEE_GRIDMIN_X: maxrow = settings.CROISEE_GRIDMIN_X
        if maxline < settings.CROISEE_GRIDMIN_Y: maxline = settings.CROISEE_GRIDMIN_Y
        if maxrow > settings.CROISEE_GRIDMAX_X: maxrow = settings.CROISEE_GRIDMAX_X
        if maxline > settings.CROISEE_GRIDMAX_Y: maxline = settings.CROISEE_GRIDMAX_Y
        puzzle = {
            'maxrow':   maxrow,
            'maxline':  maxline,
            'rows':     range(1,maxrow+1),
            'lines':    range(1,maxline+1),
            'chars':    {},
            #'posted':   False,
            'puzzle':   None,
        }
        for y in puzzle['lines']:
            puzzle['chars'][y] = {}
            for x in puzzle['rows']:
                puzzle['chars'][y][x] = 'X'
    context = {
        'MEDIA_URL':    settings.MEDIA_URL,
        'posted':       (request.method == 'POST'),
        'puzzle':       puzzle,
        'defaultx':     settings.CROISEE_GRIDDEF_X,
        'defaulty':     settings.CROISEE_GRIDDEF_Y,
        'dictionaries': _get_dictionaries(request)[0],
    }
    return render_to_response('grid.html', context)

def ajax_query(request, **kwargs):
    """
    do a query for several words, separated by slashes
    
    if words are in format "word,0", the number says which letter of both word must match
    """
    horiz = kwargs['horizontal']
    vert = kwargs['vertical']
    try:
        hl = int(kwargs['hletter'])
        vl = int(kwargs['vletter'])
    except TypeError:
        hl = None
        vl = None
    if hl != None and vl != None and len(horiz)>hl and len(vert)>vl:
        results = (_search(request, horiz, 1024), _search(request, vert, settings.CROISEE_XQUERYMAX)) # "no" limit
        hres = sets.Set()
        vres = sets.Set()
        for h in results[0]['results']:
            for v in results[1]['results']:
                if h.word[hl] == v.word[vl]:
                    hres.add(h)
                    vres.add(v)
        results[0]['results'] = list(hres)[:settings.CROISEE_QUERYMAX] # default limit
        results[1]['results'] = list(vres)[:settings.CROISEE_QUERYMAX] # default limit
        results[0]['resultcount'] = len(hres)
        results[1]['resultcount'] = len(vres)
    else:
        results = (_search(request, horiz), _search(request, vert)) # default limit
    results[0]['direction'] = 'horizontal'
    results[1]['direction'] = 'vertical'
    results[0]['name'] = _('horizontal')
    results[1]['name'] = _('vertical')
    return render_to_response('ajax_query.html', {'results':results})
