import logging
import random
from pieces import Point

class Zobrist:
  """ This is a modification of Zobrist keys: they are lazily generated into a dictionary since the number of different hexes a piece can land throughout the game on is indeterminate. """

  def __init__(self, numberOfPieces):
    self.zobristKeys = [[dict() for y in range(numberOfPieces)] for x in range(2)]
    self.sideKey = self._generateRandomNumber()
    self.currentState = 0L


  def _getDictKey(self, point = Point(None, None, None)):
    return str(point.x) + ',' +  str(point.y) + ',' + str(point.z)


  def _getZobristKey(self, colorIndex, kindIndex, point = Point(None, None, None)):
    dictKey = self._getDictKey(point)
    if not self.zobristKeys[colorIndex][kindIndex].has_key(dictKey):
      self.zobristKeys[colorIndex][kindIndex][dictKey] = self._generateRandomNumber()
    return self.zobristKeys[colorIndex][kindIndex][dictKey]


  def _generateRandomNumber(self): # is this sufficient?
    return random.randint(1, 2**32)


  def changeSide(self):
    self.currentState = self.currentState ^ self.sideKey
    logging.debug('Zobrist.changeSide: state = ' + str(self.currentState))


  def updateState(self, piece):
    key = self._getZobristKey(piece.getColorIndex(), piece.getKindIndex(), piece.point)
    self.currentState = self.currentState ^ key
    logging.debug('Zobrist.updateState: state = ' + str(self.currentState))

