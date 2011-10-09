from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.simple import direct_to_template, redirect_to


from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
  ('^about/$', direct_to_template, {'template': 'about.html'}),
  ('^participate/$', direct_to_template, {'template': 'participate.html'}),
  ('^$', redirect_to, {'url': 'tournaments'}),
  (r'^tournaments/', include('tournaments.urls')),
  url(r'^admin/', include(admin.site.urls)),
)


if settings.DEBUG:
  urlpatterns += patterns('django.views.static',
    ( r'^%s(?P<path>.*)' % settings.MEDIA_URL[1:], 'serve', {'document_root': settings.MEDIA_ROOT} ),
  )
  urlpatterns += staticfiles_urlpatterns()
