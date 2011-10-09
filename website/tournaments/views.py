import logging
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from tournaments.models import *

class Struct:
  def __init__(self, **entries): 
    self.__dict__.update(entries)

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
  return render(request, 'tournaments/game.html', {'game': game})


def rankings(request):
  from django.db import connection, transaction
  cursor = connection.cursor()

  # Data retrieval operation - no commit required
  cursor.execute("""
      SELECT 
        * 
        , ROUND(CAST(number_of_moves AS FLOAT) / MAX((wins + losses + draws), 1), 1) AS average_number_of_moves 
        , ROUND(time / MAX(number_of_moves, 1), 1) AS average_time_per_move 
        , ROUND(CAST(wins AS FLOAT) / MAX((wins + losses + draws), 1), 3) AS winning_percentage 
      FROM ( 
        SELECT 
          bot_id 
          , name 
          , SUM(wins) AS wins 
          , SUM(losses) AS losses 
          , SUM(draws) AS draws 
          , SUM(errors) AS errors 
          , SUM(number_of_moves) AS number_of_moves 
          , SUM(time) AS time 
        FROM 
          tournaments_bot b 
          LEFT OUTER JOIN tournaments_participant p 
            ON b.id = p.bot_id 
          LEFT OUTER JOIN tournaments_tournament t 
            ON p.tournament_id = t.id 
        WHERE 
          t.is_deleted = 0 GROUP BY bot_id)
      ORDER BY
        winning_percentage DESC, wins DESC, draws DESC, errors ASC, name ASC""")
  results = dictfetchall(cursor)
  rankings = [Struct(**result) for result in results]

  logging.debug(rankings)

  return render(request, 'tournaments/rankings.html', {'rankings': rankings })

def dictfetchall(cursor):
  "Returns all rows from a cursor as a dict"
  desc = cursor.description
  return [
    dict(zip([col[0] for col in desc], row))
    for row in cursor.fetchall()
  ]

