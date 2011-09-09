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

def _find_word(text, start_y, start_x, direction='h', stopchar='.', newline='\n'):
    """
    find a word in a text, starting at position y, x (0-based)
    
    direction is h or v
    """
    lines = [line for line in text.split(newline) if line]
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
        maxcol = max(min(int(request.POST.get('new_maxcol', settings.CROISEE_GRIDMIN_X)), settings.CROISEE_GRIDMAX_X), settings.CROISEE_GRIDMIN_X)
        maxrow = max(min(int(request.POST.get('new_maxrow', settings.CROISEE_GRIDMIN_Y)), settings.CROISEE_GRIDMAX_Y), settings.CROISEE_GRIDMIN_Y)
        p_text = request.POST.get('chars', '').upper()
        p_nums = request.POST.get('nums', '')
        
        puzzle = {
            'maxcol':   maxcol,
            'maxrow':   maxrow,
            'maxnum':   0,
            'text':     p_text,
            'nums':     p_nums,
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
        maxnum = int(post.get('maxnum', 0))
    except ValueError, e:
        maxnum = 0
    try:
        maxcol = max(min(int(post.get('maxcol', settings.CROISEE_GRIDMIN_X)), settings.CROISEE_GRIDMAX_X), settings.CROISEE_GRIDMIN_X)
        maxrow = max(min(int(post.get('maxrow', settings.CROISEE_GRIDMIN_Y)), settings.CROISEE_GRIDMAX_Y), settings.CROISEE_GRIDMIN_Y)
    except ValueError, e:
        logger.warning('ValueError in save: %s' % e)
        maxcol = settings.CROISEE_GRIDMIN_X
        maxrow = settings.CROISEE_GRIDMIN_Y

    p_text = post.get('chars', '').upper().replace('/', '\n') # complete text of puzzle
    logger.info('\n'+p_text.replace('.', '#').replace(' ', u'·'))
    logger.info(post.get('nums', ''))

    puzzle = {
        'maxcol':   maxcol,
        'maxrow':   maxrow,
        'maxnum':   maxnum,
        'text':     p_text.replace('\n', '/'),
        'nums':     post.get('nums', ''),
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
