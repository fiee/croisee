#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext
from django.views.generic import View, TemplateView, ListView
from croisee.models import Dictionary, Word, Puzzle, cleanword
from croisee.middleware import Http403
from datetime import datetime
from hashlib import md5
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
    Get all dictionaries that the user may access and didn't disable.
    
    requires:
    request.POST
    
    returns: tuple
        queryset of dictionaries,
        list of disabled dictionary ids 
    """
    dictionaries = Dictionary.objects.filter(Q(public=True)|Q(owner=request.user.id)) # public or own
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
    Search after a searchterm and return a dict of information.
    
    wildcards allowed: * % ? _
    
    returns: dict
        :dictionaries : queryset of Dictionaries
        :results      : list of matching Words
        :resultcount  : number of matches
        :searchterm   : cleaned searchterm
        :found        : found anything at all? (bool)
        
    If the word contains no wildcards and is unknown,
    it is given back in results with the description 
    being the word in title case!
    """
    dictionaries = _get_dictionaries(request)
    context = {
        'dictionaries': dictionaries[0],
        'results':      [],
        'resultcount':  0,
        'searchterm':   '',
        'found': True,
    }
    try:
        searchterm = cleanword(searchterm, False).upper()
        internal = searchterm.replace('?','_').replace('*','%').replace('%','%%')
        if not ('_' in internal or '%%' in internal): # without wildcards = no search needed
            if request.user.is_staff: # TODO: we need better permission handling!
                context['results'] = Word.objects.filter(word=internal).exclude(dictionary__id__in=dictionaries[1])[:limit]
            else:
                context['results'] = Word.objects.filter(word=internal, dictionary__public=True).exclude(dictionary__id__in=dictionaries[1])[:limit]
            if not context['results']: # new word
                context['results'] = [ Word(word=internal, description=searchterm.title()) ]
                context['found'] = False
        else:
            if request.user.is_staff:
                context['results'] = Word.objects.extra(where=['word LIKE "'+internal+'"']).exclude(dictionary__id__in=dictionaries[1])[:limit]
            else:
                context['results'] = Word.objects.extra(where=['word LIKE "'+internal+'"']).filter(dictionary__public=(not request.user.is_staff)).exclude(dictionary__id__in=dictionaries[1])[:limit]
        # TODO: dictionaries in selected (hu??)
        context['resultcount'] = len(context['results'])
        context['found'] = (context['found'] and (context['resultcount']>0))
        context['searchterm'] = searchterm
    except (KeyError, Word.DoesNotExist), ex:
        pass
    return context

def _find_word(text, start_y, start_x, direction='h', stopchar='.', newline='\n'):
    """
    Find a word in a text, starting at position y, x (0-based).
    
    params:
    :text             : puzzle characters
    :start_y, start_x : coordinates of the first letter of the word in the text (0-based)
    :direction        : h or v
    :stopchar         : character that marks a block (word divider) in the puzzle text
    :newline          : character that marks a new line in the puzzle text
    
    returns:
    found word or None on error or if the word doesn’t start at the given coordinates
    """
    lines = [line for line in text.split(newline) if line]
    try:
        if direction=='h':
            if start_x > 0 and lines[start_y][start_x-1] <> stopchar:
                # word doesn’t start here
                print u"word doesn’t start at",start_x,start_y,direction
                return None
            return lines[start_y][start_x:].split(stopchar)[0]
        elif direction=='v':
            if start_y > 0 and lines[start_y-1][start_x] <> stopchar:
                # word doesn’t start here
                print u"word doesn’t start at",start_x,start_y,direction
                return None
            return ''.join([line[start_x] for line in lines[start_y:]]).split(stopchar)[0]
    except IndexError, e:
        logger.warning(u'IndexError in _find_word with x=%d, y=%d, dir=%s: %s' % (start_x, start_y, direction, e))
    return None

def _find_word_by_num(text, nums, num, direction='h'):
    """
    Find a word in a text by its question number.
    
    params:
    :text: puzzle characters
    :nums: request string of question numbers like 'y.x.num,y.x.num' (0-based)
    :num:  question number of word to look for (0-based)
    :direction: h or v
    
    returns:
    see `_find_word`
    """
    # split by comma, split by dot, get coordinates by num
    #y,x = dict(map(lambda t: (int(t[2]), (int(t[0]), int(t[1]))),(e.split('.') for e in nums.strip(' ,').split(','))))[int(num)]
    try:
        y,x = [ e.split('.')[0:2] for e in nums.strip(' ,').split(',') if int(e.split('.')[2])-1 == int(num) ][0]
    except IndexError, e:
        logger.error(u'Can’t find word no.%s with "%s"\n%s' % (num, nums, e))
        return None
    return _find_word(text, int(y), int(x), direction).strip()

