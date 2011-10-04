#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
from hashlib import md5
import logging
from django.conf import settings
from django.contrib.auth.models import User
#from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import DeleteView, CreateView, SingleObjectTemplateResponseMixin, ModelFormMixin, ProcessFormView
from djangorestframework.views import View
from croisee.models import Dictionary, Word, Puzzle, cleanword
from croisee.forms import PuzzleForm
from croisee.middleware import Http403

logger = logging.getLogger(settings.PROJECT_NAME)


class DictionaryMixin(object):
    """
    Mixin for View-based classes to handle dictionary access and lookups
    """
    
    def get_dictionaries(self, ignore_post=False):
        """
        Get all dictionaries that the user may access and didn't disable.
        Return a tuple of dictionaries (queryset) and disabled dictionaries (list of IDs).
        
        The basic set of dictionaries are all public ones and all owned by the user.
        If `request.method` is 'POST', then look for a list of 'dic_#' and disable
        all dictionaries that aren’t in there. (Because they come from a set of
        checkboxes and show only up if enabled.)
        If `ignore_post` is True, don’t care about `request.method`.
        
        returns: tuple
            queryset of dictionaries,
            list of disabled dictionary ids 
        """
        if not hasattr(self, 'dictionaries'):
            self.dictionaries = Dictionary.objects.filter(Q(public=True)|Q(owner=self.request.user.id)) # public or own
        if not ignore_post and self.request.method == 'POST':
            self.disabled_dictionaries = []
            for d in self.dictionaries:
                if 'dic_%d' % d.id not in self.request.POST:
                    d.disabled = True
                    self.disabled_dictionaries.append(d.id)
        else:
            self.disabled_dictionaries = []
        return (self.dictionaries, self.disabled_dictionaries)
    
    def search(self, searchterm, limit=settings.CROISEE_QUERYMAX):
        """
        Search after a searchterm and return a dict of information.
        Limit the list of results to a maximum of `limit`.
        
        Wildcards allowed: * % ? _
        
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
            self.get_dictionaries()
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
    
    def ensure_personal_dictionary(self, create=True):
        """
        Return the user’s personal dictionary, if user is active.
        If it doesn’t exist (and create is True), create it.
        """
        user = self.request.user
        if not user.is_active:
            return None
        if not (hasattr(self, 'personal_dictionary') and isinstance(self.personal_dictionary, Dictionary)):
            if not create:
                self.personal_dictionary = Dictionary.objects.get(owner=user, name=user.username)
            else:
                self.personal_dictionary, is_new = Dictionary.objects.get_or_create(owner=user, name=user.username)
                if is_new:
                    self.personal_dictionary.description = _(u'personal dictionary of user %s, do not rename!') % user.username
                    self.personal_dictionary.public = False
                    # TODO: language?
                    self.personal_dictionary.save()
                    logger.info(_(u'Personal dictionary for user %(username)s was created.') % 
                                {'username': user.username})
        return self.personal_dictionary
    
    def find_word(self, text, start_y, start_x, direction='h', stopchar='.', newline='\n'):
        """
        Return the word from `text`, starting at position y, x (0-based).
        
        params:
        :text             : puzzle characters
        :start_y, start_x : coordinates of the first letter of the word in the text (0-based)
        :direction        : h or v
        :stopchar         : character that marks a block (word divider) in the puzzle text
        :newline          : character that marks a new line in the puzzle text
        
        returns:
        found word or None on error or if no word starts at the given coordinates
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
    
    def find_word_by_num(self, text, numbers, num, direction='h'):
        """
        Return the word from `text` by its question number.
        
        params:
        :text: puzzle characters
        :numbers: request string of question numbers like 'y.x.num,y.x.num' (0-based)
        :num:  question number of word to look for (0-based)
        :direction: h or v
        
        returns:
        see `find_word`
        """
        # split by comma, split by dot, get coordinates by num
        try:
            #y,x = dict(map(lambda t: (int(t[2]), (int(t[0]), int(t[1]))),(e.split('.') for e in nums.strip(' ,').split(','))))[int(num)]
            y,x = [ e.split('.')[0:2] for e in numbers.strip(' ,').split(',') if int(e.split('.')[2])-1 == int(num) ][0]
        except IndexError, e:
            logger.error(u'Can’t find word no.%s with "%s"\n%s' % (num, numbers, e))
            return None
        ret = self.find_word(text, int(y), int(x), direction)
        if ret:
            return ret.strip()
        else:
            return None

    def save_words(self, text, questions, numbers):
        """
        Save new words/questions from the puzzle to the database.
        Return the number of new or changed words.
        
        If a user is logged in, check if her words and questions are already in the database;
        if not, save them to her personal dictionary.
        """
        user = self.request.user
        word_count = 0
        if user.is_active and self.ensure_personal_dictionary():
            # iterate questions
            for qu in questions.split('\n'):
                parts = qu.strip().split('::') # questions are in the format "1::h::Word"
                if (not qu) or (not parts) or len(parts)!=3: continue # ignore empty or incomplete lines
                (num, dir, question) = parts
                up_question = question.upper()
                if len(question)>3 and question != up_question: # we ignore questions that are too short or the same as the word
                    word = self.find_word_by_num(text, numbers, num, dir) # find the word for the question
                    if word and (up_question != word.upper()) and not '_' in word and not ' ' in word:
                        # TODO: lookup is expensive! convert to background task!
                        if user.is_staff: # TODO: permissions
                            results = Word.objects.filter(word=word)
                        else:
                            results = Word.objects.filter(word=word, dictionary__public=True)[:settings.CROISEE_QUERYMAX]
                        is_new = True
                        for res in results:
                            if res.description.upper() == up_question:
                                is_new = False
                        if is_new or len(results)==0:
                            new_word, is_new = Word.objects.get_or_create(word=word, dictionary=self.personal_dictionary)
                            new_word.description=question
                            new_word.save()
                            word_count += 1
                            if is_new:
                                logger.info(_(u'Word %(word)s with question “%(question)s” was saved to your personal dictionary.') % 
                                            {'word':word, 'question':question})
                            else:
                                logger.info(_(u'Word “%(word)s” with question “%(question)s” was updated in your personal dictionary.') % 
                                            {'word':word, 'question':question})
        else:
            logger.info(_(u'Don’t save any words, since user %s is not active.') % user.username)
        return word_count

