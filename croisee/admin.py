# -*- coding: utf-8 -*-
from django.contrib import admin
from models import *


class WordInline(admin.TabularInline):
    model = Word

class DictionaryAdmin(admin.ModelAdmin):
    list_display = ('name','language','description')
    list_display_links = ['name',]
    list_filter = ('language',)
    list_editable = ('language','description',)
    search_fields = ('description',)
    #inlines = (WordInline,) # too much
    ordering = ('name','language')

class WordAdmin(admin.ModelAdmin):
    list_display = ('word','description','dictionary','priority')
    list_display_links = ['word',]
    list_filter = ('dictionary',)
    list_editable = ('description','priority')
    search_fields = ('word','description')
    ordering = ('word',)

class WordlistUploadAdmin(admin.ModelAdmin):
    def has_change_permission(self, request, obj=None):
        return False # To remove the 'Save and continue editing' button

admin.site.register(Word, WordAdmin)
admin.site.register(Dictionary, DictionaryAdmin)
admin.site.register(WordlistUpload, WordlistUploadAdmin)