def grid(request, *args, **kwargs):
    """
    Grid view
    """
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
            'questions': '',
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
    """
    Save grid view.

    TODO: combine with grid view, use proper form (validation)
    """
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
    #logger.info('\n'+p_text.replace('.', '#').replace(' ', u'·'))
    #logger.info(post.get('nums', ''))

    puzzle = {
        'maxcol':   maxcol,
        'maxrow':   maxrow,
        'maxnum':   maxnum,
        'text':     p_text, #.replace('\n', '/'),
        'nums':     post.get('nums', ''),
        'hash':     post.get('hash', ''),
        'questions': post.get('questions', ''),
    }

    # if a user is logged in, check if her words and questions are already in the database;
    # if not, save them to her personal dictionary
    if request.user.is_active:
        dictionaries = Dictionary.objects.filter(Q(public=True)|Q(owner=request.user.id)) # list of all allowed dictionaries
        personal_dict, is_new = Dictionary.objects.get_or_create(owner=request.user, name=settings.CROISEE_PERSONALDICT_NAME)
        if is_new:
            personal_dict.description = _(u'personal dictionary of user %s, do not rename!') % request.user.username
            personal_dict.save()
            logger.info(_(u'Personal dictionary for user %(username)s was created as %(dictname)s.') % 
                        {'username':request.user.username, 'dictname':settings.CROISEE_PERSONALDICT_NAME})
        for qu in puzzle['questions'].split('\n'):
            parts = qu.strip().split('::') # questions are in the format "1::h::Word"
            if (not qu) or (not parts) or len(parts)!=3: continue # ignore empty or incomplete lines
            (num, dir, question) = parts
            up_question = question.upper()
            if len(question)>3 and question != up_question: # we ignore questions that are too short or the same as the word
                word = _find_word_by_num(p_text, puzzle['nums'], num, dir) # find the word for the question
                if word and (up_question != word.upper()) and not '_' in word and not ' ' in word:
                    # TODO: lookup is expensive! convert to background task!
                    if request.user.is_staff:
                        results = Word.objects.filter(word=word)
                    else:
                        results = Word.objects.filter(word=word, dictionary__public=True)[:settings.CROISEE_QUERYMAX]
                    is_new = True
                    for res in results:
                        if res.description.upper() == up_question:
                            is_new = False
                    if is_new or len(results)==0:
                        new_word, is_new = Word.objects.get_or_create(word=word, dictionary=personal_dict)
                        new_word.description=question
                        new_word.save()
                        if is_new:
                            logger.info(_(u'Word %(word)s with question “%(question)s” was saved to your personal dictionary.') % 
                                        {'word':word, 'question':question})
                        else:
                            logger.info(_(u'Word “%(word)s” with question “%(question)s” was updated in your personal dictionary.') % 
                                        {'word':word, 'question':question})

    # TODO: save puzzle to database, redirect to hash url
    if not puzzle['hash']:
        puzzle['hash'] = md5('%s/%s' % (request.META.get('REMOTE_ADDR', '127.0.0.1'), datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S'))).hexdigest() 
        
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

class PuzzleView(TemplateView):
    model = Puzzle
    template_name = 'grid.html'
    
    def _get_dictionaries(self):
        """
        Get all dictionaries that the user may access and didn't disable.
        
        requires:
        list of 'dic_#' in request.POST
        
        returns: tuple
            queryset of dictionaries,
            list of disabled dictionary ids 
        """
        if not hasattr(self, 'dictionaries'):
            self.dictionaries = Dictionary.objects.filter(Q(public=True)|Q(owner=self.request.user.id)) # public or own
        if self.request.method == 'POST':
            self.disabled_dictionaries = []
            for d in self.dictionaries:
                if 'dic_%d' % d.id not in self.request.POST:
                    d.disabled = True
                    self.disabled_dictionaries.append(d.id)
        else:
            self.disabled_dictionaries = []
        return (self.dictionaries, self.disabled_dictionaries)
    
    def _search(self, searchterm, limit=settings.CROISEE_QUERYMAX):
        """
        Search after a searchterm and return a dict of information.
        
        wildcards allowed: * % ? _
        
        returns: dict
            :dictionaries : queryset of Dictionaries
            :results      : list of matching Words
            :resultcount  : number of matches
            :searchterm   : cleaned searchterm
            :found        : found anything at all? (bool)
            
        If the word contains no wildcards and is unknown,
        it is given back in results with the description 
        being the word in title case!
        """
        if not hasattr(self, 'dictionaries'):
            self._get_dictionaries()
        context = {
            'dictionaries': self.dictionaries,
            'results':      [],
            'resultcount':  0,
            'searchterm':   '',
            'found': True,
        }
        try:
            searchterm = cleanword(searchterm, False).upper()
            internal = searchterm.replace('?','_').replace('*','%').replace('%','%%')
            if not ('_' in internal or '%%' in internal): # without wildcards = no search needed
                if self.request.user.is_staff: # TODO: we need better permission handling!
                    context['results'] = Word.objects.filter(word=internal).exclude(dictionary__id__in=self.disabled_dictionaries)[:limit]
                else:
                    context['results'] = Word.objects.filter(word=internal, dictionary__public=True).exclude(dictionary__id__in=self.disabled_dictionaries)[:limit]
                # Here we add a unknown word as result - we should probably make that optional
                if not context['results']: # new word
                    context['results'] = [ Word(word=internal, description=searchterm.title()), ]
                    context['found'] = False
            else:
                if self.request.user.is_staff:
                    context['results'] = Word.objects.extra(where=['word LIKE "'+internal+'"']).exclude(dictionary__id__in=self.disabled_dictionaries)[:limit]
                else:
                    context['results'] = Word.objects.extra(where=['word LIKE "'+internal+'"']).filter(dictionary__public=(not self.request.user.is_staff)).exclude(dictionary__id__in=self.disabled_dictionaries)[:limit]
            context['resultcount'] = len(context['results'])
            context['found'] = (context['found'] and (context['resultcount']>0))
            context['searchterm'] = searchterm
        except (KeyError, Word.DoesNotExist), e:
            # We silently ignore wrong postings or empty results
            pass
        return context
    
    def _find_word(self, text, start_y, start_x, direction='h', stopchar='.', newline='\n'):
        """
        Find a word in a text, starting at position y, x (0-based).
        
        params:
        :text             : puzzle characters
        :start_y, start_x : coordinates of the first letter of the word in the text (0-based)
        :direction        : h or v
        :stopchar         : character that marks a block (word divider) in the puzzle text
        :newline          : character that marks a new line in the puzzle text
        
        returns:
        found word or None on error or if the word doesn’t start at the given coordinates
        """
        lines = [line for line in text.split(newline) if line]
        try:
            if direction=='h':
                if start_x > 0 and lines[start_y][start_x-1] <> stopchar:
                    # word doesn’t start here
                    print u"word doesn’t start at",start_x,start_y,direction
                    return None
                return lines[start_y][start_x:].split(stopchar)[0]
            elif direction=='v':
                if start_y > 0 and lines[start_y-1][start_x] <> stopchar:
                    # word doesn’t start here
                    print u"word doesn’t start at",start_x,start_y,direction
                    return None
                return ''.join([line[start_x] for line in lines[start_y:]]).split(stopchar)[0]
        except IndexError, e:
            logger.warning(u'IndexError in _find_word with x=%d, y=%d, dir=%s: %s' % (start_x, start_y, direction, e))
        return None
    
    def _find_word_by_num(self, text, nums, num, direction='h'):
        """
        Find a word in a text by its question number.
        
        params:
        :text: puzzle characters
        :nums: request string of question numbers like 'y.x.num,y.x.num' (0-based)
        :num:  question number of word to look for (0-based)
        :direction: h or v
        
        returns:
        see `_find_word`
        """
        # split by comma, split by dot, get coordinates by num
        #y,x = dict(map(lambda t: (int(t[2]), (int(t[0]), int(t[1]))),(e.split('.') for e in nums.strip(' ,').split(','))))[int(num)]
        try:
            y,x = [ e.split('.')[0:2] for e in nums.strip(' ,').split(',') if int(e.split('.')[2])-1 == int(num) ][0]
        except IndexError, e:
            logger.error(u'Can’t find word no.%s with "%s"\n%s' % (num, nums, e))
            return None
        return _find_word(text, int(y), int(x), direction).strip()

    def _get_puzzle(self, hash_id=None):
        if not hash_id and 'hash' in self.kwargs:
            hash_id = self.kwargs['hash']
        self.puzzle = Puzzle.get(code=hash_id)
        if not self.puzzle.public and self.puzzle.owner != self.request.user and not self.request.user.is_superuser:
            # TODO: proper permissions handling
            raise Http403
        return self.puzzle

    def get_context_data(self, **kwargs):
        """
        A lot of request handling happens here. Is that good?
        """
        context = super(PuzzleView, self).get_context_data(**kwargs)
        context['MEDIA_URL'] = settings.MEDIA_URL
        context['posted'] = (self.request.method == 'POST')
        context['cloze_action'] = ''
        context['defaultx'] = settings.CROISEE_GRIDDEF_X
        context['defaulty'] = settings.CROISEE_GRIDDEF_Y
        if self.request.method == 'POST' and 'cloze_searchterm' in self.request.POST:
            context.update(self._search(self.request.POST['cloze_searchterm']))
        else:
            context['dictionaries'] = self._get_dictionaries()[0]
        if 'hash' in self.kwargs:
            context['puzzle'] = self._get_puzzle()
        return context    

class IndexView(PuzzleView):
    template_name = 'index.html'

class AjaxClozeQueryView(PuzzleView): 
    """
    Search for one word and return HTML.
    
    kwargs:
    :cloze: the pattern to look for
    
    returns rendered ajax_query.html (result list)
    """
    template_name = 'ajax_query.html'

    def get_context_data(self, **kwargs):
        context = super(AjaxClozeQueryView, self).get_context_data(**kwargs)
        results = (self._search(self.kwargs['cloze']),)
        results[0]['name'] = _('results')
        results[0]['direction'] = 'horizontal'
        context['results'] = results
        return context

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

class AjaxCrossQueryView(PuzzleView): 
    """
    Query for several words, separated by slashes, and return HTML.
    
    If words are in format "word,0", the number says which letter of both words must match (0-based),
    i.e. "P___ON,1" and "JQ____,5" match at "Y".
    Only matching words are returned.
    
    kwargs:
    :horizontal, vertical: crossing cloze patterns

    returns rendered ajax_query.html (double result list)
    """
    template_name = 'ajax_query.html'

    def get_context_data(self, **kwargs):
        context = super(AjaxCrossQueryView, self).get_context_data(**kwargs)

        horiz = kwargs['horizontal']
        vert = kwargs['vertical']
        try:
            hl = int(self.kwargs['hletter'])
            vl = int(self.kwargs['vletter'])
        except TypeError:
            hl = None
            vl = None
        if hl is not None and vl is not None and len(horiz)>hl and len(vert)>vl:
            # if we got valid positionals
            results = (self._search(horiz, 1024), self._search(vert, 1024)) # "no" limit
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
            results = (self._search(horiz), self._search(vert)) # default limit
        results[0]['direction'] = 'horizontal'
        results[1]['direction'] = 'vertical'
        results[0]['name'] = _('horizontal')
        results[1]['name'] = _('vertical')
        context['results'] = results
        return context

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

class WordListView(ListView):
    model = Word
    template_name = 'dictionary_word_list.html'
    paginate_by = 50

    def _get_dictionary(self):
        if not hasattr(self, 'dictionary'):
            self.dictionary = None
        if 'object_id' in self.kwargs:
            if not self.dictionary or self.dictionary.id != int(self.kwargs['object_id']):
                d = get_object_or_404(Dictionary, pk=int(self.kwargs['object_id']))
            else:
                d = self.dictionary
            if not (d.public or d.owner==self.request.user or self.request.user.is_superuser):
                self.dictionary = None
                raise Http403
            else:
                self.dictionary = d
        elif self.request.user.is_active:
            personal_dict, is_new = Dictionary.objects.get_or_create(owner=self.request.user, name=settings.CROISEE_PERSONALDICT_NAME)
            if is_new:
                personal_dict.description = _(u'personal dictionary of user %s, do not rename!') % self.request.user.username
                personal_dict.save()
            self.dictionary = personal_dict
        else:
            self.dictionary = None
            raise Http404
        return self.dictionary

    def get_context_data(self, **kwargs):
        context = super(WordListView, self).get_context_data(**kwargs)
        context['dictionary'] = self.dictionary or self._get_dictionary()
        return context    

    def get_queryset(self):
        return Word.objects.filter(dictionary=self._get_dictionary())
