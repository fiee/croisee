from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.sitemaps import GenericSitemap
from feincms.module.page.models import Page
from schedule.models import Event
import os

admin.autodiscover()

mysitemaps = {
    'page' : GenericSitemap({
        'queryset':Page.objects.all(),
        'changefreq':'monthly',
        'date_field':'modification_date',
    }, priority=0.6),
    'event' : GenericSitemap({
        'queryset':Event.objects.all(),
        'changefreq':'daily',
        'date_field':'created_on',
    }, priority=0.5),
}

urlpatterns = patterns('')

# serve static content in debug mode
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
            'show_indexes' : True
        }),
        (r'^medialibrary/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': ('%s/medialibrary/') % settings.MEDIA_ROOT,
            'show_indexes' : True
        }),
        (r'^feincms_admin_media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT+'/feincms_admin_media',
            'show_indexes' : True
        }),
        (r'^(?P<path>favicon.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
    )


urlpatterns += patterns('',
    (r'^/?$', '%s.views.home' % settings.PROJECT_NAME),
    (r'^calendar/', include('schedule.urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),    
    (r'sitemap.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': mysitemaps}),
    (r'^$|^(.*)/$', 'feincms.views.base.handler'),
)
