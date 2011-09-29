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
    self.whitePlayer = Player('white', whiteBot, expansions)
    self.blackPlayer = Player('black', blackBot, expansions)
    self.currentPlayer = self.whitePlayer
    self.turnNumber = 1
    self.hive = Hive(expansions)

    self.gameTime = 300000 #ms
    self._readTimeControls(timeControls)
    self.moveList = []
    self._readMoveList(moveList)
    self.winner = None


  def playMove(self, moveString):
    self.validateMoveString(moveString)

    # check if the piece hasn't been played yet, otherwise take if from the board
    pieceAttributes = self.parsePieceAttributes(moveString, self.currentPlayer.color)
    piece = self.currentPlayer.getPiece(pieceAttributes)
    if not piece:
      raise InputError ("The piece you entered is not valid.")

    # may not move a piece until queen is moved
    if self.currentPlayer.hasPlayed(piece.kind, piece.number) and not self.currentPlayer.hasPlayed('Q'):
      raise MoveError("You must play your Queen Bee before you may move other insects.")

    # queen must be played in a player's first 4 moves
    if self.turnNumber / 2 + 1 == 4 and not self.currentPlayer.hasPlayed('Q') and not piece.kind == 'Q':
      raise MoveError("You must play your Queen Bee in your first 4 turns.")

    # get proposed move coordinates
    relativePiece = None
    relativePosition = None
    relativeAttributes = self.parseRelativeAttributes(moveString)
    if (relativeAttributes):
      relativePiece = self.hive.getPiece(relativeAttributes[0])
      if not relativePiece:
        raise InputError ("The relative piece you entered is not valid.")
      relativePosition = relativeAttributes[1]
    proposedCoordinates = self.hive.getRelativeCoordinates(piece, relativePiece, relativePosition)

    # check if valid move
    possibleCoordinatesList = piece.getPossibleCoordinatesList(self.hive)
    if not self.isValidMove(proposedCoordinates, possibleCoordinatesList):
      raise MoveError ("The move you entered is not valid.")

    # make the move
    if not piece.coordinates == (None, None, None):
      self.hive.pickupPiece(piece)
    self.hive.putdownPiece(piece, proposedCoordinates)

    self.moveList.append(str(self.turnNumber) + '. ' + moveString)
    self.turnNumber += 1
    self.switchCurrentPlayer()
    self.currentPlayer.addHiveState(self.hive.getState())


  def isGameOver(self):
    return not self.getWinner() == Game.WINNER_NONE


  def getWinner(self):
    surrounded = self.hive.getSurroundedQueenColors() # check for wins/stalemate (via surrounding)
    logging.debug('Game.isGameOver surrounded = ' + str(surrounded))
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
    

  def isValidMove(self, proposedCoordinates, possibleCoordinatesList):
    logging.debug('Game.isValidMove: proposedCoordinates=' + str(proposedCoordinates))
    logging.debug('Game.isValidMove: possibleCoordinatesList=' + str(possibleCoordinatesList))

    for coordinates in possibleCoordinatesList:
      if coordinates[0] == proposedCoordinates[0] and coordinates[1] == proposedCoordinates[1] and coordinates[2] == proposedCoordinates[2]:
        return True
    return False


  def getValidMoves(self):
    moveList = []

    if self.turnNumber / 2 + 1 == 4 and not self.currentPlayer.hasPlayed('Q'):
      # queen must be played in a player's first 4 moves
      queenBee = self.currentPlayer.pieces['Q']
      for coordinates in queenBee.getPossibleCoordinatesList(self.hive):
        moveList.append(Move(queenBee, queenBee.coordinates, coordinates))
      return moveList

    # may not move a piece until queen is moved
    canMoveHivePieces = True
    if not self.currentPlayer.hasPlayed('Q'):
      canMoveHivePieces = False

    for key, piece in self.currentPlayer.pieces.iteritems():
      if canMoveHivePieces or piece.coordinates == (None, None, None):
        for coordinates in piece.getPossibleCoordinatesList(self.hive):
          moveList.append(Move(piece, piece.coordinates, coordinates))

    return moveList


  def makeMove(self, move):
    logging.debug('Game.makeMove: move =' + str(move))

    if not move.startCoordinates == (None, None, None):
      self.hive.pickupPiece(move.piece)
    self.hive.putdownPiece(move.piece, move.endCoordinates)

    #self.moveList.append(str(self.turnNumber) + '. ' + move.getMoveString(self.hive))
    self.turnNumber += 1
    self.switchCurrentPlayer()
    self.currentPlayer.addHiveState(self.hive.getState())


  def unmakeMove(self, move):
    logging.debug('Game.makeMove: move =' + str(move))

    self.hive.pickupPiece(move.piece)
    if move.startCoordinates == (None, None, None):
      move.piece.coordinates = (None, None, None)
    else:
      self.hive.putdownPiece(move.piece, move.startCoordinates)

    #self.moveList.pop()
    self.turnNumber += 1
    self.switchCurrentPlayer()
    self.currentPlayer.removeHiveState()
    

  def getMoveNotation(self, move):
    logging.debug('Game.getMoveNotation: move = ' + str(move))

    moveString = move.piece.getNotation()

    #(x, y-1) TOPRIGHT
    coordinates = (move.endCoordinates[0], move.endCoordinates[1] - 1, 0)
    relativePiece = self.hive.getTopPieceAtCoordinates(coordinates)
    if relativePiece:
      logging.debug('Game.getMoveNotation: topright = ' + str(relativePiece))
      return moveString + ' ' + Hive.TOPRIGHT.strip()+ relativePiece.getNotation()

    #(x+1, y) RIGHT
    coordinates = (move.endCoordinates[0] + 1, move.endCoordinates[1], 0)
    relativePiece = self.hive.getTopPieceAtCoordinates(coordinates)
    if relativePiece:
      logging.debug('Game.getMoveNotation: right = ' + str(relativePiece))
      return moveString + ' ' + Hive.RIGHT.strip()+ relativePiece.getNotation()

    #(x+1, y+1) BOTTOMRIGHT
    coordinates = (move.endCoordinates[0] + 1, move.endCoordinates[1] + 1, 0)
    relativePiece = self.hive.getTopPieceAtCoordinates(coordinates)
    if relativePiece:
      logging.debug('Game.getMoveNotation: bottomright = ' + str(relativePiece))
      return moveString + ' ' + Hive.BOTTOMRIGHT.strip()+ relativePiece.getNotation()

    #(x, y+1) BOTTOMLEFT
    coordinates = (move.endCoordinates[0], move.endCoordinates[1] + 1, 0)
    relativePiece = self.hive.getTopPieceAtCoordinates(coordinates)
    if relativePiece:
      logging.debug('Game.getMoveNotation: bottomleft = ' + str(relativePiece))
      return moveString + ' ' + relativePiece.getNotation() + Hive.BOTTOMLEFT.strip()

    #(x-1, y) LEFT
    coordinates = (move.endCoordinates[0] - 1, move.endCoordinates[1], 0)
    relativePiece = self.hive.getTopPieceAtCoordinates(coordinates)
    if relativePiece:
      logging.debug('Game.getMoveNotation: left = ' + str(relativePiece))
      return moveString + ' ' + relativePiece.getNotation() + Hive.LEFT.strip()

    #(x-1, y-1) TOPLEFT
    coordinates = (move.endCoordinates[0] - 1, move.endCoordinates[1] - 1, 0)
    relativePiece = self.hive.getTopPieceAtCoordinates(coordinates)
    if relativePiece:
      logging.debug('Game.getMoveNotation: topleft = ' + str(relativePiece))
      return moveString + ' ' + relativePiece.getNotation() + Hive.TOPLEFT.strip()

    return moveString


  def validateMoveString(self, moveString):
    """ Basic input string validation (note: this is incomplete doesn't validate invalid stuff like wB3 -bQ2) """
    match = re.match('^[bw]?[ABGLMQS][0-3]?(?:\\s[\\\/-]?[bw][ABGLMQS][0-3]?[\\\/-]?)?$', moveString)
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
    return ', '.join(map(str, self.moveList))


  def _readTimeControls(self, timeControlsCsv):
    timeControls = timeControlsCsv.split(',')
    self.gameTime = float(timeControls[0])
    self.whitePlayer.timeUsed = float(timeControls[1])
    self.blackPlayer.timeUsed = float(timeControls[2])


  def getTimeControlsCsv(self):
    return str(self.gameTime) + ',' + str(self.whitePlayer.timeUsed) + ',' + str(self.blackPlayer.timeUsed)
   

  def printBoard(self):
    self.hive.printBoard()

