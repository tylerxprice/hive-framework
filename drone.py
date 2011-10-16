import argparse
import random
import sys
from time import time
from game import *
from collections import namedtuple


class OpeningBook():
  """ 
  Very, very simple opening book to give the bot some direction. 
  Note: for this book to work the second move is assumed to be placed at -1,0
  """
  def __init__(self, game):
    self.game = game


  def findMove(self):
    """ 
        .   .   .
         / \
      . |wG1| .
         \ /
        .   .   .

    1. wG1
    """                                                       
    if self.game.turnNumber == 1:
      return Move(self.game.currentPlayer.pieces['G1'], Point.NONE, Point(0,0,0))

    """ 
       .   .   .   .
        / \ / \
     . |bG1|w__| .
        \ / \ /
       .   .   .   .

    1. w__, 2. bG1 -w__
    """                                                       
    if self.game.turnNumber == 2:
      return Move(self.game.currentPlayer.pieces['G1'], Point.NONE, Point(-1,-1,0))
    
    """ 
      .   .   .   .
               / \
        .   . |wQ | .
         / \ / \ /
      . |b__|wG1| .
         \ / \ /
        .   .   .   .

    1. wG1, 2. b__ -wG1, 3. wQ wG1/
    """                                                       
    if self.game.turnNumber == 3 || self.game.turnNumber == 4:
      entryPoints = self.game.hive.getEntryPoints(self.game.currentPlayer.color[0])
      return Move(self.game.currentPlayer.pieces['Q'], Point.NONE, entryPoints[0])



Transposition = namedtuple('Transposition', ['depth', 'value', 'flags', 'move'])

class TranspositionTable():
  (HASH_EXACT, HASH_BETA, HASH_ALPHA) = (1, 2, 3)

  def __init__(self):
    self.table = dict()


  def record(self, key, depth, value, flags, move = None):
    self.table[key] = Transposition(depth, flags, value, move)


  def probe(self, key, depth, alpha, beta):
    if self.table.has_key(key):
      transposition = self.table[key]
      if transposition.depth >= depth:
        if transposition.flags == TranspositionTable.HASH_EXACT:
          return transposition.value
        if transposition.flags == TranspositionTable.HASH_ALPHA and transposition.value <= alpha:
          return alpha
        if transposition.flags == TranspositionTable.HASH_BETA and transposition.value >= beta:
          return beta
    return None


  def _probeMove(self, key):
    if self.table.has_key(key):
      return self.table[key].move
    return None


  def collectPrincipleVariation(self, game, depth):
    principalVariation = []

    for i in range(depth,-1,-1):
      key = game.getState()
      move = self._probeMove(key)
      if not move:
        break 
      principalVariation.append(move)
      game.makeMove(move)

    for move in principalVariation:
      board.unmakeMove(move)

    return principalVariation



class MoveSearch():
  FIXED_DEPTH = 2
  QUIESCENT_SEARCH = False
  NULL_MOVE_REDUCTION = False
  NULL_MOVE_REDUCTION_R = 2
  ASPIRATION_WINDOW = 0 
  CONTEMPT_FACTOR = -5
  WIN_SCORE = 2**15 - 1

  def __init__(self, game):
    self.game = game
    self.horizonDepth = 1
    self.bestMove = None
    self.transpositionTable = TranspositionTable()
    self.heuristic = Heuristic(game)
    self.numberOfEvaluations = 0;
    self.numberOfNodesOpened = 0;


  def findMove(self):
    val = 0
    searchStartTime = time()

    if MoveSearch.FIXED_DEPTH:
      self.horizonDepth = MoveSearch.FIXED_DEPTH
      val = self.minimax(self.horizonDepth, float('-infinity'), float('infinity'))
    else:
      while True:
        self.numberOfEvaluations = 0;
        self.numberOfNodesOpened = 0;
        
        val = self.minimax(self.horizonDepth, float('-infinity'), float('infinity'))

        if self.horizonDepth >= 3: # this will be replaced by a timer
          break

        self.horizonDepth += 1

    searchEndTime = time()
    searchTime = round((searchEndTime - searchStartTime) * 100, 1)

    sys.stderr.write('%d . %f . %d . %d . %f/%d\n' % (self.horizonDepth, val, self.numberOfNodesOpened, self.numberOfEvaluations, searchTime, 0))

    return self.bestMove


  def minimax(self, depth, alpha, beta):
    """
      Basic Alpha-Beta min-maxing with Principal Variation Line and a Transposition Table
    """
    transpositionFlags = TranspositionTable.HASH_ALPHA
