# -*- coding: utf-8 -*-
from django.contrib import admin
from models import *


class WordInline(admin.TabularInline):
    model = Word

class DictionaryAdmin(admin.ModelAdmin):
    list_display = ('name','language','description','public','owner')
    list_display_links = ['name',]
    list_filter = ('owner','language',)
    list_editable = ('language','description','public')
    search_fields = ('description','name')
    #inlines = (WordInline,) # too much
    ordering = ('name','language')
    exclude = ('owner',)

class WordAdmin(admin.ModelAdmin):
    list_display = ('word','description','dictionary','priority')
    list_display_links = ['word',]
    list_filter = ('dictionary',)
    list_editable = ('description','priority')
    search_fields = ('word','description')
    ordering = ('word',)

class WordlistUploadAdmin(admin.ModelAdmin):
    exclude = ('owner',)
    def has_change_permission(self, request, obj=None):
        return False # To remove the 'Save and continue editing' button
    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        obj.save()

admin.site.register(Word, WordAdmin)
admin.site.register(Dictionary, DictionaryAdmin)
admin.site.register(WordlistUpload, WordlistUploadAdmin)
