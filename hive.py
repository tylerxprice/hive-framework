import logging
import math
import sys
from pieces import *
from zobrist import *
from collections import namedtuple

class Move(namedtuple('Move', ['piece', 'startPoint', 'endPoint'])):
  __slots__ = ()



class Hive:
  """ The Hive "board"
          x-axis     
    -1   0   1   2   3
      \   \   \   \   \
       .   .   .   .   .
      /     / \ / \
 y  -2   . |wQ |wS1| .
          / \ / \ /
 a     . |bQ | .   .   .
 x    /   \ /
 i  -1   .   .   .   .
 s
       .   .   .   .   .
      /
     0

    The hive is not limited to the size pictured, the first piece will be placed at (0,0) and the board may expand infinitely in both the positive and negative directions. 
    This is a three dimensional board with the pieces initially played at z=0 (where z is left out of the point we assume the piece with max(z)).

    (x, y) connects to:
      (x+1, y) NORTHEAST
      (x+1, y+1) EAST
      (x, y+1) SOUTHEAST
      (x-1, y) SOUTHWEST
      (x-1, y-1) WEST
      (x, y-1) NORTHWEST
      Also connects to pieces at (x,y,z-1) COVERING and (x,y,z+1) COVERED
     
    Since the board expands ad infinitum, we will use a dictionary with keys "x,y". Where each entry is a list of pieces at the hex.
    e.g.:
      board["0,0"] = [wQ]
      board["-1,0"] = [bQ, wB1]   -- the white beetle is on top of of the black queen bee
      board["-1,-1] = [bG1]


    hexspace -> array given by:
    hex2array(x,y) = (floor((x+y)/2),y-x)
    array -> hexspace given by:
    array2hex(x,y) = (x - floor(y/2),x+ceil(y/2))
    
    dX = B.x - A.x
    dY = B.y - A.y
    distance = (abs (dX) + abs (dY) + abs (dX - dY)) / 2

  """

  # relative movement directives (not connectivity)
  (NORTHEAST, EAST, SOUTHEAST, SOUTHWEST, WEST, NORTHWEST, COVER) = (' /', ' -', ' \\', '/ ', '- ', '\\ ', '  ') 

  # adjacent point indices
  ADJACENT_NORTHEAST = 0
  ADJACENT_EAST = 1
  ADJACENT_SOUTHEAST = 2
  ADJACENT_SOUTHWEST = 3
  ADJACENT_WEST = 4
  ADJACENT_NORTHWEST = 5

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
    return [Point(point.x + 1, point.y, 0),      # (x+1, y)   NORTHEAST
            Point(point.x + 1, point.y + 1, 0),  # (x+1, y+1) EAST
            Point(point.x, point.y + 1, 0),      # (x, y+1)   SOUTHEAST
            Point(point.x - 1, point.y, 0),      # (x-1, y)   SOUTHWEST
            Point(point.x - 1, point.y - 1, 0),  # (x-1, y-1) WEST
            Point(point.x, point.y - 1, 0)]      # (x, y-1)   NORTHWEST

  def getAdjacentPoint(self, point, index):
    if index == ADJACENT_NORTHEAST: 
      return Point(point.x + 1, point.y, 0)
    if index == ADJACENT_EAST: 
      return Point(point.x + 1, point.y + 1, 0)
    if index == ADJACENT_SOUTHEAST: 
      return Point(point.x, point.y + 1, 0)
    if index == ADJACENT_SOUTHWEST: 
      return Point(point.x - 1, point.y, 0)
    if index == ADJACENT_WEST: 
      return Point(point.x - 1, point.y - 1, 0)
    if index == ADJACENT_NORTHWEST: 
      return Point(point.x, point.y - 1, 0)



  def arePointsAdjacent(self, firstPoint, secondPoint):
    return self.getDistanceBetweenPoints(firstPoint, secondPoint) == 1


  def getDistanceBetweenPoints(self, firstPoint, secondPoint):
    dx = secondPoint.x - firstPoint.x
    dy = secondPoint.y - firstPoint.y
    return (abs(dx) + abs(dy) + abs(dx-dy)) / 2


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
      if relativePosition == Hive.NORTHEAST:
        logging.debug('Hive.getRelativePoint: NORTHEAST')
        newPoint = Point(relativePoint.x + 1, relativePoint.y, 0)
      elif relativePosition == Hive.EAST:
        logging.debug('Hive.getRelativePoint: EAST')
        newPoint = Point(relativePoint.x + 1, relativePoint.y + 1, 0)
      elif relativePosition == Hive.SOUTHEAST:
        logging.debug('Hive.getRelativePoint: SOUTHEAST')
        newPoint = Point(relativePoint.x, relativePoint.y + 1, 0)
      elif relativePosition == Hive.SOUTHWEST:
        logging.debug('Hive.getRelativePoint: SOUTHWEST')
        newPoint = Point(relativePoint.x - 1, relativePoint.y, 0)
      elif relativePosition == Hive.WEST:
        logging.debug('Hive.getRelativePoint: WEST')
        newPoint = Point(relativePoint.x - 1, relativePoint.y - 1, 0)
      elif relativePosition == Hive.NORTHWEST:
        logging.debug('Hive.getRelativePoint: NORTHWEST')
        newPoint = Point(relativePoint.x, relativePoint.y - 1, 0)
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
    limits = self.getBoardArrayLimits()
    limits[0] -= 1
    limits[1] -= 1
    limits[2] += 1
    limits[3] += 1

    width = limits[2] - limits[0] + 1
    height = limits[3] - limits[1] + 1
    swidth = 4 * (width) + 1 + 2
    sheight = 2 * (height) + 1

    s = []
    s0 = [' '] * swidth
    s1 = [' '] * swidth
    s2 = [' '] * swidth

    for arry in range(limits[3], limits[1] - 1, -1):
      offsetx = 0 if arry % 2 == 0 else  2
      sx = offsetx + 2
      for arrx in range(limits[0], limits[2] + 1, 1):
        #array to hex
        hexx = arrx - int(math.floor(float(arry)/2))
        hexy = arrx + int(math.ceil(float(arry)/2))

        piece = self.getTopPieceAtPoint(Point(hexx,hexy,0))
        if piece:
          s0[sx-1] = '/'
          s0[sx+1] = '\\'
          s1[sx-2] = '|'
          s1[sx-1] = piece.color
          s1[sx] = piece.kind
          s1[sx+1] = str(piece.number) if piece.number else ' '
          s1[sx+2] = '|'
          s2[sx-1] = '\\'
          s2[sx+1] = '/'
        else:
          s1[sx] = '.'
        sx += 4
      
      s.insert(0, s2)
      s.insert(0, s1)
      s2 = s0
      s0 = [' '] * swidth
      s1 = [' '] * swidth
    s.insert(0,s2)

    for si in s:
      sys.stderr.write('# ' + ''.join(si) + '\n')
    sys.stderr.write('\n')


  def getBoardArrayLimits(self):
    limits = [float('inf'), float('inf'), float('-inf'), float('-inf')] # xmin, ymin, xmax, ymax
    for key, pieces in self.board.iteritems():
      piece = pieces[0]
      arrx = int(math.floor(float(piece.point.x + piece.point.y) / 2))
      arry = piece.point.y - piece.point.x

      limits[0] = min(limits[0], arrx)
      limits[1] = min(limits[1], arry)
      limits[2] = max(limits[2], arrx)
      limits[3] = max(limits[3], arry)

    if limits[0] == float('inf'):
      limits = [0, 0, 0, 0]

    return limits 