#    isInPrincipleVariation = False
    self.numberOfNodesOpened += 1

    val = self.transpositionTable.probe(self.game.hive.getState(), depth, alpha, beta)
    if not val == None:
      return val
    val = self.checkWinScore(depth)
    if not val == None:
      return val
    if depth <= 0:
      val = self.evaluate()
      self.transpositionTable.record(self.game.hive.getState(), depth, val, TranspositionTable.HASH_EXACT)
      return val

    validMoves = self.getValidMoves()
    self.orderMoves(validMoves)
    for move in validMoves:
      self.game.makeMove(move)

#      if isInPrincipleVariation:
#        val = -self.minimax(depth - 1, -alpha - 1, -alpha) # try a smaller window
#        if val > alpha and val < beta:
#          val = -self.minimax(depth - 1, -beta, -alpha) # pv failed, do aB regularly
#      else:
      val = -self.minimax(depth - 1, -beta, -alpha)
      
      self.game.unmakeMove(move)

      if val >= beta: # our opponent won't let us get to this move, it's too good
        self.transpositionTable.record(self.game.hive.getState(), depth, beta, TranspositionTable.HASH_BETA, move)
        return beta

      if val > alpha: # yea! a better move that we can get to
        alpha = val
#        isInPrincipleVariation = True
        transpositionFlags = TranspositionTable.HASH_EXACT
        if depth == self.horizonDepth:
          self.bestMove = move

    self.transpositionTable.record(self.game.hive.getState(), depth, alpha, transpositionFlags, self.bestMove)
    return alpha


  def checkWinScore(self, depth):
    winner = self.game.getWinner()
    if winner == Game.WINNER_NONE:
      return None

    signFlip = 1
    if self.game.currentPlayer.color == Player.BLACK:
      signFlip = -1

    if winner == Game.WINNER_DRAW:
      return signFlip * MoveSearch.CONTEMPT_FACTOR

    return signFlip * (MoveSearch.WIN_SCORE + depth) * winner

  def evaluate(self):
    self.numberOfEvaluations += 1;

    signFlip = 1
    if self.game.currentPlayer.color == Player.BLACK:
      signFlip = -1

    return signFlip * self.heuristic.evaluate()


  def getValidMoves(self):
    #can edit the valid move list here for testing...
    #piece = self.game.currentPlayer.pieces['B1']
    #moveList = []
    #for point in piece.getPossiblePoints(self.game.hive):
    #  moveList.append(Move(piece, piece.point, point))
    #
    #sys.stderr.write(str(moveList) + '\n\n')
    #return moveList
    return self.game.getValidMoves()



  def orderMoves(self, moveList):
    """
      Speed ups:
        * if more than one of a particular kind of piece in pile, don't check both (could be taken care of in transposition table anyways

      Ideas: 
        * simpleMobility to sort
        * if # free pieces < empty hexes around queen: look at adding pieces first:w
    """
    moveList.sort(key=lambda move: move.piece.isPlayed())
    return moveList



