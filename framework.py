import sys
import re


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

    return siblings

  def getFirstSibling(self):
    siblings = self.getSiblings()
    if len(siblings) > 0:
      return siblings[0]
    return None


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
      self.pieces[key] = None
    return piece


class Player:
  def __init__(self, color):
    self.pile = Pile(color);
    self.color = color;

  def pickupPiece(self, color, kind, number):
    return self.pile.pickupPiece(color, kind, number)


class Hive:
  #(TOPRIGHT, RIGHT, BOTTOMRIGHT, BOTTOMLEFT, LEFT, TOPLEFT, COVER) = (' /', ' -', ' \\', '/ ', '- '. '\\ ', '  ') 
  
  def __init__(self):
    self.head = None

  def pickupPiece(self, color, kind, number):
    piece = getPiece(color, kind, number)
    if piece:
      if piece == self.head:
        self.head = piece.getFirstSibling()
      piece.pickup();
    return None

  def getPiece(self, color, kind, number):
    if not self.head:
      return None
    return self.findPiece(None, self.head, color, kind, number)

  def findPiece(self, previousSibling, piece, color, kind, number):
    if piece.color == color and piece.kind == kind and piece.number == number:
      return piece;

    siblings = piece.getSiblings()
    for sibling in siblings:
      if (sibling != previousSibling): #stops circular references
        return self.findPiece(previousSibling, sibling, color, kind, number)

    return None
  

  def putdownPiece(self, piece, relativePiece, relativePosition):
    if not self.head or not relativePiece:
      self.head = piece
    else:
      if relativePosition == Hive.TOPRIGHT:
        relativePiece.topRightSibling = piece
        piece.bottomLeftSibling = relativePiece
      elif relativePosition == Hive.RIGHT:
        relativePiece.rightSibling = piece
        piece.leftSibling = relativePiece
      elif relativePosition == Hive.BOTTOMRIGHT:
        relativePiece.bottomRightSibling = piece
        piece.topLeftSibling = relativePiece
      elif relativePosition == Hive.TOPLEFT:
        relativePiece.topLeftSibling = piece
        piece.bottomRightSibling = relativePiece
      elif relativePosition == Hive.LEFT:
        relativePiece.leftSibling = piece
        piece.rightSibling = relativePiece
      elif relativePosition == Hive.BOTTOMLEFT:
        relativePiece.bottomLeftSibling = piece
        piece.topRightSibling = relativePiece
      elif relativePosition == Hive.COVER:
        relativePiece.coveringSibling = piece
        piece.coveredSibling = relativePiece

        


      
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


    # check if the piece is being played relative to another
    relativePiece = None
    relativePosition = None 
    relativeMatches = re.search('(?P<lm>[\\\/-]?)(?P<color>b|w)(?P<kind>[ABGQS])(?P<number>[0-9]?)(?P<rm>[\\\/-]?)$', moveString)
    if relativeMatches:
      relativeColor = relativeMatches.group('color')
      relativeKind = relativeMatches.group('kind')
      relativeNumber = relativeMatches.group('number')
      relativePiece = self.hive.getPiece(relativeColor, relativeKind, relativeNumber)

      leftMove = relativeMatches.group('lm')
      rightMove = relativeMatches.group('rm')
      if not leftMove and not rightMove:
        relativePostion = '  '
      elif not leftMove: 
        relativePostion = ' ' + rightMove
      else:
        relativePosition = leftMove + ' '

    self.hive.putdownPiece(piece, relativePiece, relativePosition)

    if self.currentPlayer == self.whitePlayer:
      self.currentPlayer = self.blackPlayer
    else:
      self.currentPlayer = self.whitePlayer

    self.moveList.append(moveString)

  def getMoveListCsv(self):
    return ','.join(map(str, self.moveList))


def main():
    game = Game()

    print ('Hive framework v0.1')
    print ('-------------------')
    print 

    enteredMove = None
    while True:
      enteredMove = raw_input('Enter a move: ');
      if enteredMove == 'exit':
        break
      game.makeMove(enteredMove)
      print ("This is the current move list:")
      print (game.getMoveListCsv())
      print


    sys.exit(0)

if __name__ == "__main__": main() 