class IndexView(TemplateView):
    template_name = 'index.html'

class DeletePuzzleView(DeleteView):
    model = Puzzle
    form_class = PuzzleForm
    template_name = 'grid.html'
    success_url = '/puzzle/' #reverse('croisee-puzzle-new')
    slug_field = 'code' # but code must come in 'slug' kwarg!
    #context_object_name = 'puzzle'
    # TODO: permissions

class NewPuzzleView(CreateView, DictionaryMixin):
    model = Puzzle
    form_class = PuzzleForm
    template_name = 'grid.html'
    #success_url = '' # default: get_absolute_url
    slug_field = 'code' # but code must come in 'slug' kwarg!
    #context_object_name = 'puzzle'

    def new_hash_id(self):
        """
        Create a new MD5 hash id from remote IP and current time.
        """
        return md5('%s/%s' % (self.request.META.get('REMOTE_ADDR', '127.0.0.1'), datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S'))).hexdigest()
    
    def get_user(self):
        if isinstance(self.request.user, type(User)):
            return self.request.user
        else:
            return User.objects.get(pk=settings.CROISEE_DEFAULT_OWNER_ID)

    def get_initial(self):
        return {
                'width': settings.CROISEE_GRIDMIN_X,
                'height': settings.CROISEE_GRIDMIN_Y,
                'code': self.new_hash_id(),
                'title': '',
                'text': '',
                'numbers': '',
                'questions': '',
                'owner': self.get_user(),
                'language': settings.LANGUAGE_CODE,
                }

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """
        if not self.object and self.request.method=='POST':
            self.get_object()
        return super(NewPuzzleView, self).get_form_kwargs()

    def get_object(self, queryset=None):
        """
        Return a new puzzle object.
        Override get_object from SingleObjectMixin.
        """
        self.object = Puzzle(**self.get_initial())
        return self.object

    def get_context_data(self, **kwargs):
        context = super(NewPuzzleView, self).get_context_data(**kwargs)
        context['default_x'] = settings.CROISEE_GRIDDEF_X
        context['default_y'] = settings.CROISEE_GRIDDEF_Y
        context['dictionaries'] = self.get_dictionaries()[0]
        return context    


class PuzzleView(DictionaryMixin, SingleObjectTemplateResponseMixin, ModelFormMixin, ProcessFormView):
    model = Puzzle
    form_class = PuzzleForm
    template_name = 'grid.html'
    #success_url = '' # default: get_absolute_url
    slug_field = 'code' # but code must come in 'slug' kwarg!
    #context_object_name = 'puzzle'

    def new_hash_id(self):
        """
        Create a new MD5 hash id from remote IP and current time.
        """
        return md5('%s/%s' % (self.request.META.get('REMOTE_ADDR', '127.0.0.1'), datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S'))).hexdigest()
        
    def get_object(self, queryset=None):
        if 'slug' in self.kwargs:
            hash_id = self.kwargs['slug']
        else:
            hash_id = self.request.POST.get('code', None)
        if hasattr(self, 'object') and ((not hash_id) or hash_id == self.object.code):
            return self.object
        user = self.get_user()
        owner = user
        if owner != self.request.user and not self.request.user.is_active:
            # an unknown or anonymous user cannot become an owner
            owner = User.objects.get(pk=settings.CROISEE_DEFAULT_OWNER_ID)
        try:
            self.object = Puzzle.objects.get(code=hash_id)
        except Puzzle.DoesNotExist, e:
            logger.info('puzzle "%s" not found, creating new puzzle' % hash_id)
            hash_id = self.request.POST.get('code', self.new_hash_id())
            self.object = Puzzle(
                public = True, #(not self.request.user.is_active),
                code = hash_id,
                owner = owner,
                createdby = user,
                createdon = datetime.now(),
                height = max(min(int(self.request.POST.get('width', settings.CROISEE_GRIDMIN_Y)), settings.CROISEE_GRIDMAX_Y), settings.CROISEE_GRIDMIN_Y),
                width = max(min(int(self.request.POST.get('height', settings.CROISEE_GRIDMIN_X)), settings.CROISEE_GRIDMAX_X), settings.CROISEE_GRIDMIN_X),
                text = self.request.POST.get('text', '').upper(),
                numbers = self.request.POST.get('numbers', ''),
                questions = self.request.POST.get('questions', ''),
            )
        if (not self.object.public) and (self.object.owner != self.request.user) and (not self.request.user.is_superuser):
            # TODO: proper permissions handling
            logger.warning('user "%s" must not access puzzle "%s", owned by "%s"!' % (self.request.user, hash_id, self.object.owner))
            raise Http403
        self.object.lastchangedby = user
        self.object.lastchangedon = datetime.now()
        return self.object
    
    def get_user(self):
        if isinstance(self.request.user, type(User)):
            return self.request.user
        else:
            return User.objects.get(pk=settings.CROISEE_DEFAULT_OWNER_ID)
    
    def save_puzzle(self, **kwargs):
        # TODO: permissions
        if not (hasattr(self, 'object') and isinstance(self.object, Puzzle)):
            self.get_object()
        self.object.lastchangedby = self.get_user()
        self.object.lastchangedon = datetime.now()
        self.save_words(self.object.text, self.object.questions, self.object.numbers) # TODO: background task?
        logger.info('save_puzzle: %s' % self.object)
        return self.object.save(**kwargs)

    def form_invalid(self, form):
        logger.warn('form is invalid!\n%s' % form.errors)
        return super(PuzzleView, self).form_invalid(form)

    def form_valid(self, form):
        """
        Beware, doesn’t call super() to avoid multiple saving!
        
        TODO: compare with get_object
        """
        new_object = form.save(commit=False)
        for field in ('title', 'text', 'questions', 'numbers', 'width', 'height'):
            #logger.info('setting %s to:\n%s' % (field, getattr(new_object, field)))
            setattr(self.object, field, getattr(new_object, field))
        logger.info('form_valid: %s' % self.object)
        self.save_puzzle()
        return self.render_to_response(self.get_context_data(form=form)) #HttpResponseRedirect(self.get_success_url())

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instanciating the form.
        """
        if (not hasattr(self, 'object') or not self.object) and self.request.method=='POST':
            self.get_object()
        return super(PuzzleView, self).get_form_kwargs()

    def get_context_data(self, **kwargs):
        context = super(PuzzleView, self).get_context_data(**kwargs)
        #context['posted'] = (self.request.method == 'POST')
        context['default_x'] = settings.CROISEE_GRIDDEF_X
        context['default_y'] = settings.CROISEE_GRIDDEF_Y
        context['dictionaries'] = self.get_dictionaries()[0]
        return context    
    
    def get(self, request, *args, **kwargs):
        if 'slug' in kwargs:
            self.get_object()
        return super(PuzzleView, self).get(request, *args, **kwargs)

#    def post(self, request, *args, **kwargs):
#        self.save_puzzle()
#        return super(PuzzleView, self).post(request, *args, **kwargs)

class SavePuzzleView(PuzzleView):

    def post(self, request, *args, **kwargs):
        self._save_puzzle()
        return self.get(request, *args, **kwargs)
    

class AjaxClozeQueryView(TemplateView, DictionaryMixin): 
    """
    Search for one word and return HTML.
    
    kwargs:
    :cloze: the pattern to look for
    
    returns rendered ajax_query.html (result list)
    """
    template_name = 'ajax_query.html'

    def get_context_data(self, **kwargs):
        context = super(AjaxClozeQueryView, self).get_context_data(**kwargs)
        results = (self.search(self.kwargs['cloze']),)
        results[0]['name'] = _('results')
        results[0]['direction'] = 'horizontal'
        context['results'] = results
        return context

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)

class AjaxCrossQueryView(TemplateView, DictionaryMixin): 
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
            results = (self.search(horiz, 1024), self.search(vert, 1024)) # "no" limit
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
            results = (self.search(horiz), self.search(vert)) # default limit
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
            self.personal_dictionary, is_new = Dictionary.objects.get_or_create(owner=self.request.user, name=settings.CROISEE_PERSONALDICT_NAME)
            if is_new:
                self.personal_dictionary.description = _(u'personal dictionary of user %s, do not rename!') % self.request.user.username
                self.personal_dictionary.save()
            self.dictionary = self.personal_dictionary
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