class Heuristic():
  """
    Positive = WHITE is winning!
  """
  (OPENING_PHASE, MIDGAME_PHASE, ENDGAME_PHASE) = (0, 1, 2)

  # estimated worth of the pieces (to use as a scaling factor)
  PIECE_VALUES = { 'A': 5, 'B': 5, 'G': 3, 'Q': 20, 'S': 1, 'M': 0, 'L': 0, 'D': 0} # expansion pieces not included

  # give weight to having pieces near the opposing queen bee (index = hexes away)
                        #0  1  2  3  4  5  6  7
  SPIDER_TROPISM      = [0, 5, 1, 2, 3, 0, 0, 0]  
  ANT_TROPISM         = [0, 5, 0, 0, 0, 0, 0, 0]
  BEETLE_TROPISM      = [5, 3, 4, 1, 0, 0, 0, 0]
  GRASSHOPPER_TROPISM = [0, 5, 1, 0, 0, 0, 0, 0]
  TROPISM_INDEX_MAX   = 7 # this index should have 0 tropism bonus

  QUEEN_SAFETY_SCORES = [0, 10, 0, -5, -15, -30, 0] # index = number of pieces surrounding

  ENTRY_POINT_SCORE = 1
  QUEEN_GATE_SCORE = 10

  def __init__(self, game):
    self.game = game

  def evaluate(self):
    """
      What makes a good Hive board state? Some thoughts:
      * mobility is key, being able to move pieces gives you control of the game
      * a pinned piece might be okay if it has 3 adjacent pieces and 2 free edges in a row (could escape when the 4th piece is played)

      * +limit where your opponent can add new pieces
      * +place new pieces in hexes not adjacent to the queen (may be included in queen safety evaluation and entry evaluation)

      * +piece values: spider < grasshopper < ant = beetle < queen bee
      * grasshopper and beetle may be worth more in end game (they can fill the final hexes adjacent to the queen)
      * +move pieces towards opponent's queen (tropism)

      * +leave 'controlled gates' next to your queen is good (limit ant/spider tropism to queen)
      * +have more pieces around the opponents queen is winning
      * need enough *free* pieces to surround opponents queen (not including own queen -- it's a bad attacking piece)

      * pin your opponents' pieces next to their queen
      * place pieces where they can't be pinned (unless next to opponents queen)
      * if a piece can be pinned by an opponent, it's in a bad spot
      * +don't unpin the opponent's queen (included in queen mobility evaluation)
      * don't unpin the opponent's first played piece

    """
    score = 0
    score += self.getPiecewiseEvaluation(self.game.hive, self.game.whitePlayer)
    score -= self.getPiecewiseEvaluation(self.game.hive, self.game.blackPlayer)
    return score


  def getPiecewiseEvaluation(self, hive, player):
    score = 0
    opposingQueen = self.game.whitePlayer.pieces['Q'] if player.color == Player.BLACK else self.game.blackPlayer.pieces['Q']
    queen = player.pieces['Q']

    # entry point eval: better if not near the queen
    if player.getNumberOfPiecesToPlay() > 0:
      nonQueenEntryPointCount = 0
      entryPoints = hive.getEntryPoints(player.color[0])
      for entryPoint in entryPoints:
        if not hive.arePointsAdjacent(entryPoint, queen.point):
          nonQueenEntryPointCount += 1
      score += nonQueenEntryPointCount * Heuristic.ENTRY_POINT_SCORE

    # Queen Evaluation...
    # pinned factor
    if queen.isPinned(hive):
      score -= Heuristic.PIECE_VALUES[queen.kind]
#    else:
#      score += Heuristic.PIECE_VALUES[queen.kind]

    queenAdjacentPieceCount = 0
    queenAdjacentPoints = hive.getAdjacentPoints(queen.point)
    for queenAdjacentPoint in queenAdjacentPoints:

      # queen safety factor
      if hive.getTopPieceAtPoint(queenAdjacentPoint):
        queenAdjacentPieceCount += 1

      # controlled gate factor
      if hive.isPointInGate(queenAdjacentPoint):
        # check to see if the gate is controlled (sides must be ours or pinned pieces)
        for index, adjacentPoint in enumerate(hive.getAdjacentPoints(queenAdjacentPoint)):
          if not hive.getTopPieceAtPoint(adjacentPoint): # empty adjacency from gate
            easterPoint = hive.getAdjacentPoint(adjacentPoint, ((index - 1) % 6))
            westerPoint = hive.getAdjacentPoint(adjacentPoint, ((index + 1) % 6))
            easterPiece = hive.getTopPieceAtPoint(easterPoint)
            westerPiece = hive.getTopPieceAtPoint(westerPoint)
            if easterPiece and (easterPiece.color == queen.color or easterPiece.isPinned(hive)) and westerPiece and (westerPiece.color == queen.color or westerPiece.isPinned(hive)):
              score += Heuristic.QUEEN_GATE_SCORE
            break

    score += Heuristic.QUEEN_SAFETY_SCORES[queenAdjacentPieceCount]


    # Spider Evaluation...
    for i in range(1,3):
      spider = player.pieces['S' + str(i)]
      if spider.isPlayed():
        
        # pinned factor
        if spider.isPinned(hive):
          score -= Heuristic.PIECE_VALUES[spider.kind]
#        else:
#          score += Heuristic.PIECE_VALUES[spider.kind]

        # tropism factor
        if opposingQueen.isPlayed():
          distanceFromOpposingQueen = hive.getDistanceBetweenPoints(spider.point, opposingQueen.point)
          distanceFromOpposingQueen = min(distanceFromOpposingQueen, Heuristic.TROPISM_INDEX_MAX)
          score += Heuristic.SPIDER_TROPISM[distanceFromOpposingQueen]

    # Beetle Evaluation...
    for i in range(1,3):
      beetle = player.pieces['B' + str(i)]
      if beetle.isPlayed():

        # pinned factor
        if beetle.isPinned(hive):
          score -= Heuristic.PIECE_VALUES[beetle.kind]
