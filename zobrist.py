import random

class Zobrist:
  """ This is a modification of Zobrist keys: they are lazily generated into a dictionary since the number of different hexes a piece can land throughout the game on is indeterminate. """
  def __init__(self):
    self.zobristKeys = dict()
    self.sideKey = self._generateRandomNumber()
    self.currentState = 0L


  def _getDictKey(self, color, kind, number = '', coordinates = (None, None, None)):
    return color + kind + str(number) + '@' + str(coordinates[0]) + ',' +  str(coordinates[1]) + ',' + str(coordinates[2])


  def _getZobristKey(self, color, kind, number = '', coordinates = (None, None, None)):
    dictKey = self._getDictKey(color, kind, number, coordinates)
    if not self.zobristKeys.has_key(dictKey):
      self.zobristKeys[dictKey] = self._generateRandomNumber()
    return self.zobristKeys[dictKey]


  def _generateRandomNumber(self): # is this sufficient?
    return random.randint(1, 2**32)


  def changeSide(self):
    self.currentState = self.currentState ^ self.sideKey
    #logging.debug('Zobrist.changeSide: state = ' + str(self.currentState))


  def updateState(self, piece):
    key = self._getZobristKey(piece.color, piece.kind, piece.number, piece.coordinates)
    self.currentState = self.currentState ^ key
    #logging.debug('Zobrist.updateState: state = ' + str(self.currentState))

