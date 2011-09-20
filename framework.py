import sys
import re
import logging

logging.basicConfig(level=logging.DEBUG)


class Piece:
  def __init__(self, color, kind, number):
    self.color = color
    self.kind = kind
    self.number = number
    self.coordinates = (None, None, None) #x,y,z

  def pickup(self):
    logging.debug('Piece.pickup: ' + self.getNotation());
    self.coordinates = (None, None, None)

  def getNotation(self):
    return self.color + self.kind + str(self.number)#+ ' @ ' + str(self.coordinates)

  def getPbemNotation(self):
    notation = self.kind
    if notation == 'G': notation = 'H'
    if self.color == 'b': notation = notation.lower()
    return notation 

  def __repr__(self):
    return self.color + self.kind + str(self.number) + ' @ ' + str(self.coordinates)

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



"""                                   
  The Hive "board"

                       +  1   2   3   4   5   6   7   8   9   10
                                                                  
                    A   .   .   .   .   .   .   .   .   .   .   A
                                                                  
                  B   .   .   .   .   .   .   .   .   .   .   B
                                                                  
                C   .   .   .   .   .   .   .   .   .   .   C
                                                                  
              D   .   .   .   .   .   .   .   .   .   .   D
                           / \ / \
            E   .   .   . | * | * | .   .   .   .   .   E
                         / \ / \ / \
          F   .   .   . | * | Q | * | .   .   .   .   F
                         \ / \ / \ /
        G   .   .   .   . | * | * | .   .   .   .   G
                           \ / \ /
      H   .   .   .   .   .   .   .   .   .   .   H
                                                                  
    I   .   .   .   .   .   .   .   .   .   .   I
                                                                  
  J   .   .   .   .   .   .   .   .   .   .   J
                                                                  
    1   2   3   4   5   6   7   8   9   10


  The hive is not limited to this 10 by 10 board, the first piece will be placed at (0,0) and it will expand infinitely in both the positive and negative directions. 
  This is a three dimensional board with the pieces initially played at z=0 (where z is left out of the coordinantes we assume the piece with max(z)).

  (x, y) connects to:
    (x, y-1) TOPRIGHT
    (x+1, y) RIGHT
    (x+1, y+1) BOTTOMRIGHT
    (x, y+1) BOTTOMLEFT
    (x-1, y) LEFT
    (x-1, y-1) TOPLEFT
    Also connects to pieces at (x,y,z-1) COVERING and (x,y,z+1) COVERED
   

  Since the board expands ad infinitum, we will use a dictionary with keys "x,y". Where each entry is a list of pieces at the square.
  e.g.:
    board["0,0"] = [wQ]
    board["-1,0"] = [bQ, wB1]   -- the white beetle is ontop of of the black queen bee, each piece will know their z value to find the max
    board["-1,-1] = [bG1]

"""
class Hive:
  # relative movement directives (not connectivity)
  (TOPRIGHT, RIGHT, BOTTOMRIGHT, BOTTOMLEFT, LEFT, TOPLEFT, COVER) = (' /', ' -', ' \\', '/ ', '- ', '\\ ', '  ') 

  def __init__(self):
    self.board = dict()

  def getBoardKey(self, coordinates):
    return str(coordinates[0]) + ',' + str(coordinates[1])

  def pickupPiece(self, color, kind, number):
    piece = self.getPiece(color, kind, number)
    if piece:
      # remove space from board or remove piece from space (if there are other pieces on it)
      key = self.getBoardKey(piece.coordinates)
      if len(self.board[key]) == 1:
        del self.board[key]
      else:
        self.board[key].remove(piece)
      piece.pickup()
      return piece
    return None

  def getPiece(self, color, kind, number):
    for key in self.board.keys():
      for piece in self.board[key]:
        if piece.color == color and piece.kind == kind and str(piece.number) == number:
          return piece
    return None 
  
  def putdownPiece(self, piece, relativePiece, relativePosition):
    logging.debug('Hive.putdownPiece: piece=' + piece.getNotation())

    newCoordinates = (0,0,0)
    if relativePiece:
      logging.debug('Hive.putdownPiece: relativePiece=' + relativePiece.getNotation())
      logging.debug('Hive.putdownPiece: relativePosition=' + relativePosition)

      relativeCoordinates = relativePiece.coordinates
      if relativePosition == Hive.TOPRIGHT:
        logging.debug('Hive.putdownPiece: TOPRIGHT')
        newCoordinates = (relativeCoordinates[0], relativeCoordinates[1] - 1, 0)
      elif relativePosition == Hive.RIGHT:
        logging.debug('Hive.putdownPiece: RIGHT')
        newCoordinates = (relativeCoordinates[0] + 1, relativeCoordinates[1], 0)
      elif relativePosition == Hive.BOTTOMRIGHT:
        logging.debug('Hive.putdownPiece: BOTTOMRIGHT')
        newCoordinates = (relativeCoordinates[0] + 1, relativeCoordinates[1] + 1, 0)
      elif relativePosition == Hive.BOTTOMLEFT:
        logging.debug('Hive.putdownPiece: BOTTOMLEFT')
        newCoordinates = (relativeCoordinates[0], relativeCoordinates[1] + 1, 0)
      elif relativePosition == Hive.LEFT:
        logging.debug('Hive.putdownPiece: LEFT')
        newCoordinates = (relativeCoordinates[0] - 1, relativeCoordinates[1], 0)
      elif relativePosition == Hive.TOPLEFT:
        logging.debug('Hive.putdownPiece: TOPLEFT')
        newCoordinates = (relativeCoordinates[0] - 1, relativeCoordinates[1] - 1, 0)
      elif relativePosition == Hive.COVER:
        logging.debug('Hive.putdownPiece: COVER')
        newCoordinates = (relativeCoordinates[0], relativeCoordinates[1], relativeCoordinates[2] + 1)

    key = self.getBoardKey(newCoordinates)
    if self.board.has_key(key):
      z = -1
      for p in self.board[key]:
        z = max(p.coordinates[2], z)
      z += 1
      self.board[key].append(piece)
    else:
      self.board[key] = [piece]

    piece.coordinates = newCoordinates



