#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crossword tool - wordlist

Make a wordlist from a text (in utf-8 encoding)
"""
import os, sys, locale
import re
locale.setlocale(locale.LC_ALL, 'de_DE.utf-8') # affects re's \w

reTEX = re.compile(r'\\\w+')
reNONCHARS = re.compile(r'[^\w\s]')
reSINGLECHAR = re.compile(r'^\w?\n', flags=re.MULTILINE)

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
    s = set(text.split(' '))
    s.discard('')
    n = set()
    for w in s:
        # remove case variants
        if not w.lower() in n:
            n.add(w)
    return n

def lowercase(text):
    return text.lower()

if __name__ == '__main__':

    if len(sys.argv) > 1:
        args = sys.argv[1:]
    else:
        sys.exit(1)

    targetfile = open('wordlist.txt', 'a+', encoding='utf-8')
    text = ''
    while len(args)>0:
        path = os.path.abspath(args.pop())
        print("reading %s" % path)
        sourcefile = open(path, 'r', encoding='utf-8')
        sourcetext = ''.join(sourcefile.readlines())
        sourcefile.close()
        text += sourcetext

    text = clean_text(text)
    text = '\n'.join(sorted(text_to_set(text), key=lowercase))
    targetfile.write(text)
    targetfile.close()
