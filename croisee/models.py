#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unicodedata
import re, os
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.template.loader import render_to_string
from django.conf import settings

REPLACEMENTS = (
# international characters that need more than just stripping accents
    (u'Ä', 'AE'),
    (u'Ö', 'OE'),
    (u'Ü', 'UE'),
    (u'ß', 'SS'),
)
reASCIIonly = re.compile(r'[^A-Z]+', re.I)

def cleanword(word):
    word = word.upper()
    for k,v in REPLACEMENTS:
        word = word.replace(k,v)
    word = unicodedata.normalize('NFD', word).encode('ASCII', 'ignore') # decompose international chars
    word = reASCIIonly.sub('', word)
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
    try:
        parts[2] = int(parts[2])
    except ValueError, ex:
        parts[2] = 0
    parts[0] = cleanword(parts[0])
    return parts
    

class Word(models.Model):
    """
    A word
    """

    class Meta:
        verbose_name = _(u'Word')
        verbose_name_plural = _(u'Words')
        ordering = ['word',]
    
    word = models.CharField(_(u'Word'), max_length=20, 
                            unique=True, primary_key=True, 
                            help_text=_(u'a word fitting a crossword puzzle; will become uppercased; no numbers, hyphens etc.'))

    def __unicode__(self):
        return self.word

    def length(self):
        return len(self.word)
    
    def save(self, force_insert=False, force_update=False):
        self.word = cleanword(self.word)
        super(Word, self).save(force_insert, force_update)



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
    language = models.CharField(_(u'Language'), max_length=15, 
                                default=settings.LANGUAGE_CODE, choices=settings.LANGUAGES, 
                                help_text=_(u'Language of (most of) the words in this dictionary'))
    description = models.CharField(_(u'Description'), max_length=255, blank=True)
    
    def __unicode__(self):
        return "%s (%s)" % (self.name, self.language)



class Description(models.Model):
    """
    A description or question for a word, according to a dictionary
    """
    class Meta:
        verbose_name = _(u'Description')
        verbose_name_plural = _(u'Descriptions')
        order_with_respect_to = 'word'
        ordering = ['priority','word']
        unique_together = (('word','dictionary'),)

    word = models.ForeignKey(Word, verbose_name=_(u'Word'))
    dictionary = models.ForeignKey(Dictionary, verbose_name=_(u'Dictionary'), related_name="%(class)s_related")
    description = models.CharField(_(u'Description'), max_length=127, help_text=_(u'Meaning of the word within the context of the selected dictionary'))
    priority = models.SmallIntegerField(_(u'Priority'), default=0, help_text=_(u'0 is neutral, you can increase or decrease the priority'))
    
    def __unicode__(self):
        return "%s\t%s" % (self.word, self.description)


class WordlistUpload(models.Model):
    """
    Wordlist importer
    """
    wordlist_file = models.FileField(_(u'wordlist file (.txt)'), upload_to=os.path.join(settings.MEDIA_ROOT, 'temp'),
                                help_text=_(u'Select a .txt file containing a single word per line to upload as a new dictionary.'))
    dictionary = models.ForeignKey(Dictionary, null=True, blank=True, help_text=_(u'Select a dictionary to add these words to. leave this empty to create a new dictionary from the supplied name.'))
    name = models.CharField(_(u'Name'), max_length=31, help_text=_(u'A short descriptive name'))
    language = models.CharField(_(u'Language'), max_length=15, 
                                default=settings.LANGUAGE_CODE, choices=settings.LANGUAGES, 
                                help_text=_(u'Language of (most of) the words in this dictionary'))
    description = models.CharField(_(u'Description'), max_length=255)

    class Meta:
        verbose_name = _(u'wordlist upload')
        verbose_name_plural = _(u'wordlist uploads')

    def save(self, *args, **kwargs):
        super(WordlistUpload, self).save(*args, **kwargs)
        dictionary = self.process_wordlist()
        super(WordlistUpload, self).delete()
        return dictionary

    def process_wordlist(self):
        if os.path.isfile(self.wordlist_file.path):
            words = []
            wordfile = file(self.wordlist_file.path, 'rU')
            words += wordfile.readlines()
            wordfile.close()
            
            if self.dictionary:
                DC = self.dictionary
            else:
                DC = Dictionary.objects.create(
                    name = self.name,
                    language = self.language,
                    description = self.description
                )
            DC.save()
            
            for w in words:
                (newword, newdesc, newprio) = splitwordline(w)
                if len(newword)<3: next
                try:
                    W = Word.objects.get(word=newword)
                except Word.DoesNotExist:
                    W = Word.objects.create(word=newword)
                    W.save()
                    
                try:
                    DE = Description.objects.get(word=W, dictionary=DC)
                    if newdesc: DE.description = newdesc
                    if newprio: DE.priority = newprio
                except Description.DoesNotExist:
                    DE = Description.objects.create(
                        word = W,
                        dictionary = DC,
                        description = newdesc,
                        priority = newprio,
                    )
                DE.save()
            
            return DC