from __future__ import unicode_literals
from __future__ import absolute_import
import os
import django
from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
try:
    from rest_framework.views import ListOrCreateModelView, InstanceModelView
    from croisee.resources import PuzzleResource, DictionaryResource
    REST_API = True
except ImportError:
    REST_API = False
# from croisee import models
from croisee import views

admin.autodiscover()

js_info_dict = {
    'packages': (settings.PROJECT_NAME,),
}

urlpatterns = [
    url(r'^/?$', views.IndexView.as_view(), name='%s-index' % settings.PROJECT_NAME),
    url(r'^i18n/', include('django.conf.urls.i18n',)),
    url(r'^jsi18n/$', django.views.i18n.javascript_catalog, js_info_dict, name='javascript-catalog'),
]

# serve static content in debug mode
if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', django.views.static.serve, {
            'document_root': settings.MEDIA_ROOT,
            'show_indexes' : True
        }),
        url(r'^(?P<path>favicon.*)$', django.views.static.serve, {
            'document_root': settings.MEDIA_ROOT,
            'content_type': 'application/x-favicon',
        }),
        url(r'^admin/doc/', include('django.contrib.admindocs.urls',)),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


urlpatterns += [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('django_registration.backends.activation.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^ajax/(?P<cloze>[A-Z\*\?_%]+)/$', 
        views.AjaxClozeQueryView.as_view(),
        name='%s-ajax_clozequery' % settings.PROJECT_NAME),
    url(r'^ajax/(?P<horizontal>[A-Z\*\?_%]+)(,(?P<hletter>\d+))?/(?P<vertical>[A-Z\*\?_%]+)(,(?P<vletter>\d+))?/$',
        views.AjaxCrossQueryView.as_view(),
        name='%s-ajax_crossquery' % settings.PROJECT_NAME),

    url(r'^puzzle/$', views.NewPuzzleView.as_view(), name='%s-puzzle-new' % settings.PROJECT_NAME),
    url(r'^puzzle/save/$', views.PuzzleView.as_view(), name='%s-puzzle-save' % settings.PROJECT_NAME),
    url(r'^puzzle/list/$',
        views.PuzzleListView.as_view(),
        name='%s-puzzle-list' % settings.PROJECT_NAME),
    url(r'^puzzle/(?P<slug>[a-z\d]+)/$', views.PuzzleView.as_view(), name='%s-puzzle-get' % settings.PROJECT_NAME),
    url(r'^puzzle/(?P<slug>[a-z\d]+)/(?P<format>context|latex|txt)/$', views.PuzzleExportView.as_view(), name='%s-puzzle-export' % settings.PROJECT_NAME),
    # (?P<format>html|context|latex|pdf|txt|idml|json|yaml)
    url(r'^puzzle/(?P<slug>[a-z\d]+)/delete/$', views.DeletePuzzleView.as_view(), name='%s-puzzle-delete' % settings.PROJECT_NAME),
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
        views.WordListView.as_view(),
        name='%s-dictionary-personal' % settings.PROJECT_NAME),
    # show other dictionary
    url(r'^dictionary/(?P<object_id>\d+)/$',
        views.WordListView.as_view(),
        name='%s-dictionary' % settings.PROJECT_NAME),
]

handler500 = views.TemplateView.as_view(template_name='500.html')

if REST_API:
    urlpatterns += [
        url('^api/puzzle/$', ListOrCreateModelView.as_view(resource=PuzzleResource), name='api-%s-puzzle-root' % settings.PROJECT_NAME),
        url('^api/puzzle/(?P<object_id>[a-z\d]{24,})/$', InstanceModelView.as_view(resource=PuzzleResource)),
        url('^api/dictionary/(?P<object_id>\d+)/$', InstanceModelView.as_view(resource=DictionaryResource)),
    ]
