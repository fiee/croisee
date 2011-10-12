from django import template
from django.template.defaultfilters import stringfilter
import re

register = template.Library()

reTeXSpecials = re.compile(r'([&%|{}\[\]])', re.I|re.M)

@stringfilter
def texquote(input):
    """Quote TeX characters"""
    return reTeXSpecials.sub(r'\\\1{}', input)

register.filter('texquote', texquote)

@stringfilter
def texlines(input):
    """convert \\n to \\crlf"""
    return input.replace('\n', '\\crlf\n')

register.filter('texlines', texlines)

@stringfilter
def texlogo(input, word):
    """Replace word with a logo version"""
    return input.replace(word, u'\\Logo{%s}' % (word)) # no filters with 2 arguments?

register.filter('texlogo', texlogo)

@stringfilter
def braced(input):
    """Put braces around a word"""
    return '{%s}' % input

register.filter('braced', braced)
