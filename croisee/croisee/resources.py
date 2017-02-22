from __future__ import unicode_literals
from __future__ import absolute_import
from rest_framework.resources import ModelResource
from croisee.models import Puzzle, Dictionary


class PuzzleResource(ModelResource):
    allowed_methods = ('GET', 'PUT', 'DELETE')
    fields = ('code', 'title', 'owner', 'language', 'text', 'questions', 'numbers', 'width', 'height')
    #exclude = ('createdby', 'createdon', 'lastchangedby', 'lastchangedon')
    ordering = ('-lastchangedon',)
    model = Puzzle
    

class DictionaryResource(ModelResource):
    model = Dictionary
    