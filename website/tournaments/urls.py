from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView
from tournaments.models import Tournament, Game

urlpatterns = patterns('',
  (r'^$', 
    ListView.as_view(
      queryset=Tournament.objects.order_by('-date_played'),
      context_object_name='tournaments',
      template_name='tournaments/index.html')),
  (r'^(?P<pk>\d+)/$', 
    DetailView.as_view(
      model=Tournament,
      template_name='tournaments/tournament.html')),
  url(r'^game/(?P<pk>\d+)/$', 
    DetailView.as_view(
      model=Game,
      template_name='tournaments/game.html'),
    name='game_results'),
)