"""
  Prints the "board" by mapping the trapezoidal hex representation into a 2D char array as follows:

   0123456789012345
  0   / \ / \ / \                   
  1  | . | . | . |  0
  2 / \ / \ / \ /  
  3| . | * | .  1
  4 \ / \ /    
   0   1   2 

  Char array indices are on the left and top axes, hex indices on the bottom and right axies
  hex   -> char
  (0,0) -> (4,1)
  (1,0) -> (8,1)
  (2,0) -> (12,1)
  (0,1) -> (2,3)
  (1,1) -> (6,3)
  (2,1) -> (10,3)

  sx = 4*x - 2*y + 2*h
  sy = 2*y + 1

"""
  def printBoard(self):
    #debug print out all keys and pairs
    logging.debug('Hive.printBoard: board=' + str(self.board))


    # get max and min x/y values
    # iterate through all x,y printing empty piece or top most piece
    limits = self.getBoardLimits()
    limits[0] -= 1
    limits[1] -= 1
    limits[2] += 1
    limits[3] += 1
    width = limits[2] - limits[0] + 1
    height = limits[3] - limits[1] + 1
    #logging.debug('Hive.printBoard: limits=' + str(limits) + ', dims=' + str(width) + 'x' + str(height))

    # build a 2D array of chars that will eventually be printed
    s = [];
    for i in range (2 * height):
      s.append([' '] * (4 * width + 2 * height))

    #logging.debug('Hive.printBoard: s_dims=' + str(len(s[0])) + 'x' + str(len(s)))

    for y in range(limits[1], limits[3] + 1): # height/rows
      absy = y - limits[1]
      sy = 2 * absy + 1 #magic mapping formula

      for x in range(limits[0], limits[2] + 1): # width/columns
        absx = x - limits[0]
        sx = 4 * absx - 2 * absy + 2 * height #magic mapping formula
        #logging.debug('Hive.printBoard: (x,y)=(' + str(x) + ',' + str(y) + '), (absx,absy)=' + str(absx) + ',' + str(absy) + '), (sx,sy)=' + str(sx) + ',' + str(sy) + ')')
        key = self.getBoardKey((x, y))
        if self.board.has_key(key):
          piece = self.board[key][len(self.board[key]) - 1]
          s[sy][sx] = piece.getPbemNotation()
          s[sy-1][sx-1] = '/'
          s[sy][sx-2] = '|'
          s[sy+1][sx-1] = '\\'
          s[sy+1][sx+1] = '/'
          s[sy][sx+2] = '|'
          s[sy-1][sx+1] = '\\'
        else:
          s[sy][sx] = '.'
        

    for si in s:
      print ''.join(si)

  def getBoardLimits(self):
    limits = [0, 0, 0, 0] # xmin, ymin, xmax, ymax
    for key in self.board.keys():
      for piece in self.board[key]:
        limits[0] = min(limits[0], piece.coordinates[0])
        limits[1] = min(limits[1], piece.coordinates[1])
        limits[2] = max(limits[2], piece.coordinates[0])
        limits[3] = max(limits[3], piece.coordinates[1])
    return limits 

      
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

    # flip current player
    if self.currentPlayer == self.whitePlayer:
      self.currentPlayer = self.blackPlayer
    else:
      self.currentPlayer = self.whitePlayer

    # keep a running list of the played moves
    self.moveList.append(moveString)

  def getMoveListCsv(self):
    return ','.join(map(str, self.moveList))

  def printBoard(self):
    self.hive.printBoard()


def main():
    game = Game()

    print ('Hive AI Framework')
    print ('-------------------')
    print 

    enteredMove = None
    while True:
      enteredMove = raw_input(game.currentPlayer.color.capitalize() + '\'s turn, enter a move: ');
      if enteredMove == 'exit':
        break
      game.makeMove(enteredMove)
      print
      game.printBoard()
      print


    sys.exit(0)

if __name__ == "__main__": main() 

