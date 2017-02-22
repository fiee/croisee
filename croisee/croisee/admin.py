# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import absolute_import
from django.contrib import admin
from croisee import models


class WordInline(admin.TabularInline):
    model = models.Word


class DictionaryAdmin(admin.ModelAdmin):
    list_display = ('name','language','description','public','owner')
    list_display_links = ['name',]
    list_filter = ('owner','language',)
    list_editable = ('language','description','public')
    search_fields = ('description','name')
    #inlines = (WordInline,) # too much
    ordering = ('name','language')
    exclude = ('owner',)

    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        obj.save()


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


class PuzzleAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'language', 'owner', 'public', 'width', 'height')
    list_display_links = ('code',)
    list_filter = ('public', 'owner', 'language', )
    list_editable = ('title', 'public', 'language',)
    search_fields = ('title', 'text', 'questions')
    
    def save_model(self, request, obj, form, change):
        obj.owner = request.user
        obj.save()


admin.site.register(models.Word, WordAdmin)
admin.site.register(models.Dictionary, DictionaryAdmin)
admin.site.register(models.WordlistUpload, WordlistUploadAdmin)
admin.site.register(models.Puzzle, PuzzleAdmin)
