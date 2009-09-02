#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unicodedata
import re
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.template.loader import render_to_string
from django.conf import settings

class Word(models.Model):
    """
    A word
    """
    REPLACEMENTS = (
    # international characters that need more than just stripping accents
        (u'Ä', 'AE'),
        (u'Ö', 'OE'),
        (u'Ü', 'UE'),
        (u'ß', 'SS'),
    )
    reASCIIonly = re.compile(r'[^A-Z]+', re.I)

    class Meta:
        verbose_name = _(u'Word')
        verbose_name_plural = _(u'Words')
    
    word = models.CharField(_(u'Word'), max_length=20, 
                            unique=True, primary_key=True, 
                            help_text=_(u'a word fitting a crossword puzzle; will become uppercased; no numbers, hyphens etc.'))

    def __unicode__(self):
        return self.word

    def length(self):
        return len(self.word)
    
    def cleanword(self, word=None):
        if word==None: word = self.word
        word = word.upper()
        for k,v in self.REPLACEMENTS:
            word = word.replace(k,v)
        word = unicodedata.normalize('NFD', word).encode('ASCII', 'ignore') # decompose international chars
        word = self.reASCIIonly.sub(word)
        return word
            
    
    def save(self, force_insert=False, force_update=False):
        self.word = self.cleanword()
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
        verbose_name = _(u'Dictionary')
        verbose_name_plural = _(u'Dictionaries')
        order_with_respect_to = 'word'
        ordering = ['priority','word']
        unique_together = (('word','dictionary'),)

    word = models.ForeignKey(Word, verbose_name=_(u'Word'))
    dictionary = models.ForeignKey(Dictionary, verbose_name=_(u'Dictionary'))
    description = models.CharField(_(u'Description'), max_length=31, help_text=_(u'Meaning of the word within the context of the selected dictionary'))
    priority = models.SmallIntegerField(_(u'Priority'), default=0, help_text=_(u'0 is neutral, you can increase or decrease the priority'))
    
    def __unicode__(self):
        return "%s\t%s" % (self.word, self.description)