#        else:
#          score += Heuristic.PIECE_VALUES[beetle.kind]

        # tropism factor
        if opposingQueen.isPlayed():
          distanceFromOpposingQueen = hive.getDistanceBetweenPoints(beetle.point, opposingQueen.point)
          distanceFromOpposingQueen = min(distanceFromOpposingQueen, Heuristic.TROPISM_INDEX_MAX)
          score += Heuristic.BEETLE_TROPISM[distanceFromOpposingQueen]

    # Grasshopper Evaluation...
    for i in range(1,4):
      grasshopper = player.pieces['G' + str(i)]
      if grasshopper.isPlayed():
        
        # pinned factor
        if grasshopper.isPinned(hive):
          score -= Heuristic.PIECE_VALUES[grasshopper.kind]
#        else:
#          score += Heuristic.PIECE_VALUES[grasshopper.kind]

        # tropism factor
        if opposingQueen.isPlayed():
          distanceFromOpposingQueen = hive.getDistanceBetweenPoints(grasshopper.point, opposingQueen.point)
          distanceFromOpposingQueen = min(distanceFromOpposingQueen, Heuristic.TROPISM_INDEX_MAX)
          score += Heuristic.GRASSHOPPER_TROPISM[distanceFromOpposingQueen]


    # Ant Evaluation
    for i in range(1,4):
      ant = player.pieces['A' + str(i)]
      if ant.isPlayed():

        # pinned factor
        if ant.isPinned(hive):
          score -= Heuristic.PIECE_VALUES[ant.kind]
#        else:
#          score += Heuristic.PIECE_VALUES[ant.kind]

        # tropism factor
        if opposingQueen.isPlayed():
          distanceFromOpposingQueen = hive.getDistanceBetweenPoints(ant.point, opposingQueen.point)
          distanceFromOpposingQueen = min(distanceFromOpposingQueen, Heuristic.TROPISM_INDEX_MAX)
          score += Heuristic.ANT_TROPISM[distanceFromOpposingQueen]

    return score


  def getSimpleMobilityScore(self, player):
    """
      Give points equal to the piece worth if the piece can move _at all_
    """
    score = 0
    for key, piece in player.pieces.iteritems():
      if not piece.point == Point.NONE: # on board
        if not piece.isPinned(self.game.hive):
          score += Heuristic.PIECE_VALUES[piece.kind]
    return score


  def getGamePhase(self):
    """
      Game phases: 
        1. opening: neither queen is pinned, pieces still to come on the board
        2. mid-game: both queens are pinned, pieces still to come on the board
        3. end-game: no pieces left to come on the board
    """
    white = self.game.whitePlayer
    black = self.game.blackPlayer
    
    numberOfPieces = len(white.pieces) + len(black.pieces)
    numberOfPiecesPlayed = self.game.hive.getNumberOfPieces()

    if numberOfPieces == numberOfPiecesPlayed:
      return Heuristic.ENDGAME_PHASE

    isWhiteQueenPinned = white.pieces['Q'].isPinned(self.game.hive)
    isBlackQueenPinned = black.pieces['Q'].isPinned(self.game.hive)

    if isWhiteQueenPinned and isBlackQueenPinned:
      return Heuristic.MIDGAME_PHASE

    return Heuristic.OPENING_PHASE


class Drone():
  """ The bot that will play Hive """
  def __init__(self, args):
    self.args = self._parseArgs(args)
    self.game = Game('' , '', self.args['times'], self.args['moves'], self.args['expansions'])
    self.player = self.game.currentPlayer
    self.bestMove = None


  def _parseArgs(self, args):
    parser = argparse.ArgumentParser(prog="drone", argument_default='')
    parser.add_argument(args[0], default='')
    parser.add_argument('--times', default='30000,0,0') # game time, white used, black used (ms)
    parser.add_argument('--moves', default='') # 1. wS1, 2. bG1 -wS1, 3. wQ wS1/, ...
    parser.add_argument('--expansions', default='') # LM
    args = parser.parse_args(args)
    return vars(args)


  def run(self):
    self.bestMove = OpeningBook(self.game).findMove()
    if not self.bestMove:
      self.bestMove = MoveSearch(self.game).findMove()

    self.printMove()


  def printMove(self):
    if not self.bestMove:
      sys.stdout.write('pass')
    else:
      sys.stdout.write(self.game.getMoveNotation(self.bestMove))



if __name__ == "__main__": 
  Drone(sys.argv).run() 

