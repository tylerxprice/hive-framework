import sys
import re
import logging

logging.basicConfig(level=logging.DEBUG)


class Piece:
  def __init__(self, color, kind, number):
    self.color = color
    self.kind = kind
    self.number = number
    self.topLeftSibling = None
    self.leftSibling = None
    self.bottomLeftSibling = None
    self.topRightSibling = None
    self.rightSibling = None
    self.bottomRightSibling = None
    self.coveringSibling = None
    self.coveredSibling = None

  def pickup(self):
    logging.debug('Piece.pickup: ' + self.getNotation());

    if self.topLeftSibling:
      self.topLeftSibling.bottomRightSibling = None
      self.topLeftSibling = None
    if self.leftSibling:
      self.leftSibling.rightSibling = None
      self.leftSibling = None
    if self.bottomLeftSibling:
      self.bottomLeftSibling.topRightSibling = None
      self.bottomLeftSibling = None
    if self.topRightSibling:
      self.topRightSibling.bottomLeftSibling = None
      self.topRightSibling = None
    if self.rightSibling:
      self.rightSibling.leftSibling = None
      self.rightSibling = None
    if self.bottomRightSibling:
      self.bottomRightSibling.topLeftSibling = None
      self.bottomRightSibling = None
    if self.coveringSibling:
      self.coveringSibling.coveredSibling = None
      self.coveringSibling = None
    if self.coveredSibling:
      self.coveredSibling.coveringSibling = None
      self.coveredSibling = None


  def getSiblings(self):
    siblings = []
    if self.topLeftSibling:
      siblings.append(self.topLeftSibling)
    if self.leftSibling:
      siblings.append(self.leftSibling)
    if self.bottomLeftSibling:
      siblings.append(self.bottomLeftSibling)
    if self.topRightSibling:
      siblings.append(self.topRightSibling)
    if self.rightSibling:
      siblings.append(self.rightSibling)
    if self.bottomRightSibling:
      siblings.append(self.bottomRightSibling)
    if self.coveringSibling:
      siblings.append(self.coveringSibling)
    if self.coveredSibling:
      siblings.append(self.coveredSibling)

    logging.debug('Piece.getSiblings found ' + str(len(siblings)) + ' siblings.')
    return siblings

  def getFirstSibling(self):
    siblings = self.getSiblings()
    if len(siblings) > 0:
      return siblings[0]
    return None

  def getNotation(self):
    return self.color + self.kind + str(self.number)


class QueenBeePiece(Piece):
  """
    The Queen Bee piece. It moves one hex at a time and cannot be surrounded or the player looses.
  """
  def __init__(self, color):
    Piece.__init__(self, color, 'Q', '')

class SpiderPiece(Piece):
  """
    The Spider piece. It moves exactly three hexes at a time.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'S', number)

class BeetlePiece(Piece):
  """
    The Beetle piece. It moves exactly one hexes at a time, but can cover other pieces.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'B', number)

class AntPiece(Piece):
  """
    The Ant piece. It moves anywhere on the outside of the hive.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'A', number)

class GrasshopperPiece(Piece):
  """
    The Grasshopper piece. It moves in a straight line over other pieces.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'G', number)


class Pile:
  def __init__(self, color):
    """
    Build dictionary of pieces available for use
    """
    self.pieces = dict()
    self.setupStartingPieces(color)

  def setupStartingPieces(self, color):
    self.pieces['Q'] = QueenBeePiece(color);
    self.pieces['S1'] = SpiderPiece(color, 1);
    self.pieces['S2'] = SpiderPiece(color, 2);
    self.pieces['B1'] = BeetlePiece(color, 1);
    self.pieces['B2'] = BeetlePiece(color, 2);
    self.pieces['A1'] = AntPiece(color, 1);
    self.pieces['A2'] = AntPiece(color, 2);
    self.pieces['A3'] = AntPiece(color, 3);
    self.pieces['G1'] = GrasshopperPiece(color, 1);
    self.pieces['G2'] = GrasshopperPiece(color, 2);
    self.pieces['G3'] = GrasshopperPiece(color, 3);
  
  def pickupPiece(self, color, kind, number):
    key = kind + number
    piece = None
    if self.pieces.has_key(key):
      piece = self.pieces[key]
      del self.pieces[key]
      logging.debug("Pile.pickupPiece: " + piece.getNotation())
    return piece


class Player:
  def __init__(self, color):
    self.pile = Pile(color[0]);
    self.color = color;

  def pickupPiece(self, color, kind, number):
    return self.pile.pickupPiece(color, kind, number)


