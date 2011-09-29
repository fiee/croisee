from django.forms import ModelForm
from croisee.models import *

class PuzzleForm(ModelForm):
    class Meta(object):
        model = Puzzle

class DictionaryForm(ModelForm):
    class Meta(object):
        model = Dictionary

class WordForm(ModelForm):
    class Meta(object):
        model = Word
