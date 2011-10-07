import os
from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
try:
    from djangorestframework.views import ListOrCreateModelView, InstanceModelView
    from croisee.resources import PuzzleResource, DictionaryResource
    REST_API = True
except ImportError:
    REST_API = False
from croisee.models import *
from croisee.views import *

admin.autodiscover()

js_info_dict = {
    'packages': (settings.PROJECT_NAME,),
}

urlpatterns = patterns('',
    url(r'^/?$', IndexView.as_view(), name='%s-index' % settings.PROJECT_NAME),
    url(r'^i18n/', include('django.conf.urls.i18n')),
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
    
    url('^puzzle/$', NewPuzzleView.as_view(), name='%s-puzzle-new' % settings.PROJECT_NAME),
    url('^puzzle/save/$', PuzzleView.as_view(), name='%s-puzzle-save' % settings.PROJECT_NAME),
    url('^puzzle/(?P<slug>[a-z\d]+)/$', PuzzleView.as_view(), name='%s-puzzle-get' % settings.PROJECT_NAME),
    url('^puzzle/(?P<slug>[a-z\d]+)/delete/$', DeletePuzzleView.as_view(), name='%s-puzzle-delete' % settings.PROJECT_NAME),
#    # new puzzle
#    url(r'^puzzle/$', 
#        NewPuzzleView.as_view(), 
#        name='%s-puzzle-new' % settings.PROJECT_NAME),
#    # save new puzzle
#    url(r'^puzzle/save/$', 
#        SavePuzzleView.as_view(), 
#        name='%s-puzzle-save' % settings.PROJECT_NAME),
#    # get puzzle by hash code  
#    url(r'^puzzle/(?P<slug>)[a-z\d]{24,}/(?P<action>(get|save|delete)/)?$', 
#        PuzzleView.as_view(), 
#        name='%s-puzzle' % settings.PROJECT_NAME),
    # show personal dictionary  
    url(r'^dictionary/$', 
        WordListView.as_view(), 
        name='%s-dictionary-personal' % settings.PROJECT_NAME),
    # show other dictionary  
    url(r'^dictionary/(?P<object_id>\d+)/$', 
        WordListView.as_view(), 
        name='%s-dictionary' % settings.PROJECT_NAME),
)

handler500 = TemplateView.as_view(template_name='500.html')

if REST_API:
    urlpatterns += patterns('',
        url('^api/puzzle/$', ListOrCreateModelView.as_view(resource=PuzzleResource), name='api-%s-puzzle-root' % settings.PROJECT_NAME),
        url('^api/puzzle/(?P<object_id>[a-z\d]{24,})/$', InstanceModelView.as_view(resource=PuzzleResource)),
        url('^api/dictionary/(?P<object_id>\d+)/$', InstanceModelView.as_view(resource=DictionaryResource)),
    )