class Hive:
  (TOPRIGHT, RIGHT, BOTTOMRIGHT, BOTTOMLEFT, LEFT, TOPLEFT, COVER) = (' /', ' -', ' \\', '/ ', '- ', '\\ ', '  ') 
  
  def __init__(self):
    self.head = None

  def pickupPiece(self, color, kind, number):
    logging.debug('Hive.pickupPiece: color=' + color + ', kind=' + kind + ', number=' + number)
    piece = self.getPiece(color, kind, number)
    if piece:
      if piece == self.head:
        self.head = piece.getFirstSibling()
      piece.pickup();
      logging.debug("Hive.pickupPiece: " + piece.getNotation())
    return piece

  def getPiece(self, color, kind, number):
    if not self.head:
      logging.debug('Hive.getPiece: no head')
      return None
    return self.findPiece(None, self.head, color, kind, number)

  def findPiece(self, previousSibling, piece, color, kind, number):
    logging.debug('Hive.findPiece: ' + piece.getNotation() + ', color=' + color + ', kind=' + kind + ', number=' + number)

    if piece.color == color and piece.kind == kind and str(piece.number) == number:
      logging.debug('Hive.findPiece: matched')
      return piece;

    siblings = piece.getSiblings()
    for sibling in siblings:
      if sibling != previousSibling: #stops circular references
        return self.findPiece(piece, sibling, color, kind, number)

    return None
  

  def putdownPiece(self, piece, relativePiece, relativePosition):
    logging.debug('Hive.putdownPiece: piece=' + piece.getNotation())
    if relativePiece: 
      logging.debug('Hive.putdownPiece: relativePiece=' + relativePiece.getNotation())
    if relativePosition:
      logging.debug('Hive.putdownPiece: relativePosition=' + relativePosition)

    if not self.head or not relativePiece:
      self.head = piece
      logging.debug('Hive.putdownPiece: reset head')
    else:
      if relativePosition == Hive.TOPRIGHT:
        relativePiece.topRightSibling = piece
        piece.bottomLeftSibling = relativePiece
        logging.debug('Hive.putdownPiece: TOPRIGHT')
      elif relativePosition == Hive.RIGHT:
        relativePiece.rightSibling = piece
        piece.leftSibling = relativePiece
        logging.debug('Hive.putdownPiece: RIGHT')
      elif relativePosition == Hive.BOTTOMRIGHT:
        relativePiece.bottomRightSibling = piece
        piece.topLeftSibling = relativePiece
        logging.debug('Hive.putdownPiece: BOTTOMRIGHT')
      elif relativePosition == Hive.TOPLEFT:
        relativePiece.topLeftSibling = piece
        piece.bottomRightSibling = relativePiece
        logging.debug('Hive.putdownPiece: TOPLEFT')
      elif relativePosition == Hive.LEFT:
        relativePiece.leftSibling = piece
        piece.rightSibling = relativePiece
        logging.debug('Hive.putdownPiece: LEFT')
      elif relativePosition == Hive.BOTTOMLEFT:
        relativePiece.bottomLeftSibling = piece
        piece.topRightSibling = relativePiece
        logging.debug('Hive.putdownPiece: BOTTOMLEFT')
      elif relativePosition == Hive.COVER:
        relativePiece.coveringSibling = piece
        piece.coveredSibling = relativePiece
        logging.debug('Hive.putdownPiece: COVER')

      
class Game:
  def __init__(self):
    self.whitePlayer = Player('white')
    self.blackPlayer = Player('black')
    self.currentPlayer = self.whitePlayer
    self.hive = Hive()
    self.moveList = []

  def makeMove(self, moveString):

    # parse move string for the piece being placed
    pieceMatches = re.search('^(?P<color>b|w)(?P<kind>[ABGQS])(?P<number>[0-9]?)', moveString);
    pieceColor = pieceMatches.group('color')
    pieceKind = pieceMatches.group('kind')
    pieceNumber = pieceMatches.group('number')

    # check if the piece hasn't been played yet, otherwise take if from the board
    piece = self.currentPlayer.pickupPiece(pieceColor, pieceKind, pieceNumber) 
    if not piece:
      piece = self.hive.pickupPiece(pieceColor, pieceKind, pieceNumber)

    logging.debug('Game.makeMove picked up: ' + piece.getNotation())

    # check if the piece is being played relative to another
    relativePiece = None
    relativePosition = None 
    relativeMatches = re.search(' (?P<lm>[\\\/-]?)(?P<color>b|w)(?P<kind>[ABGQS])(?P<number>[0-9]?)(?P<rm>[\\\/-]?)$', moveString)
    if relativeMatches:
      relativeColor = relativeMatches.group('color')
      relativeKind = relativeMatches.group('kind')
      relativeNumber = relativeMatches.group('number')
      relativePiece = self.hive.getPiece(relativeColor, relativeKind, relativeNumber)
      logging.debug(relativeMatches.groupdict())
      logging.debug('Game.makeMove found relative piece: ' + relativePiece.getNotation())

      leftMove = relativeMatches.group('lm')
      rightMove = relativeMatches.group('rm')
      if leftMove == '' and rightMove == '':
        relativePosition = '  '
      elif leftMove == '': 
        relativePosition = ' ' + rightMove
      else:
        relativePosition = leftMove + ' '

    # play the piece
    self.hive.putdownPiece(piece, relativePiece, relativePosition)
    logging.debug('Game.makeMove piece putdown, len(piece.getSiblings())=' + str(len(piece.getSiblings())))

    # flip current player
    if self.currentPlayer == self.whitePlayer:
      self.currentPlayer = self.blackPlayer
    else:
      self.currentPlayer = self.whitePlayer

    # keep a running list of the played moves
    self.moveList.append(moveString)

  def getMoveListCsv(self):
    return ','.join(map(str, self.moveList))


def main():
    game = Game()

    print ('HiveAI Framework v0.1')
    print ('-------------------')
    print 

    enteredMove = None
    while True:
      enteredMove = raw_input(game.currentPlayer.color.capitalize() + '\'s turn, enter a move: ');
      if enteredMove == 'exit':
        break
      game.makeMove(enteredMove)
      print ("This is the current move list:")
      print (game.getMoveListCsv())
      print


    sys.exit(0)

if __name__ == "__main__": main() 

