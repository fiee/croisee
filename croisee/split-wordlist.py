#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Crossword tool - wordlist

Split a wordlist that's too big for an upload

Usage: split-wordlist.py <sourcefile.txt> [<number of lines>]

Defaults to 10,000 lines, writes to sourcefile_#.txt
"""
import os, sys

if __name__ == '__main__':

    if len(sys.argv) > 1:
        path = os.path.abspath(sys.argv[1])
        if not os.path.isfile(path):
            print "%s is not a file!" % path
            sys.exit(2)
        if (len(sys.argv) > 2):
            maxlines = int(sys.argv[2])
        else:
            maxlines = 10000
    else:
        print __doc__
        sys.exit(1)
    
    sourcefile = file(path, 'rU')
    linecount = 0
    targetnumber = 1
    head, tail = os.path.splitext(path)
    for line in sourcefile.readlines():
        if linecount % maxlines == 0:
            if linecount>0:
                targetfile.close()
            targetname = "%s_%03d%s" % (head, targetnumber, tail)
            print "new file: %s (%d lines written)" % (os.path.basename(targetname), linecount)
            targetfile = file(targetname, 'w')
            targetnumber += 1
        targetfile.write(line)
        linecount += 1
    print "split completed, %d lines written." % linecount
        
    sourcefile.close()
    targetfile.close()    

