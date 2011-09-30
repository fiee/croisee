#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unicodedata
import re, os
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User

REPLACEMENTS = (
# international characters that need more than just stripping accents
    (u'Ä', 'AE'),
    (u'Ö', 'OE'),
    (u'Ü', 'UE'),
    (u'ß', 'SS'),
    (u'Œ', 'OE'),
    (u'Æ', 'AE'),
    (u'Ø', 'OE'),
    #(u'', ''),
)
reASCIIonly = re.compile(r'[^A-Z]', re.I)
reCleanInput = re.compile(r'[^\w_%\?\*]', re.I)

def cleanword(word, strict=True):
    word = word.upper()
    for k,v in REPLACEMENTS:
        word = word.replace(k,v)
    word = unicodedata.normalize('NFD', word).encode('ASCII', 'ignore') # decompose international chars
    if strict:
        word = reASCIIonly.sub('', word)
    else:
        word = reCleanInput.sub('', word)
    return word

def splitwordline(line):
    """
    a line from a wordlist may contain word, description and priority, separated by tabs
    
    if description and priority are missing, default is the word and 0
    """
    parts = line.replace('\n','').split('\t')
    if len(parts)==1:
        parts.extend([parts[0],0])
    elif len(parts)==2:
        parts.append(0)
    elif len(parts)>3:
        parts = parts[0:2]
    if len(parts[1])<2:
        parts[1] = parts[0]
    try:
        parts[2] = int(parts[2])
    except ValueError, ex:
        parts[2] = 0
    parts[0] = cleanword(parts[0])
    return parts
    

class Dictionary(models.Model):
    """
    A dictionary
    """
    class Meta:
        verbose_name = _(u'Dictionary')
        verbose_name_plural = _(u'Dictionaries')
        ordering = ['language','name']
        unique_together = (('name','language'),)

    name = models.CharField(_(u'Name'), max_length=31, help_text=_(u'A short descriptive name'))
    public = models.BooleanField(_(u'public?'), default=True, help_text=_(u'May everyone use this dictionary?'))
    language = models.CharField(_(u'Language'), max_length=15, 
                                default=settings.LANGUAGE_CODE, choices=settings.LANGUAGES, 
                                help_text=_(u'Language of (most of) the words in this dictionary'))
    description = models.CharField(_(u'Description'), max_length=255, blank=True)
    owner = models.ForeignKey(User, verbose_name=_(u'Owner'))
    
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.language)

    def get_absolute_url(self):
        return '/dictionary/%d/' % self.id


class Word(models.Model):
    """
    A word with a description, according to a dictionary
    """
    class Meta:
        verbose_name = _(u'Word')
        verbose_name_plural = _(u'Words')
        ordering = ['word','priority']
        unique_together = (('word','dictionary'),)

    word = models.CharField(_(u'Word'), max_length=63, help_text=_(u'a word fitting a crossword puzzle; will become uppercased; no numbers, hyphens etc.'))
    dictionary = models.ForeignKey(Dictionary, verbose_name=_(u'Dictionary')) #, related_name="%(class)s_related")
    description = models.CharField(_(u'Description'), max_length=127, help_text=_(u'Meaning of the word within the context of the selected dictionary'))
    priority = models.SmallIntegerField(_(u'Priority'), default=0, help_text=_(u'0 is neutral, you can increase or decrease the priority'))
    
    def __unicode__(self):
        return "%s\t%s" % (self.word, self.description)
    
    def save(self, *args, **kwargs):
        self.word = cleanword(self.word)
        super(Word, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return '/dictionary/%d/%s/' % (self.dictionary.id, self.word)


class WordlistUpload(models.Model):
    """
    Wordlist importer
    """
    wordlist_file = models.FileField(_(u'wordlist file (.txt)'), upload_to=os.path.join(settings.MEDIA_ROOT, 'temp'),
                                help_text=_(u'Select a .txt file containing a single word per line to upload as a new dictionary.'))
    dictionary = models.ForeignKey(Dictionary, null=True, blank=True, help_text=_(u'Select a dictionary to add these words to. leave this empty to create a new dictionary from the supplied name.'))
    name = models.CharField(_(u'Name'), max_length=31, blank=True, help_text=_(u'A short descriptive name'))
    uniqueonly = models.BooleanField(_(u'only unique'), default=True, help_text=_(u'Import only words that are not contained in any other dictionary?'))
    public = models.BooleanField(_(u'public?'), default=True, help_text=_(u'May everyone use this dictionary?'))
    language = models.CharField(_(u'Language'), max_length=15, 
                                default=settings.LANGUAGE_CODE, choices=settings.LANGUAGES, 
                                help_text=_(u'Language of (most of) the words in this dictionary'))
    description = models.CharField(_(u'Description'), blank=True, max_length=255)
    owner = models.ForeignKey(User, verbose_name=_(u'Owner'))

    class Meta:
        verbose_name = _(u'wordlist upload')
        verbose_name_plural = _(u'wordlist uploads')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.wordlist_file)

    def save(self, *args, **kwargs):
        super(WordlistUpload, self).save(*args, **kwargs)
        dictionary = self.process_wordlist()
        super(WordlistUpload, self).delete()
        return dictionary

    def process_wordlist(self):
        if not os.path.isfile(self.wordlist_file.path):
            # TODO: throw exception?
            return None
        wordfile = file(self.wordlist_file.path, 'rU')
        lines = wordfile.readlines()
        wordfile.close()
        
        if self.dictionary:
            D = self.dictionary
        else:
            if not self.name:
                # TODO: throw exception?
                return false
            D = Dictionary.objects.create(
                name = self.name,
                public = self.public,
                language = self.language,
                description = self.description,
                owner = self.owner,
            )
        D.save()
        
        for line in lines:
            (newword, newdesc, newprio) = splitwordline(line.decode('utf-8'))
            # TODO: exception if decoding fails
            if len(newword)<2: continue
            try:
                if self.uniqueonly:
                    W = Word.objects.filter(word=newword, dictionary__language=D.language)
                    W = W[0]
                else:
                    W = Word.objects.get(word=newword, dictionary=D)
            except (Word.DoesNotExist, IndexError):
                W = Word.objects.create(word=newword, dictionary=D)
            if newdesc: W.description = newdesc
            if newprio: W.priority = newprio
            W.save()
                
        try:
            os.remove(self.wordlist_file.path)
        except Exception, ex:
            print ex
        
        return D

