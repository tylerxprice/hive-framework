import argparse
import json
import logging
import os
import shlex
import sys
from time import time
from datetime import datetime
from django.conf import settings
settings.configure(DEBUG=True, DATABASES = {
  'default': {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': os.path.join(os.path.join(os.path.dirname(__file__), 'website'), 'tournaments.sqlite3'),
    'USER': '',
    'PASSWORD': '',
    'HOST': '',
    'PORT': '',
  }},
  MEDIA_ROOT=os.path.join(os.path.dirname(__file__), 'website/media')
)
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from website.tournaments.models import Bot, Tournament, Participant, Game
from framework import Framework


logging.basicConfig(level=logging.DEBUG)


class Scheduler(object):
  def __init__(self, args):
    self.args = self.parse_args(args) 

  def parse_args(self, args):
    parser = argparse.ArgumentParser(prog='scheduler', argument_default='')
    parser.add_argument(args[0], default='') 
    args = parser.parse_args(args)
    args = vars(args)
    return args

  def run(self):

    try:
      tournament = Tournament()
      tournament.status = Tournament.STATUS_CHOICES[0][0]
      tournament.save()

      logging.debug('Scheduler.run: tournament = ' + str(tournament))

      bots = Bot.objects.filter(is_deleted=0)
      start_time = time()
      for white in bots:

        try:
          white_participant = Participant.objects.get(tournament__id=tournament.id, bot__id=white.id)
        except ObjectDoesNotExist:
          white_participant = Participant(tournament=tournament, bot=white)

        logging.debug('Scheduler.run: white = ' + str(white))

        for black in bots:
          if not white == black:
            logging.debug(white.name + ' v. ' + black.name)

            try:
              black_participant = Participant.objects.get(tournament__id=tournament.id, bot__id=black.id)
            except ObjectDoesNotExist:
              black_participant = Participant(tournament=tournament, bot=black)

            logging.debug('Scheduler.run: black = ' + str(black))

            game = Game(tournament=tournament, white=white, black=black)

            logging.debug('Scheduler.run: game = ' + str(game))

            commandLine = 'framework --white="' + white.name + '" --black="' + black.name + '" --times="600000,0,0" --moves=", " --expansions=""'
            commandLine = commandLine.encode('ascii')
            framework = Framework(shlex.split(commandLine))
            results = framework.norun() 

            logging.debug('Scheduler.run: results = ' + str(results))

            white_participant.wins += results['white']['wins']
            white_participant.losses += results['white']['loses']
            white_participant.draws += results['white']['draws']
            white_participant.number_of_moves += results['white']['number_of_moves']
            white_participant.time += results['white']['time']
            white_participant.errors += results['white']['errors']
            white_participant.save()

            black_participant.wins += results['black']['wins']
            black_participant.losses += results['black']['loses']
            black_participant.draws += results['black']['draws']
            black_participant.number_of_moves += results['black']['number_of_moves']
            black_participant.time += results['black']['time']
            black_participant.errors += results['black']['errors']
            black_participant.save()

            game.duration = results['white']['time'] + results['black']['time']
            game.duration = results['white']['time'] + results['black']['time']
            game.number_of_moves = results['white']['number_of_moves'] + results['black']['number_of_moves']

            if results['white']['wins'] == 1:
              game.winner = game.WINNER_CHOICES[0][0]
            elif results['black']['wins'] == 1: 
              game.winner = game.WINNER_CHOICES[1][0]
            else: 
              game.winner = game.WINNER_CHOICES[2][0]

            result_json = json.dumps({ 
              'white': white.name,
              'black': black.name,
              'times': results['args']['times'],
              'moves': results['args']['moves'],
              'expansions': results['args']['expansions'],
              'date_played': datetime.utcnow().isoformat(),
              'duration': game.duration,
              'winner': game.winner,
              'play_by_play': results['play_by_play']
              }, indent=2)

            game.result_file.save('result.json', ContentFile(result_json))

            game.save()

      end_time = time()

      tournament.duration = round((end_time - start_time) * 100)
      tournament.status = Tournament.STATUS_CHOICES[2][0]
      tournament.save()
    except:
      print "Unexpected error:", sys.exc_info()


if __name__ == "__main__": 
  Scheduler(sys.argv).run()

