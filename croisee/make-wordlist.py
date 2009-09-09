#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Crossword tool - wordlist

Make a wordlist from a text (in utf-8 encoding)
"""
import os, sys, locale
import re
import sets
locale.setlocale(locale.LC_ALL, 'de_DE.utf-8') # affects re's \w

reTEX = re.compile(r'\\\w+', re.LOCALE)
reNONCHARS = re.compile(r'[^\w\s]', re.LOCALE)
reSINGLECHAR = re.compile(r'^\w?\n', re.LOCALE|re.MULTILINE)

def clean_text(text):
    text = reTEX.sub(' ', text)
    text = re.sub(r'<[^>]+>', '', text) # XML tags
    text = re.sub(r'[\'’´`‘]s', '', text) # genitives
    text = reNONCHARS.sub('', text)
    text = reSINGLECHAR.sub('', text)
    text = re.sub(r'[\s\n\d_]+', ' ', text) # unify spaces and numbers
    #text = re.sub(r'(^|\s)\w{1,2}\s', ' ', text) # single and double letters
    text = re.sub(r'\s+', ' ', text) # unify spaces
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
    
    targetfile = file('wordlist.txt', 'a+')
    text = ''
    while len(args)>0:
        path = os.path.abspath(args.pop())
        print u"reading %s" % path
        sourcefile = file(path, 'rU')
        sourcetext = unicode(''.join(sourcefile.readlines()), 'utf-8')
        sourcefile.close()
        text += sourcetext

    text = clean_text(text)
    text = u'\n'.join(sorted(text_to_set(text), key=lowercase))
    targetfile.write(text.encode('utf-8'))
    targetfile.close()
    