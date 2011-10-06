from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView
from tournaments.models import Tournament, Game

urlpatterns = patterns('',
  (r'^$', 
    ListView.as_view(
      queryset=Tournament.objects.order_by('-date_played'),
      context_object_name='tournaments',
      template_name='tournaments/index.html')),
  (r'^(?P<id>\d+)/$', 'tournaments.views.tournament'),
  (r'^game/(?P<id>\d+)/$', 'tournaments.views.game'),
)

