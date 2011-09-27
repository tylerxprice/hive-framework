from pieces import *

class Player:
  def __init__(self, color, bot):
    self.bot = bot
    self.color = color
    self.pieces = dict()
    self.setupStartingPieces(color[0])
    self.seenHiveStates = []


  def setupStartingPieces(self, color):
    self.pieces['Q'] = QueenBeePiece(color)
    self.pieces['S1'] = SpiderPiece(color, 1)
    self.pieces['S2'] = SpiderPiece(color, 2)
    self.pieces['B1'] = BeetlePiece(color, 1)
    self.pieces['B2'] = BeetlePiece(color, 2)
    self.pieces['A1'] = AntPiece(color, 1)
    self.pieces['A2'] = AntPiece(color, 2)
    self.pieces['A3'] = AntPiece(color, 3)
    self.pieces['G1'] = GrasshopperPiece(color, 1)
    self.pieces['G2'] = GrasshopperPiece(color, 2)
    self.pieces['G3'] = GrasshopperPiece(color, 3)


  def getPiece(self, (color, kind, number)):
    key = kind + str(number)
    return self.pieces[key]


  def hasPlayed(self, kind, number = ''):
    key = kind + str(number)
    return not self.pieces[key].coordinates == (None, None, None)


  def addHiveState(self, state):
    self.seenHiveStates.append(state)


  def hasSeenThreefoldRepetition(self):
    if len(self.seenHiveStates) < 5:
      return False

    length = len(self.seenHiveStates)
    return self.seenHiveStates[length - 5] == self.seenHiveStates[length - 3] == self.seenHiveStates[length - 1]