import logging
import re
import sys
from cmd2 import Cmd
from errors import *
from pieces import *
from player import *
from hive import *

class Game:
  def __init__(self, whiteBot, blackBot, timeControls, moveList):
    self.whitePlayer = Player('white', whiteBot)
    self.blackPlayer = Player('black', blackBot)
    self.currentPlayer = self.whitePlayer
    self.turnNumber = 1
    self.gameTime = 300000 #ms
    self._readTimeControls(timeControls)
    self.moveList = []
    self._readMoveList(moveList)
    self.hive = Hive()
    self.winner = None

  def makeMove(self, moveString):
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
    if piece.coordinates == (None,None,None): # not on board yet
      logging.debug('Game.makeMove: piece not on board')
      possibleCoordinatesList = self.hive.getEntryCoordinatesList(piece.color)
    elif not piece == self.hive.getTopPieceAtCoordinates(piece.coordinates): # beetle pinned
      logging.debug('Game.makeMove: piece beetle pinned')
      possibleCoordinatesList = []
    elif self.hive.isBrokenWithoutPiece(piece): # if picking up breaks hive: 0 possible coordinates
      logging.debug('Game.makeMove: breaks hive')
      possibleCoordinatesList = []
    else:
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


  def isGameOver(self):
    # check for wins/stalemate (via surrounding)
    surrounded = self.hive.getSurroundedQueenColors()
    logging.debug('Game.isGameOver surrounded = ' + str(surrounded))
    if len(surrounded) > 0:
      if len(surrounded) == 2:
        self.winner = 'draw'
      elif surrounded[0] == 'w':
        self.winner = 'black'
      else:
        self.winner = 'white'
      return True
    
    # check for stalemate (via threefold repetition)
    if self.currentPlayer.hasSeenThreefoldRepetition():
      self.winner = 'draw'
      return True

    return False
    

  def isValidMove(self, proposedCoordinates, possibleCoordinatesList):
    logging.debug('Game.isValidMove: proposedCoordinates=' + str(proposedCoordinates))
    logging.debug('Game.isValidMove: possibleCoordinatesList=' + str(possibleCoordinatesList))

    for coordinates in possibleCoordinatesList:
      if coordinates[0] == proposedCoordinates[0] and coordinates[1] == proposedCoordinates[1] and coordinates[2] == proposedCoordinates[2]:
        return True
    return False


  def validateMoveString(self, moveString):
    """ Basic input string validation (note: this is incomplete doesn't validate invalid stuff like wB3 -bQ2) """
    match = re.match('^[bw]?[ABGQS][0-3]?(?:\\s[\\\/-]?[bw][ABGQS][0-3]?[\\\/-]?)?$', moveString)
    if not match:
      raise InputError("The move you entered is not valid.")


  def parsePieceAttributes(self, moveString, currentColor):
    matches = re.search('^(?P<color>b|w)?(?P<kind>[ABGQS])(?P<number>[0-3]?)', moveString)
    color = matches.group('color')
    if not color:
      color = currentColor
    return (color, matches.group('kind'), matches.group('number'))


  def parseRelativeAttributes(self, moveString):
    matches = re.search(' (?P<lm>[\\\/-]?)(?P<color>b|w)(?P<kind>[ABGQS])(?P<number>[0-3]?)(?P<rm>[\\\/-]?)$', moveString)
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
    self.currentPlayer.addHiveState(self.hive.zobrist.currentState)


  def _readMoveList(self, moveListCsv):
    moveList = moveListCsv.split(', ')
    for move in moveList:
      if not move == '':
        move = re.sub('^[0-9]+. ', '', move)
        self.makeMove(move)

  def getMoveListCsv(self):
    return ','.join(map(str, self.moveList))


  def _readTimeControls(self, timeControlsCsv):
    timeControls = timeControlsCsv.split(',')
    self.gameTime = timeControls[0]
    self.whitePlayer.timeUsed = timeControls[1]
    self.blackPlayer.timeUsed = timeControls[2]

  def getTimeControlsCsv(self):
    return str(self.gameTime) + ',' + str(self.whitePlayer.timeUsed) + ',' + str(self.blackPlayer.timeUsed)
   

  def printBoard(self):
    self.hive.printBoard()

