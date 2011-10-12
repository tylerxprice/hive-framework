import argparse
import logging
import random
import sys
from game import *

#logging.basicConfig(level=logging.DEBUG)


class OpeningBook():
  """ 
  Very, very simple opening book to give the bot some direction. 
  """
  def __init__(self, game):
    self.game = game


  def findMove(self):
    logging.debug('OpeningBook.findMove: turnNumber = ' + str(self.game.turnNumber))
    """ 
                 -3  -2  -1   0   1   2   3  x

             -2  .   .   .   .   .   .   .   
                            
           -1  .   .   .   .   .   .   .   
                        / \                
          0  .   .   . | ? | .   .   .   
                        \ /           
       -1  .   .   .   .   .   .   .   
                                    
     -2  .   .   .   .   .   .   .   

    y

    1. ?
    """                                                       
    if self.game.turnNumber == 1:
      return Move(self.game.currentPlayer.pieces['G1'], Point.NONE, Point(0,0,0))


    """ 
                 -3  -2  -1   0   1   2   3  x

             -2  .   .   .   .   .   .   .   
                            
           -1  .   .   .   .   .   .   .   
                    / \ / \                
          0  .   . | ? |w__| .   .   .   
                    \ / \ /           
       -1  .   .   .   .   .   .   .   
                                    
     -2  .   .   .   .   .   .   .   

    y

    1. w_, 2. ? -w_
    """                                                       
    if self.game.turnNumber == 2:
      return Move(self.game.currentPlayer.pieces['G1'], Point.NONE, Point(-1,0,0))



class MoveSearch():
  WIN_SCORE = 2**15 - 1

  def __init__(self, game):
    self.game = game
    self.horizonDepth = 1
    self.bestMove = None
    self.heuristic = Heuristic(game)


  def findMove(self):
    self.minimax(self.horizonDepth, float('-infinity'), float('infinity'))
    return self.bestMove


  def minimax(self, depth, alpha, beta):
    """
      Basic Alpha-Beta min-maxing
    """
    val = self.checkWinScore()
    if not val == None:
      return val
    if depth <= 0:
      val = self.evaluate()
      return val

    validMoves = self.game.getValidMoves()
    for move in validMoves:
      self.game.makeMove(move)

      val = -self.minimax(depth - 1, -beta, -alpha)
      
      self.game.unmakeMove(move)

      if val >= beta: # our opponent won't let us get to this move, it's too good
        return beta

      if val > alpha: # yea! a better move that we can get to
        alpha = val
        if depth == self.horizonDepth:
          self.bestMove = move

    return alpha


  def checkWinScore(self):
    winner = self.game.getWinner()
    if winner == Game.WINNER_NONE:
      return None

    signFlip = 1
    if self.game.currentPlayer.color == Player.BLACK:
      signFlip = -1

    if winner == Game.WINNER_DRAW:
      return signFlip * MoveSearch.CONTEMPT_FACTOR

    return signFlip * MoveSearch.WIN_SCORE * winner


  def evaluate(self):
    signFlip = 1
    if self.game.currentPlayer.color == Player.BLACK:
      signFlip = -1

    return signFlip * self.heuristic.evaluate()


class Heuristic():
  """
    Positive => WHITE is winning!
  """
  def __init__(self, game):
    self.game = game

  def evaluate(self):
    return random.randrange(-10, 10)


class Randy():
  """ A bot that will play random moves in Hive """
  def __init__(self, args):
    self.args = self._parseArgs(args)
    self.game = Game('' , '', self.args['times'], self.args['moves'], self.args['expansions'])
    self.player = self.game.currentPlayer
    self.bestMove = None


  def _parseArgs(self, args):
    parser = argparse.ArgumentParser(prog="randy", argument_default='')
    parser.add_argument(args[0], default='')
    parser.add_argument('--times', default='30000,0,0') # game time, white used, black used (ms)
    parser.add_argument('--moves', default='') # 1. wS1, 2. bG1 -wS1, 3. wQ wS1/, ...
    parser.add_argument('--expansions', default='') # LMD
    args = parser.parse_args(args)
    logging.debug('Randy._parseArgs: args = ' + str(args))
    return vars(args)


  def run(self):
    #self.game.printBoard()

    self.bestMove = OpeningBook(self.game).findMove()
    if not self.bestMove:
      self.bestMove = MoveSearch(self.game).findMove()

    self.printMove()


  def printMove(self):
    logging.debug('Randy.printMove: bestMove = ' + str(self.bestMove))
    if not self.bestMove:
      sys.stdout.write('invalid move')
    else:
      sys.stdout.write(self.game.getMoveNotation(self.bestMove))



if __name__ == "__main__": 
  Randy(sys.argv).run() 

