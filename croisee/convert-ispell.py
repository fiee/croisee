#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Crossword tool - wordlist

Make a wordlist from an ispell dict

Those dicts are wordlists with additional metadata behind a slash.
The text encoding is similar to old TeX conventions.
But some files contain accented vocals in Latin-1 encoding.
"""
import os, sys, locale
import re
import sets
locale.setlocale(locale.LC_ALL, 'de_DE.utf-8') # affects re's \w

replacements = (
    ('a"', u'ä'),
    ('o"', u'ö'),
    ('u"', u'ü'),
    ('A"', u'Ä'),
    ('O"', u'Ö'),
    ('U"', u'Ü'),
    ('sS', u'ß'),
    ('qq', ''), # hyphenation?
    #('\n\n', '\n')
)

reSUFFIX = re.compile(r'/[A-Z#]+$',re.I|re.M)
reNONCHARS = re.compile(r'[^\w\s]', re.LOCALE)
reSINGLECHAR = re.compile(r'^\w?\n', re.LOCALE|re.MULTILINE)

def clean_text(text):
    for k,v in replacements:
        text = text.replace(k,v)
    text = reSUFFIX.sub('', text) # word type identifiers
    text = reNONCHARS.sub('', text)
    text = reSINGLECHAR.sub('', text)
    return text

def text_to_set(text):
    """
    take a text and return a set of all contained words
    """
    s = sets.Set(text.split(' '))
    s.discard('')
    return s

def lowercase(text):
    return text.lower()

if __name__ == '__main__':

    if len(sys.argv) > 1:
        args = sys.argv[1:]
    else:
        sys.exit(1)
    
    targetfile = file('wordlist.txt', 'w+')
    text = ''
    while len(args)>0:
        path = os.path.abspath(args.pop())
        print u"reading %s" % path
        sourcefile = file(path, 'rU')
        sourcetext = u''
        #for line in sourcefile.readlines():
        #    sourcetext += unicode(line, 'latin-1')
        sourcetext = unicode(''.join(sourcefile.readlines()), 'latin-1')
        sourcefile.close()
        text += sourcetext

    text = clean_text(text)
    text = u'\n'.join(sorted(text_to_set(text), key=lowercase))
    targetfile.write(text.encode('utf-8'))
    targetfile.close()
    