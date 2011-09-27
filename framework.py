import argparse
import logging
import os
import shlex
import subprocess
import sys
import time
from cmd2 import Cmd
from errors import *
from player import *
from game import *

logging.basicConfig(level=logging.DEBUG)

class Framework():
  def __init__(self, args):
    self.args = self._parseArgs(args)

  def _parseArgs(self, args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--white')
    parser.add_argument('--black')
    parser.add_argument('--times', default='30000,0,0')
    parser.add_argument('--moves', default='')
    args = parser.parse_args(args.split())
    args = vars(args)
    logging.debug('Framework._parseArgs: args = ' + str(args))
    return args

  def run(self):
    self.args['white'] = self.readBot('white', self.args['white'])
    self.args['black'] = self.readBot('black', self.args['black'])
    self.game = Game(self.args['white'], self.args['black'], self.args['times'], self.args['moves'])

    while not self.game.isGameOver():
      moveString = self.readMove()
      if moveString == 'quit' or moveString == 'exit':
        break
      try:
        print self.game.currentPlayer.color.capitalize() + ' plays ' + moveString
        self.game.makeMove(moveString)
      except InputError as e:
        print e.value
        if self.game.currentPlayer.bot: break;
      except MoveError as e:
        print e.value
        if self.game.currentPlayer.bot: break;
      else:
        self.game.printBoard()


  def readBot(self, color, bot=''):
    while True:
      if not bot:
        bot = raw_input(color.capitalize() + " player bot (blank for human): ")
      else:
        print color.capitalize() + " player bot (blank for human): " + bot

      if bot == '':
        return None
      elif os.path.exists(bot):
        return bot
      else:
        print "Couldn't locate the bot. Try again."
        bot = None
    return None


  def readMove(self): 
    moveString = 'error'
    if self.game.currentPlayer.bot:
      try:
        commandLine = self.game.currentPlayer.bot + '--times="' + self.game.getTimeControlsCsv() + '" --moves="' + self.game.getMovesListCsv() + '"'
        args = shlex.split(commandLine)
        startTime = time()
        botProcess = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=None)
        moveString = botProcess.communicate()[0]
        endTime = time()
        totalTime = endTime - startTime()
        self.game.currentPlayer.timeUsed += totalTime
        logging.debug('Framework.readMove bottime = ' + str (totalTime))
      except OSError as details:
        logging.debug('Framework.readMOve OSError = ' + str(details))
        raise InputError(player.bot + ' process failed to execute')
    else:
      moveString = raw_input(self.game.currentPlayer.color.capitalize() + "'s turn: ")

    return moveString



class HiveCmd(Cmd):
  """ Hive Bot Framework """
  prompt = 'hive> '
  intro = 'Hive Bot Framework\n------------------'

  def do_game(self, args = ''):
    Framework(args).run()


if __name__ == "__main__": 
  HiveCmd().cmdloop() 

