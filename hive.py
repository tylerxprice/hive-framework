import logging
import sys
from pieces import *
from zobrist import *
from collections import namedtuple

class Move(namedtuple('Move', ['piece', 'startPoint', 'endPoint'])):
  __slots__ = ()



class Hive:
  """ The Hive "board"
                         +  1   2   3   4   5   6   7   8   9   10
                                                                    
                      A   .   .   .   .   .   .   .   .   .   .   A
                                                                    
                    B   .   .   .   .   .   .   .   .   .   .   B
                                                                    
                  C   .   .   .   .   .   .   .   .   .   .   C
                                                                    
                D   .   .   .   .   .   .   .   .   .   .   D
                             / \ / \
              E   .   .   . | * | * | .   .   .   .   .   E
                           / \ / \ / \
            F   .   .   . | * |wQ | * | .   .   .   .   F
                           \ / \ / \ /
          G   .   .   .   . | * | * | .   .   .   .   G
                             \ / \ /
        H   .   .   .   .   .   .   .   .   .   .   H
                                                                    
      I   .   .   .   .   .   .   .   .   .   .   I
                                                                    
    J   .   .   .   .   .   .   .   .   .   .   J
                                                                    
      1   2   3   4   5   6   7   8   9   10

    The hive is not limited to this 10 by 10 board, the first piece will be placed at (0,0) and it will expand infinitely in both the positive and negative directions. 
    This is a three dimensional board with the pieces initially played at z=0 (where z is left out of the point we assume the piece with max(z)).

    (x, y) connects to:
      (x, y-1) TOPRIGHT
      (x+1, y) RIGHT
      (x+1, y+1) BOTTOMRIGHT
      (x, y+1) BOTTOMLEFT
      (x-1, y) LEFT
      (x-1, y-1) TOPLEFT
      Also connects to pieces at (x,y,z-1) COVERING and (x,y,z+1) COVERED
     
    Since the board expands ad infinitum, we will use a dictionary with keys "x,y". Where each entry is a list of pieces at the hex.
    e.g.:
      board["0,0"] = [wQ]
      board["-1,0"] = [bQ, wB1]   -- the white beetle is on top of of the black queen bee
      board["-1,-1] = [bG1]
  """

  # relative movement directives (not connectivity)
  (TOPRIGHT, RIGHT, BOTTOMRIGHT, BOTTOMLEFT, LEFT, TOPLEFT, COVER) = (' /', ' -', ' \\', '/ ', '- ', '\\ ', '  ') 

  def __init__(self, expansions):
    self.board = dict()
    self.zobrist = Zobrist(5 + len(expansions))


  def getBoardKey(self, point):
    return str(point.x) + ',' + str(point.y)


  def getTopPieceAtPoint(self, point):
    key = self.getBoardKey(point)
    if self.board.has_key(key):
      return self.board[key][len(self.board[key]) - 1]
    return None


  def getPiecesAtPoint(self, point):
    key = self.getBoardKey(point)
    if self.board.has_key(key):
      return self.board[key]
    return []


  def getNumberOfPieces(self):
    count = 0
    for key, value in self.board.iteritems():
      count += len(value)
    return count
  

  def getState(self):
    return self.zobrist.currentState


  def getAdjacentPoints(self, point):
    return [Point(point.x, point.y - 1, 0),      # (x, y-1)    TOPRIGHT
            Point(point.x + 1, point.y, 0),      # (x+1, y)    RIGHT
            Point(point.x + 1, point.y + 1, 0),  # (x+1, y+1)  BOTTOMRIGHT
            Point(point.x, point.y + 1, 0),      # (x, y+1)    BOTTOMLEFT
            Point(point.x - 1, point.y, 0),      # (x-1, y)    LEFT
            Point(point.x - 1, point.y - 1, 0)] # (x-1, y-1)  TOPLEFT


  def arePointsAdjacent(self, firstPoint, secondPoint):
    for point in self.getAdjacentPoints(firstPoint):
      if point.x == secondPoint.x and point.y == secondPoint.y:
        return True

    return False

  def doesPointOnlyBorderColor(self, point, color):
    for point in self.getAdjacentPoints(point):
      pointKey = self.getBoardKey(point)
      if self.board.has_key(pointKey):
        piece = self.board[pointKey][len(self.board[pointKey]) - 1]
        if not piece.color == color:
          return False

    return True


  def isPointInGate(self, point):
    """ point must be bordered on 5+ sides """
    borderCount = 0
    for point in self.getAdjacentPoints(point):
      piece = self.getTopPieceAtPoint(point)
      if piece:
        borderCount += 1

    return borderCount >= 5


  def hasTwoEmptyAdjacentPoints(self, point):
    adjacentPoints = self.getAdjacentPoints(point)

    freeCount = 0
    maxFreeCount = 0
    for adjacentPoint in adjacentPoints:
      if self.getTopPieceAtPoint(adjacentPoint):
        freeCount = 0 # reset free count
      else:
        freeCount += 1
      maxFreeCount = max(maxFreeCount, freeCount)

    return maxFreeCount > 1


  def getBorderPoints(self, includeGates):
    points = []
    uniquePoints = dict()
    
    for key, pieces in self.board.iteritems():
      piece = pieces[len(pieces) - 1]
      for point in self.getAdjacentPoints(piece.point):
        pointKey = self.getBoardKey(point)
        if not self.board.has_key(pointKey) and not uniquePoints.has_key(point):
          if includeGates or not self.isPointInGate(point):
            uniquePoints[pointKey] = 1
            points.append(point)
    
    return points; 


  def getEntryPoints(self, color):
    points = []
    uniquePoints = dict()

    for key, pieces in self.board.iteritems():
      piece = pieces[len(pieces) - 1] 

      adjacentPoints = self.getAdjacentPoints(piece.point)
      for point in adjacentPoints:
        pointKey = self.getBoardKey(point)
        if not self.board.has_key(pointKey) and not uniquePoints.has_key(pointKey):
          if self.getNumberOfPieces() == 1 or self.doesPointOnlyBorderColor(point, color):
            uniquePoints[pointKey] = 1
            points.append(point)

    if len(points) == 0:
      points.append(Point(0, 0, 0))

    return points; 


  def isBrokenWithoutPiece(self, piece):
    if len(self.board) == 0:
      return False
  
    visitedPieces = dict()

    self.pickupPiece(piece)

    # get a random piece
    key = self.board.keys()[0]
    rootPiece = self.board[key][len(self.board[key]) - 1]
    for p in self.board[key]: visitedPieces[p.getNotation()] = 1

    # try to visit all pieces in the hive
    self._visitPiece(rootPiece, visitedPieces)

    self.putdownPiece(piece, piece.point)

    logging.debug('Hive.isBrokenWithoutPiece: end state, board = ' + str(self.board))
    logging.debug('Hive.isBrokenWithoutPiece: end state, visitedPieces = ' + str(visitedPieces))
    logging.debug('Hive.isBrokenWithoutPiece: end state, numberOFPieces = ' + str(self.getNumberOfPieces()))

    # if all pieces were vistited the hive is still connected
    return not len(visitedPieces) == self.getNumberOfPieces() - 1


  def _visitPiece(self, piece, visitedPieces):
    logging.debug('Hive.visitPice: visiting = ' + str(piece))

    adjacentPoints = self.getAdjacentPoints(piece.point)
    
    for point in adjacentPoints:
      topPiece = self.getTopPieceAtPoint(point)
      if topPiece and not visitedPieces.has_key(topPiece.getNotation()):
        for p in self.getPiecesAtPoint(point):
          visitedPieces[p.getNotation()] = 1
        self._visitPiece(topPiece, visitedPieces)


  def getPiece(self, (color, kind, number)):
    for key in self.board.keys():
      for piece in self.board[key]:
        if piece.color == color and piece.kind == kind and str(piece.number) == number:
          return piece
    return None 

  
  def getRelativePoint(self, piece, relativePiece, relativePosition):
    newPoint = Point(0,0,0)
    if relativePiece:
      logging.debug('Hive.getRelativePoint: relativePiece=' + str(relativePiece))
      logging.debug('Hive.getRelativePoint: relativePosition=' + relativePosition)

      relativePoint = relativePiece.point
      if relativePosition == Hive.TOPRIGHT:
        logging.debug('Hive.getRelativePoint: TOPRIGHT')
        newPoint = Point(relativePoint.x, relativePoint.y - 1, 0)
      elif relativePosition == Hive.RIGHT:
        logging.debug('Hive.getRelativePoint: RIGHT')
        newPoint = Point(relativePoint.x + 1, relativePoint.y, 0)
      elif relativePosition == Hive.BOTTOMRIGHT:
        logging.debug('Hive.getRelativePoint: BOTTOMRIGHT')
        newPoint = Point(relativePoint.x + 1, relativePoint.y + 1, 0)
      elif relativePosition == Hive.BOTTOMLEFT:
        logging.debug('Hive.getRelativePoint: BOTTOMLEFT')
        newPoint = Point(relativePoint.x, relativePoint.y + 1, 0)
      elif relativePosition == Hive.LEFT:
        logging.debug('Hive.getRelativePoint: LEFT')
        newPoint = Point(relativePoint.x - 1, relativePoint.y, 0)
      elif relativePosition == Hive.TOPLEFT:
        logging.debug('Hive.getRelativePoint: TOPLEFT')
        newPoint = Point(relativePoint.x - 1, relativePoint.y - 1, 0)
      elif relativePosition == Hive.COVER:
        logging.debug('Hive.getRelativePoint: COVER')
        newPoint = Point(relativePoint.x, relativePoint.y, relativePoint.z + 1)
    return newPoint


  def pickupPiece(self, piece):
    key = self.getBoardKey(piece.point)
    if len(self.board[key]) == 1:
      del self.board[key]
    else:
      self.board[key].remove(piece)
    self.zobrist.updateState(piece)


  def putdownPiece(self, piece, point):
    key = self.getBoardKey(point)
    if self.board.has_key(key):
      z = -1
      for p in self.board[key]:
        z = max(p.point.z, z)
      z += 1
      point = Point(point.x, point.y, z)
      self.board[key].append(piece)
    else:
      self.board[key] = [piece]

    piece.point = point
    self.zobrist.updateState(piece)
  

  def getSurroundedQueenColors(self):
    surrounded = []

    for key, pieces in self.board.iteritems():
      for piece in pieces:
        if piece.kind == 'Q':
          isSurrounded = True
          for point in self.getAdjacentPoints(piece.point):
            if not self.getTopPieceAtPoint(point):
              isSurrounded = False
              break
          if isSurrounded:
            surrounded.append(piece.color)

    return surrounded


  def printBoard(self):
    """
      Prints the "board" by mapping the trapezoidal hex representation into a 2D char array as follows:
           sx        111111
           0123456789012345  y
       sy 0   / \ / \ / \     
          1  | . | . | . | 0  
          2 / \ / \ / \ /     
          3| . | . | .   1    
          4 \ / \ /           
           0   1   2   x      

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
      h = max(y)
    """

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
    s = []
    for i in range (2 * height + 2):
      s.append([' '] * (4 * width + 2 * height + 1 + 2)) # added 2 for padding

    #logging.debug('Hive.printBoard: s_dims=' + str(len(s[0])) + 'x' + str(len(s)))

    for y in range(limits[1], limits[3] + 2): # height/rows
      absy = y - limits[1]
      sy = 2 * absy + 1 #magic mapping formula
      
      if absy < height: # y-axis
        axisy = 4 * width - 2 * absy + 2 * height
        s[sy][axisy + 2] = str(y)

      for x in range(limits[0], limits[2] + 1): # width/columns
        absx = x - limits[0]
        sx = 4 * absx - 2 * absy + 2 * height + 2 #magic mapping formula

        if absy == height: # x-axis
          strx = str(x)
          for i in range(0,len(strx)): 
            s[sy][sx+i] = strx[i]
        else:
          key = self.getBoardKey(Point(x, y, 0))
          if self.board.has_key(key):
            piece = self.board[key][len(self.board[key]) - 1]
            s[sy][sx-1] = piece.color
            s[sy][sx] = piece.kind
            s[sy][sx+1] = str(piece.number) if piece.number else ' '
            s[sy-1][sx-1] = '/'
            s[sy][sx-2] = '|'
            s[sy+1][sx-1] = '\\'
            s[sy+1][sx+1] = '/'
            s[sy][sx+2] = '|'
            s[sy-1][sx+1] = '\\'
          else:
            s[sy][sx] = '.'
        

    sys.stderr.write('| ' + (' ' *  (4 * ((width -1) + 2) + 2 * height ) + 'y\n'))
    for si in s:
      if s.index(si) == len(s) - 1:
        sys.stderr.write('|x')
      else:
        sys.stderr.write('| ')
      sys.stderr.write(''.join(si) + '\n')

    sys.stderr.write('\n')


  def getBoardLimits(self):
    limits = [0, 0, 0, 0] # xmin, ymin, xmax, ymax
    for key in self.board.keys():
      for piece in self.board[key]:
        limits[0] = min(limits[0], piece.point.x)
        limits[1] = min(limits[1], piece.point.y)
        limits[2] = max(limits[2], piece.point.x)
        limits[3] = max(limits[3], piece.point.y)
    return limits 

