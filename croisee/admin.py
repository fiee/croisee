# -*- coding: utf-8 -*-
from django.contrib import admin
from models import *

class WordAdmin(admin.ModelAdmin):
    search_fields = ('word')
    #list_display = ('word')
    #list_display_links = ['word',]
    #list_filter = ('art',)
    

admin.site.register(Word, WordAdmin)
