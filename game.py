import logging
import re
import sys
from errors import *
from pieces import *
from player import *
from hive import *

class Game:
  (WINNER_WHITE, WINNER_BLACK, WINNER_DRAW, WINNER_NONE) = (1, -1, 0, None)

  def __init__(self, whiteBot, blackBot, timeControls, moveList, expansions):
    self.whitePlayer = Player(Player.WHITE, whiteBot, expansions)
    self.blackPlayer = Player(Player.BLACK, blackBot, expansions)
    self.currentPlayer = self.whitePlayer
    self.turnNumber = 1
    self.hive = Hive(expansions)

    self.gameTime = 300000 #ms
    self._readTimeControls(timeControls)
    self.moveList = []
    self._readMoveList(moveList)
    self.winner = None

  def getCurrentPlayer(self):
    return self.currentPlayer

  def getOpposingPlayer(self):
    if self.currentPlayer.color == Player.WHITE:
      return self.blackPlayer
    return self.whitePlayer

  def playMove(self, moveString):
    self.validateMoveString(moveString)

    if moveString == 'pass' and not len(self.getValidMoves()) == 0:
      raise MoveError("You cannot pass when you have legal moves.")
    else:
      # check if the piece hasn't been played yet, otherwise take if from the board
      pieceAttributes = self.parsePieceAttributes(moveString, self.currentPlayer.color)
      piece = self.currentPlayer.getPiece(pieceAttributes)
      if not piece:
        raise InputError ("The piece you entered is not valid.")

      # may not move a piece until queen is moved
      if self.currentPlayer.hasPlayed(piece.kind, piece.number) and not self.currentPlayer.hasPlayed('Q'):
        raise MoveError("You must play your Queen Bee before you may move other insects.")

      # queen must be played in a player's first 4 moves
      if (self.turnNumber + 1) / 2 == 4 and not self.currentPlayer.hasPlayed('Q') and not piece.kind == 'Q':
        raise MoveError("You must play your Queen Bee in your first 4 turns.")

      # get proposed move point
      relativePiece = None
      relativePosition = None
      relativeAttributes = self.parseRelativeAttributes(moveString)
      if (relativeAttributes):
        relativePiece = self.hive.getPiece(relativeAttributes[0])
        if not relativePiece:
          raise InputError ("The relative piece you entered is not valid.")
        relativePosition = relativeAttributes[1]
      proposedPoint = self.hive.getRelativePoint(piece, relativePiece, relativePosition)

      # check if valid move
      possiblePoints = piece.getPossiblePoints(self.hive)
      if not self.isValidMove(proposedPoint, possiblePoints):
        raise MoveError ("The move you entered is not valid.")

      # make the move
      if not piece.point == Point.NONE:
        self.hive.pickupPiece(piece)
      self.hive.putdownPiece(piece, proposedPoint)

    self.moveList.append(str(self.turnNumber) + '. ' + moveString)
    self.turnNumber += 1
    self.switchCurrentPlayer()
    self.currentPlayer.addHiveState(self.hive.getState())


  def isGameOver(self):
    return not self.getWinner() == Game.WINNER_NONE


  def getWinner(self):
    surrounded = self.hive.getSurroundedQueenColors() # check for wins/stalemate (via surrounding)
    if len(surrounded) > 0:
      if len(surrounded) == 2:
        return Game.WINNER_DRAW
      elif surrounded[0] == 'w':
        return Game.WINNER_BLACK
      else:
        return Game.WINNER_WHITE
      return True
    
    # check for stalemate (via threefold repetition)
    if self.currentPlayer.hasSeenThreefoldRepetition():
      return Game.WINNER_DRAW

    return Game.WINNER_NONE
    

  def isValidMove(self, proposedPoint, possiblePoints):
    logging.debug('Game.isValidMove: proposedPoint=' + str(proposedPoint))
    logging.debug('Game.isValidMove: possiblePoints=' + str(possiblePoints))

    for point in possiblePoints:
      if point.x == proposedPoint.x and point.y == proposedPoint.y and point.z == proposedPoint.z:
        return True
    return False


  def getValidMoves(self):
    moveList = []

    if (self.turnNumber + 1) / 2 == 4 and not self.currentPlayer.hasPlayed('Q'):
      # queen must be played in a player's first 4 moves
      queenBee = self.currentPlayer.pieces['Q']
      for point in queenBee.getPossiblePoints(self.hive):
        moveList.append(Move(queenBee, queenBee.point, point))
      return moveList

    # may not move a piece until queen is moved
    canMoveHivePieces = True
    if not self.currentPlayer.hasPlayed('Q'):
      canMoveHivePieces = False

    for key, piece in self.currentPlayer.pieces.iteritems():
      if canMoveHivePieces or not piece.isPlayed():
        for point in piece.getPossiblePoints(self.hive):
          moveList.append(Move(piece, piece.point, point))

    return moveList


  def makeMove(self, move):
    if not move.startPoint == Point.NONE:
      self.hive.pickupPiece(move.piece)
    self.hive.putdownPiece(move.piece, move.endPoint)

    #self.moveList.append(str(self.turnNumber) + '. ' + move.getMoveString(self.hive))
    self.turnNumber += 1
    self.switchCurrentPlayer()
    self.currentPlayer.addHiveState(self.hive.getState())


  def unmakeMove(self, move):
    self.hive.pickupPiece(move.piece)
    if move.startPoint == Point.NONE:
      move.piece.point = Point.NONE
    else:
      self.hive.putdownPiece(move.piece, move.startPoint)

    #self.moveList.pop()
    self.turnNumber += 1
    self.switchCurrentPlayer()
    self.currentPlayer.removeHiveState()
    

  def getMoveNotation(self, move):
    moveString = move.piece.getNotation()

    #(x+1, y) NORTHEAST
    relativePiece = self.hive.getTopPieceAtPoint(Point(move.endPoint.x + 1, move.endPoint.y, 0))
    if relativePiece:
      return moveString + ' ' + Hive.NORTHEAST.strip() + relativePiece.getNotation()

    #(x+1, y+1) EAST
    relativePiece = self.hive.getTopPieceAtPoint(Point(move.endPoint.x + 1, move.endPoint.y + 1, 0))
    if relativePiece:
      return moveString + ' ' + Hive.EAST.strip() + relativePiece.getNotation()

    #(x, y+1) SOUTHEAST
    relativePiece = self.hive.getTopPieceAtPoint(Point(move.endPoint.x, move.endPoint.y + 1, 0))
    if relativePiece:
      return moveString + ' ' + Hive.SOUTHEAST.strip() + relativePiece.getNotation()

    #(x-1, y) SOUTHWEST
    relativePiece = self.hive.getTopPieceAtPoint(Point(move.endPoint.x - 1, move.endPoint.y, 0))
    if relativePiece:
      return moveString + ' ' + relativePiece.getNotation() + Hive.SOUTHWEST.strip()

    #(x-1, y-1) WEST
    relativePiece = self.hive.getTopPieceAtPoint(Point(move.endPoint.x - 1, move.endPoint.y - 1, 0))
    if relativePiece:
      return moveString + ' ' + relativePiece.getNotation() + Hive.WEST.strip()

    #(x, y-1) NORTHWEST
    relativePiece = self.hive.getTopPieceAtPoint(Point(move.endPoint.x, move.endPoint.y - 1, 0))
    if relativePiece:
      return moveString + ' ' + relativePiece.getNotation() + Hive.NORTHWEST.strip()

    return moveString


  def validateMoveString(self, moveString):
    """ Basic input string validation (note: this is incomplete doesn't validate invalid stuff like wB3 -bQ2) """
    match = re.match('^(?:pass)|(?:[bw]?[ABGLMQS][0-3]?(?:\\s[\\\/-]?[bw][ABGLMQS][0-3]?[\\\/-]?)?)$', moveString)
    if not match:
      raise InputError("The move you entered is not valid.")


  def parsePieceAttributes(self, moveString, currentColor):
    matches = re.search('^(?P<color>b|w)?(?P<kind>[ABGLMQS])(?P<number>[0-3]?)', moveString)
    color = matches.group('color')
    if not color:
      color = currentColor
    return (color, matches.group('kind'), matches.group('number'))


  def parseRelativeAttributes(self, moveString):
    matches = re.search(' (?P<lm>[\\\/-]?)(?P<color>b|w)(?P<kind>[ABGLMQS])(?P<number>[0-3]?)(?P<rm>[\\\/-]?)$', moveString)
    if matches:
      position = (matches.group('lm') if matches.group('lm') != '' else ' ') + (matches.group('rm') if matches.group('rm') != '' else ' ')
      return ((matches.group('color'), matches.group('kind'), matches.group('number')), position)
    return None


  def switchCurrentPlayer(self):
    if self.currentPlayer == self.whitePlayer:
      self.currentPlayer = self.blackPlayer
    else:
      self.currentPlayer = self.whitePlayer
    self.hive.zobrist.changeSide()


  def _readMoveList(self, moveListCsv):
    moveList = moveListCsv.split(', ')
    for move in moveList:
      if not move == '':
        move = re.sub('^[0-9]+. ', '', move)
        self.playMove(move)


  def getMoveListCsv(self):
    return ', '.join(map(str, self.moveList)) + ', '


  def _readTimeControls(self, timeControlsCsv):
    timeControls = timeControlsCsv.split(',')
    self.gameTime = float(timeControls[0])
    self.whitePlayer.timeUsed = float(timeControls[1])
    self.blackPlayer.timeUsed = float(timeControls[2])


  def getTimeControlsCsv(self):
    return str(self.gameTime) + ',' + str(self.whitePlayer.timeUsed) + ',' + str(self.blackPlayer.timeUsed)
   

  def printBoard(self):
    self.hive.printBoard()

