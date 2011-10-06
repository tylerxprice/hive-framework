from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from tournaments.models import *

def tournament(request, id):
  tournament = get_object_or_404(Tournament, pk=id)
  participants = tournament.get_participants();
  bots = map(lambda p: p.bot, participants)
  number_of_bots = len(bots)

  matrix = [None for j in range(number_of_bots)]
  for game in tournament.game_set.all():
    y = bots.index(game.white)
    x = bots.index(game.black)
    if not matrix[y]:
      matrix[y] = dict()
      matrix[y]['bot_name'] = game.white.name # need this for the row header
      matrix[y]['games'] = [None for i in range(len(bots))] # the None will stay in for the square against itself
    matrix[y]['games'][x] = game

  return render(request, 'tournaments/tournament.html', {
    'tournament': tournament, 
    'result_matrix': matrix, 
    'number_of_bots': number_of_bots, 
    'participants': participants,
    })


def game(request, id):
  game = get_object_or_404(Game, pk=id)
  return rnder(request, 'tournaments/game.html', {'game': game})