PUZZLE_TYPES = (
    ('d', _(u'default crossword puzzle with black squares')), # numbers and black squares in grid. only possible type ATM
    ('b', _(u'crossword puzzle with bars (no squares)')),
    ('s', _(u'Swedish crossword puzzle (questions in squares)')), # default in most magazines
    # other...
)

class Puzzle(models.Model):
    """
    """
    title = models.CharField(verbose_name=_(u'title'), max_length=255, blank=True, help_text=_(u'title or short description of this puzzle'))
    code = models.SlugField(verbose_name=_(u'code'), max_length=63, editable=False, unique=True, help_text=_(u'auto-generated URL code of this puzzle'))
    public = models.BooleanField(verbose_name=_(u'public'), default=True, help_text=_(u'Is this puzzle publicly viewable?'))
    language = models.CharField(verbose_name=_(u'language'), max_length=7, default=settings.LANGUAGE_CODE, help_text=_(u'main language of this puzzle'), choices=settings.LANGUAGES)

    owner = models.ForeignKey(User, verbose_name=_(u'owner'), help_text=_(u'owner of the puzzle'))
    createdby = models.ForeignKey(User, verbose_name=_(u'created by'), related_name='+', editable=False, help_text=_(u'user that saved the puzzle for the first time (may be anonymous)'))
    lastchangedby = models.ForeignKey(User, verbose_name=_(u'last changed by'), related_name='+', editable=False, help_text=_(u'user that saved the puzzle the latest time'))
    createdon = models.DateTimeField(verbose_name=_(u'created on'), auto_now_add=True, help_text=_(u'timestamp of creation (first save)'))
    lastchangedon = models.DateTimeField(verbose_name=_(u'last changed on'), auto_now=True, help_text=_(u'timestamp of last change'))
    
    type = models.CharField(verbose_name=_(u'type'), max_length=1, default='d', editable=False, help_text=_(u'type of this puzzle'), choices=PUZZLE_TYPES)
    width = models.PositiveSmallIntegerField(verbose_name=_(u'width'), default=settings.CROISEE_GRIDDEF_X, help_text=_(u'width of the puzzle (number of characters)'))
    height = models.PositiveSmallIntegerField(verbose_name=_(u'height'), default=settings.CROISEE_GRIDDEF_Y, help_text=_(u'height of the puzzle (number of characters)'))
    text = models.TextField(verbose_name=_(u'text'), blank=True, help_text=_(u'characters of the puzzle (solution)'))
    numbers = models.TextField(verbose_name=_(u'numbers'), blank=True, help_text=_(u'list of coordinates of word start numbers')) # x,y,num\n
    questions = models.TextField(verbose_name=_(u'questions'), blank=True, help_text=_(u'list of questions')) # 1::h::Description\n

    class Meta:
        verbose_name = _(u'crossword puzzle')
        verbose_name_plural = _(u'crossword puzzles')

    def __unicode__(self):
        return "%s (%s)" % (self.code, self.title)
    
    def get_absolute_url(self):
        return '/puzzle/%s/' % self.code
