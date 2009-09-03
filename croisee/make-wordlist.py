#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Crossword tool - wordlist

Make a wordlist from a text (in utf-8 encoding)
"""
import os, sys, str
import re
import sets

def clean_text(text):
    text = re.sub(r'\\\w+', ' ', text) # TeX commands
    text = re.sub(r'<[^>]+>', '', text) # XML tags
    text = re.sub(r'[^\w\s]', ' ', text) # non-chars
    text = re.sub(r'[\s\n\d_]+', ' ', text) # unify spaces and numbers
    text = re.sub(r'(^|\s)\w{1,2}\s', ' ', text) # single and double letters
    text = re.sub(r'\s+', ' ', text) # unify spaces
    return text

def text_to_set(text):
    """
    take a text and return a set of all contained words
    """
    s = sets.Set(text.split(' '))
    s.discard('')
    return s

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
        sourcetext = u''.join(sourcefile.readlines()).decode('utf-8')
        sourcefile.close()
        text += sourcetext

    text = clean_text(text)
    text = u'\n'.join(sorted(text_to_set(text), key=str.lower))
    targetfile.write(text)
    targetfile.close()
    