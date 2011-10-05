from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
  (r'^tournaments/', include('tournaments.urls')),
  url(r'^admin/', include(admin.site.urls))
)

if settings.DEBUG:
  urlpatterns += staticfiles_urlpatterns()
