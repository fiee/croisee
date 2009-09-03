from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from models import *
import os

admin.autodiscover()

urlpatterns = patterns('',
        (r'^/?$', '%s.views.index' % settings.PROJECT_NAME),
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
        }),
        (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    )


urlpatterns += patterns('',
    (r'^admin/', include(admin.site.urls)),    
    (r'^$|^(.*?)/$', '%s.views.index' % settings.PROJECT_NAME),
)
