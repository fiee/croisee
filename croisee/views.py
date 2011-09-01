#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect
from django.template import RequestContext
from croisee.models import Dictionary, Word, cleanword
import logging
logger = logging.getLogger(settings.PROJECT_NAME)

def server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: `500.html`
    Context: None
    """
    # see http://ericholscher.com/blog/2009/sep/23/pretty-django-error-pages/
    return render(request, template_name)

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
            context['results'] = Word.objects.filter(word=internal, dictionary__public=(not request.user.is_staff)).exclude(dictionary__id__in=dictionaries[1])[:limit]
            if not context['results']: # new word
                context['results'] = [ Word(word=internal, description=searchterm.title()) ]
        else:
            context['results'] = Word.objects.extra(where=['word LIKE "'+internal+'"']).filter(dictionary__public=(not request.user.is_staff)).exclude(dictionary__id__in=dictionaries[1])[:limit]
        # TODO: dictionaries in selected (hu??)
        context['resultcount'] = len(context['results'])
        context['searchterm'] = searchterm
    except (KeyError, Word.DoesNotExist), ex:
        pass
    return context

def _find_word(text, start_y, start_x, direction='h', stopchar='.'):
    """
    find a word in a text, starting at position y, x (0-based)
    
    direction is h or v
    """
    lines = [line for line in text.split('\n') if line]
    try:
        if direction=='h':
            if start_x > 0 and lines[start_y][start_x-1] <> stopchar:
                # word doesn’t start here
                return None
            return lines[start_y][start_x:].split(stopchar)[0]
        elif direction=='v':
            if start_y > 0 and lines[start_y-1][start_x] <> stopchar:
                # word doesn’t start here
                return None
            return ''.join([line[start_x] for line in lines[start_y:]]).split(stopchar)[0]
    except IndexError, e:
        logger.warning('IndexError in _find_word with x=%d, y=%d, dir=%s: %s' % (start_x, start_y, direction, e))
    return None

def index(request, *args, **kwargs):
    context = {
        'MEDIA_URL':    settings.MEDIA_URL,
        'posted':       (request.method == 'POST'),
        'cloze_action': '',
    }
    if request.method == 'POST':
        context.update(_search(request, request.POST['cloze_searchterm']))
    else:
        context['dictionaries'] = _get_dictionaries(request)[0]
    return render(request, 'index.html', context)

def grid(request, *args, **kwargs):
    puzzle = None
    
    if (request.method == 'POST'):
        if ('maxcol' in request.POST and 'maxrow' in request.POST):
            maxcol = int(request.POST['maxcol'])
            maxrow = int(request.POST['maxrow'])
            if maxcol < settings.CROISEE_GRIDMIN_X: maxcol = settings.CROISEE_GRIDMIN_X
            if maxrow < settings.CROISEE_GRIDMIN_Y: maxrow = settings.CROISEE_GRIDMIN_Y
            if maxcol > settings.CROISEE_GRIDMAX_X: maxcol = settings.CROISEE_GRIDMAX_X
            if maxrow > settings.CROISEE_GRIDMAX_Y: maxrow = settings.CROISEE_GRIDMAX_Y
        else:
            maxcol = settings.CROISEE_GRIDMAX_X
            maxrow = settings.CROISEE_GRIDMAX_Y
        
        puzzle = {
            'maxcol':   maxcol,
            'maxrow':   maxrow,
            'maxnum':   0,
            'data':    [{'id':y, 'cols':[{'id':x, 'num':'', 'char':''} for x in range(maxcol)]} for y in range(maxrow)],
            'text':     '',
        }
        
    context = {
        'MEDIA_URL':    settings.MEDIA_URL,
        'posted':       (request.method == 'POST'),
        'puzzle':       puzzle,
        'defaultx':     settings.CROISEE_GRIDDEF_X,
        'defaulty':     settings.CROISEE_GRIDDEF_Y,
        'dictionaries': _get_dictionaries(request)[0],
        'cloze_action': 'ajax/DUMMY/',
    }
    return render(request, 'grid.html', context)

def save(request, *args, **kwargs):
    if request.method != 'POST':
        return redirect('%s-index' % settings.PROJECT_NAME)

    post = {}
    for key in request.POST:
        post[key.encode('ascii')] = request.POST[key]

    try:
        maxnum = int(post['maxnum'])
    except ValueError, e:
        maxnum = 0
    except KeyError, e:
        maxnum = 0
    try:
        maxcol = int(post['maxcol'])
        maxrow = int(post['maxrow'])
    except ValueError, e:
        logger.warning('ValueError in save: %s' % e)
        maxcol = 0
        maxrow = 0
    except KeyError, e:
        logger.warning('KeyError in save: %s' % e)
        maxcol = 0
        maxrow = 0
    if maxcol < settings.CROISEE_GRIDMIN_X: maxcol = settings.CROISEE_GRIDMIN_X
    if maxrow < settings.CROISEE_GRIDMIN_Y: maxrow = settings.CROISEE_GRIDMIN_Y
    if maxcol > settings.CROISEE_GRIDMAX_X: maxcol = settings.CROISEE_GRIDMAX_X
    if maxrow > settings.CROISEE_GRIDMAX_Y: maxrow = settings.CROISEE_GRIDMAX_Y

    word_starts = []
    
    p_text = '' # complete text of puzzle
    num = 0 # word start number counter

    for y in range(maxcol):
        for x in range(maxrow):
            coord = '%d_%d' % (y, x)
            c = post['char_'+coord]
            if c=='': c= ' '
            p_text += c[0].upper()
            if post['num_'+coord]:
                num += 1
                word_starts.append([num, y, x, ''])
        p_text += '\n'
    logger.info('\n'+p_text.replace('.', '#').replace(' ', u'·'))

    words_horiz = [None for i in range(num+1)]
    words_vert = [None for i in range(num+1)]
    
    for c in range(len(word_starts)):
        [num, y, x, dir] = word_starts[c]
        words_horiz[num] = _find_word(p_text, y, x, 'h')
        words_vert[num] = _find_word(p_text, y, x, 'v')
        if words_horiz[num]: dir += 'h'
        if words_vert[num]: dir += 'v'
        word_starts[c][3] = dir
        num += 1
    
    puzzle = {
        'maxcol':   maxcol,
        'maxrow':   maxrow,
        'maxnum':   maxnum,
        'text':     p_text,
        'data':     [{'id':y, 'cols':[{'id':x, 'num':post['num_%d_%d' % (y,x)], 'char':post['char_%d_%d' % (y,x)]} for x in range(maxcol)]} for y in range(maxrow)],
    }
    context = {
        'MEDIA_URL':    settings.MEDIA_URL,
        'posted':       (request.method == 'POST'),
        'puzzle':       puzzle,
        'defaultx':     settings.CROISEE_GRIDDEF_X,
        'defaulty':     settings.CROISEE_GRIDDEF_Y,
        'dictionaries': _get_dictionaries(request)[0],
        'cloze_action': 'ajax/DUMMY/',
    }
    return render(request, 'grid.html', context)

def ajax_clozequery(request, **kwargs):
    results = (_search(request, kwargs['cloze']),)
    results[0]['name'] = _('results')
    results[0]['direction'] = 'horizontal'
    return render(request, 'ajax_query.html', {'results':results})

def ajax_crossquery(request, **kwargs):
    """
    do a query for several words, separated by slashes
    
    if words are in format "word,0", the number says which letter of both words must match
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
        hres = set()
        vres = set()
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
    return render(request, 'ajax_query.html', {'results':results})
