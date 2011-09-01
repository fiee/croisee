from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from models import *
import os

admin.autodiscover()

urlpatterns = patterns('',
        url(r'^/?$', '%s.views.index' % settings.PROJECT_NAME, name='%s-index' % settings.PROJECT_NAME),
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
    url(r'^ajax/(?P<cloze>[A-Z\*\?_%]+)/$', '%s.views.ajax_clozequery' % settings.PROJECT_NAME, name="%s-ajax_clozequery" % settings.PROJECT_NAME),  
    url(r'^ajax/(?P<horizontal>[A-Z\*\?_%]+)(,(?P<hletter>\d+))?/(?P<vertical>[A-Z\*\?_%]+)(,(?P<vletter>\d+))?/$', '%s.views.ajax_crossquery' % settings.PROJECT_NAME, name="%s-ajax_crossquery" % settings.PROJECT_NAME),  
    url(r'^grid/save/$', '%s.views.save' % settings.PROJECT_NAME, name='%s-save' % settings.PROJECT_NAME),
    url(r'^grid/$', '%s.views.grid' % settings.PROJECT_NAME, name='%s-grid' % settings.PROJECT_NAME),
    #url(r'^$|^(.*?)/$', '%s.views.index' % settings.PROJECT_NAME, name='%s-index' % settings.PROJECT_NAME),
)

handler500 = '%s.views.server_error' % settings.PROJECT_NAME
