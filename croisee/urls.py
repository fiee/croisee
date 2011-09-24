from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from models import *
from views import PuzzleView, IndexView, WordListView, AjaxClozeQueryView, AjaxCrossQueryView
import os

admin.autodiscover()

js_info_dict = {
    'packages': (settings.PROJECT_NAME,),
}

urlpatterns = patterns('',
    url(r'^/?$', IndexView.as_view(), name='%s-index' % settings.PROJECT_NAME),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
)

# serve static content in debug mode
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            'show_indexes' : True
        }),
        (r'^(?P<path>favicon.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            'mimetype': 'application/x-favicon',
        }),
        (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    )

urlpatterns += patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^ajax/(?P<cloze>[A-Z\*\?_%]+)/$', 
        AjaxClozeQueryView.as_view(), 
        name='%s-ajax_clozequery' % settings.PROJECT_NAME),  
    url(r'^ajax/(?P<horizontal>[A-Z\*\?_%]+)(,(?P<hletter>\d+))?/(?P<vertical>[A-Z\*\?_%]+)(,(?P<vletter>\d+))?/$', 
        AjaxCrossQueryView.as_view(), 
        name='%s-ajax_crossquery' % settings.PROJECT_NAME),
    # get puzzle by hash code  
    url(r'^puzzle/(?P<hash>)[a-z\d]{24,}/(?P<action>(get|save|delete)/)?$', 
        PuzzleView.as_view(), 
        name='%s-puzzle' % settings.PROJECT_NAME),
    # show personal dictionary  
    url(r'^dictionary/$', 
        WordListView.as_view(), 
        name='%s-dictionary-personal' % settings.PROJECT_NAME),
    # show other dictionary  
    url(r'^dictionary/(?P<object_id>\d+)/$', 
        WordListView.as_view(), 
        name='%s-dictionary' % settings.PROJECT_NAME),
    url(r'^grid/save/$', '%s.views.save' % settings.PROJECT_NAME, name='%s-save' % settings.PROJECT_NAME),
    url(r'^grid/$', '%s.views.grid' % settings.PROJECT_NAME, name='%s-grid' % settings.PROJECT_NAME),
    #url(r'^$|^(.*?)/$', '%s.views.index' % settings.PROJECT_NAME, name='%s-index' % settings.PROJECT_NAME),
)

handler500 = '%s.views.server_error' % settings.PROJECT_NAME
