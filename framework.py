import argparse
import logging
import math
import os
import shlex
import subprocess
import sys
from time import time
from errors import *
from game import *

#logging.basicConfig(level=logging.DEBUG)

class Framework():
  def __init__(self, args):
    self.args = self._parseArgs(args)

  def _parseArgs(self, args):
    parser = argparse.ArgumentParser(prog='framework', argument_default='')
    parser.add_argument(args[0], default='') 
    parser.add_argument('--white') 
    parser.add_argument('--black')
    parser.add_argument('--times', default='30000,0,0') # game time, white used, black used (ms)
    parser.add_argument('--moves', default='') # 1. wS1, 2. bG1 -wS1, 3. wQ wS1/, ...
    parser.add_argument('--expansions', default='') # LM
    args = parser.parse_args(args)
    args = vars(args)
    logging.debug('Framework._parseArgs: args = ' + str(args))
    return args

  def run(self):
    self.args['white'] = self.readBot('white', self.args['white'])
    self.args['black'] = self.readBot('black', self.args['black'])
    self.game = Game(self.args['white'], self.args['black'], self.args['times'], self.args['moves'], self.args['expansions'])
    self.game.hive.printBoard()

    results = {}
    results['play_by_play'] = [] 

    error = ''
    while not self.game.isGameOver():
      moveString, moveTime, errorOutput = self.readMove()
      if moveString == 'quit' or moveString == 'exit':
        break
      try:
        sys.stdout.write(self.game.currentPlayer.color.capitalize() + ' plays ' + moveString + '\n')
        self.game.playMove(moveString)
      except InputError as e:
        sys.stderr.write(e.value + '\n')
        if self.game.currentPlayer.bot: 
          error = self.game.currentPlayer.color
          break;
      except MoveError as e:
        sys.stderr.write(e.value + '\n')
        if self.game.currentPlayer.bot: 
          error = self.game.currentPlayer.color
          break;
      else:
        self.game.printBoard()

      results['play_by_play'].append({
        'move_number': self.game.turnNumber - 1,
        'move_string': moveString,
        'move_time': moveTime,
        'error_output': errorOutput,
      })

    if error:
      winner = Game.WINNER_WHITE if error == Player.BLACK else Game.WINNER_BLACK
    else:
      winner = self.game.getWinner()

    if winner == Game.WINNER_WHITE:
      sys.stdout.write('White wins!\n')
    elif winner == Game.WINNER_BLACK:
      sys.stdout.write('Black wins!\n')
    elif winner == Game.WINNER_DRAW:
      sys.stdout.write('It\'s a draw!\n')

    results['args'] = {} 
    results['args']['times'] = self.game.getTimeControlsCsv() 
    results['args']['moves'] = self.game.getMoveListCsv() 
    results['args']['expansions'] = self.args['expansions'] 
    results['white'] = {} 
    results['white']['wins'] = 1 if winner == Game.WINNER_WHITE else 0
    results['white']['loses'] = 1 if winner == Game.WINNER_BLACK else 0
    results['white']['draws'] = 1 if winner == Game.WINNER_DRAW else 0
    results['white']['errors'] = 1 if error == Player.WHITE else 0
    results['white']['number_of_moves'] = int(math.ceil(float(self.game.turnNumber - 1) / 2)) 
    results['white']['time'] = self.game.whitePlayer.timeUsed
    results['black'] = {} 
    results['black']['wins'] = 1 if winner == Game.WINNER_BLACK else 0
    results['black']['loses'] = 1 if winner == Game.WINNER_WHITE else 0
    results['black']['draws'] = 1 if winner == Game.WINNER_DRAW else 0
    results['black']['errors'] = 1 if error == Player.BLACK else 0
    results['black']['number_of_moves'] = int(math.floor(float(self.game.turnNumber - 1) / 2)) 
    results['black']['time'] = self.game.blackPlayer.timeUsed

    return results

  def norun(self):
    self.game = Game(self.args['white'], self.args['black'], self.args['times'], self.args['moves'], self.args['expansions'])
    results = {}
    results['play_by_play'] = [] 

    winner = Game.WINNER_DRAW
    error = 0

    results['args'] = {} 
    results['args']['times'] = self.game.getTimeControlsCsv() 
    results['args']['moves'] = self.game.getMoveListCsv() 
    results['args']['expansions'] = self.args['expansions'] 
    results['white'] = {} 
    results['white']['wins'] = 1 if winner == Game.WINNER_WHITE else 0
    results['white']['loses'] = 1 if winner == Game.WINNER_BLACK else 0
    results['white']['draws'] = 1 if winner == Game.WINNER_DRAW else 0
    results['white']['errors'] = 1 if error == Player.WHITE else 0
    results['white']['number_of_moves'] = int(math.ceil(float(self.game.turnNumber - 1) / 2)) 
    results['white']['time'] = self.game.whitePlayer.timeUsed
    results['black'] = {} 
    results['black']['wins'] = 1 if winner == Game.WINNER_BLACK else 0
    results['black']['loses'] = 1 if winner == Game.WINNER_WHITE else 0
    results['black']['draws'] = 1 if winner == Game.WINNER_DRAW else 0
    results['black']['errors'] = 1 if error == Player.BLACK else 0
    results['black']['number_of_moves'] = int(math.floor(float(self.game.turnNumber - 1) / 2)) 
    results['black']['time'] = self.game.blackPlayer.timeUsed

    return results

  def readBot(self, color, bot=''):
    while True:
      if not bot:
        bot = raw_input(color.capitalize() + " player bot (blank for human): ")
      else:
        sys.stdout.write(color.capitalize() + " player bot (blank for human): " + bot + "\n")

      # tack on .exe if Windows
      if os.name == 'nt' and not bot == '' and bot.rfind('.') < 0:
        bot += '.exe'

      if bot == '':
        return None
      elif os.path.exists(bot):
        return bot
      else:
        sys.stdout.write("Couldn't locate the bot. Try again.\n")
        bot = None
    return None


  def readMove(self): 
    moveString = 'error'
    moveTime = 0.0
    errorOutput = 0

    if self.game.currentPlayer.bot:
      try:
        bot = self.game.currentPlayer.bot
        if bot.endswith('.py'):
          bot = 'python ' + bot

        commandLine = bot + ' --times="' + self.game.getTimeControlsCsv() + '" --moves="' + self.game.getMoveListCsv() + '"'
        logging.debug('Framework.readMove: commandLine = ' + commandLine)
        args = shlex.split(commandLine)

        startTime = time()
        botProcess = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=None)
        moveString, errorOutput = botProcess.communicate()
        endTime = time()

        sys.stderr.write(errorOutput)
        moveTime = round((endTime - startTime) * 100)
        self.game.currentPlayer.timeUsed += moveTime
      except OSError as details:
        logging.debug('Framework.readMove: OSError = ' + str(details))
        raise InputError(self.game.currentPlayer.bot + ' process failed to execute')
    else:
      moveString = raw_input(self.game.currentPlayer.color.capitalize() + "'s turn: ")

    return (moveString, moveTime, errorOutput)


if __name__ == "__main__": 
  Framework(sys.argv).run()

