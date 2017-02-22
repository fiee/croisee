from __future__ import unicode_literals
from __future__ import absolute_import
from django.forms import ModelForm
from croisee import models


class PuzzleForm(ModelForm):
    class Meta(object):
        model = models.Puzzle
        fields = "__all__"


class DictionaryForm(ModelForm):
    class Meta(object):
        model = models.Dictionary
        fields = "__all__"


class WordForm(ModelForm):
    class Meta(object):
        model = models.Word
        fields = "__all__"
