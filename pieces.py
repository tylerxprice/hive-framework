from collections import namedtuple

class Point(namedtuple('Point', ['x', 'y', 'z'])):
  NONE = (None, None, None)
  __slots__ = ()

class Piece:
  (COLORSTRING, KINDSTRING) = ('wb', 'ABGQSML')

  def __init__(self, color, kind, number):
    self.color = color # w, b
    self.kind = kind # A, B, G, Q, S
    self.number = number # '', 1, 2, 3
    self.point = Point.NONE # (x,y,z)


  def getColorIndex(self):
    return Piece.COLORSTRING.index(self.color)


  def getKindIndex(self):
    return Piece.KINDSTRING.index(self.kind)


  def getNotation(self):
    return self.color + self.kind + str(self.number)


  def isPlayed(self):
    return not self.point == Point.NONE


  def getPossiblePoints(self, hive):
    if not self.isPlayed():
      return hive.getEntryPoints(self.color)
    elif not self == hive.getTopPieceAtPoint(self.point): # beetle pinned
      return []
    elif hive.isBrokenWithoutPiece(self): # if picking up breaks hive: 0 possible points
      return []

    return None


  def isPinned(self, hive):
    if not self.isPlayed():
      return False

    if not self == hive.getTopPieceAtPoint(self.point): # beetle pinned
      return True 
    elif hive.isBrokenWithoutPiece(self): # if picking up breaks hive: 0 possible points
      return True 

    return False


  def __repr__(self):
    return self.color + self.kind + `self.number` + ' @ ' + str(self.point)



class QueenBeePiece(Piece):
  """
    The Queen Bee piece. It moves one hex at a time and cannot be surrounded or the player looses.
  """
  def __init__(self, color, number = ''):
    Piece.__init__(self, color, 'Q', number)


  def getPossiblePoints(self, hive):
    possiblePoints = Piece.getPossiblePoints(self, hive)
    if not possiblePoints == None:
      return possiblePoints

    # can move 1 empty hex away, but cannot enter gates
    possiblePoints = []

    # can't move if pinned (needs 2 adjacent points to move through)
    if not hive.hasTwoEmptyAdjacentPoints(self.point):
      return possiblePoints 
    
    hive.pickupPiece(self)

    adjacentPoints = hive.getAdjacentPoints(self.point)

    # partition adjacent points into occupied and slideable
    occupiedAdjacentPoints = []
    slideableAdjacentPoints = []
    for index, adjacentPoint in enumerate(adjacentPoints):
      if hive.getTopPieceAtPoint(adjacentPoint):
        occupiedAdjacentPoints.append(adjacentPoint)
      else:
        easterPoint = hive.getAdjacentPoint(self.point, ((index - 1) % 6))
        westerPoint = hive.getAdjacentPoint(self.point, ((index + 1) % 6))
        if not hive.getTopPieceAtPoint(easterPoint) or not hive.getTopPieceAtPoint(westerPoint):
          slideableAdjacentPoints.append(adjacentPoint)

    # check slideable adjacencies for valid moves (must be adjacent to one of the occupied adjacencies)
    for slidableAdjacentPoint in slideableAdjacentPoints:
      for occupiedAdjacentPoint in occupiedAdjacentPoints:
        if hive.arePointsAdjacent(slidableAdjacentPoint, occupiedAdjacentPoint):
          possiblePoints.append(slidableAdjacentPoint)
          break
    
    hive.putdownPiece(self, self.point)

    return possiblePoints

  def isPinned(self, hive):
    return Piece.isPinned(self, hive) and not hive.hasTwoEmptyAdjacentPoints(self.point)


class SpiderPiece(Piece):
  """
    The Spider piece. It moves exactly three hexes at a time.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'S', number)


  def getPossiblePoints(self, hive):
    possiblePoints = Piece.getPossiblePoints(self, hive)
    if not possiblePoints == None:
      return possiblePoints

    # can move 3 emtpy hex away, but cannot enter gates and cannot backtrack
    possiblePoints = []

    # can't move if pinned (needs 2 adjacent points to move through)
    if not hive.hasTwoEmptyAdjacentPoints(self.point):
      return possiblePoints 

    # find all 3 node segments in the graph that is the non-gate border nodes starting at the current node
    hive.pickupPiece(self)
    self._visitPoint(self.point, 0, [], possiblePoints, hive)
    hive.putdownPiece(self, self.point)

    return possiblePoints


  def _visitPoint(self, point, depth, currentPath, possiblePoints, hive):
    if depth == 3:
      if not point in possiblePoints:
        possiblePoints.append(point)
        return

    currentPath.append(point)

    # get adjacencies
    adjacentPoints = hive.getAdjacentPoints(point)

    # partition into occupied and slideable
    occupiedAdjacentPoints = []
    slideableAdjacentPoints = []
    for index, adjacentPoint in enumerate(adjacentPoints):
      if hive.getTopPieceAtPoint(adjacentPoint):
        occupiedAdjacentPoints.append(adjacentPoint)
      else:
        easterPoint = hive.getAdjacentPoint(point, ((index - 1) % 6))
        westerPoint = hive.getAdjacentPoint(point, ((index + 1) % 6))
        if not hive.getTopPieceAtPoint(easterPoint) or not hive.getTopPieceAtPoint(westerPoint):
          slideableAdjacentPoints.append(adjacentPoint)
    
    for slidableAdjacentPoint in slideableAdjacentPoints:
      for occupiedAdjacentPoint in occupiedAdjacentPoints:
        if not slidableAdjacentPoint in currentPath and hive.arePointsAdjacent(slidableAdjacentPoint, occupiedAdjacentPoint):
          self._visitPoint(slidableAdjacentPoint, depth + 1, currentPath, possiblePoints, hive)
          break

    currentPath.pop()

  def isPinned(self, hive):
    return Piece.isPinned(self, hive) and not hive.hasTwoEmptyAdjacentPoints(self.point)


class BeetlePiece(Piece):
  """
    The Beetle piece. It moves exactly one hexes at a time, but can cover other pieces.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'B', number)


  def getPossiblePoints(self, hive):
    possiblePoints = Piece.getPossiblePoints(self, hive)
    if not possiblePoints == None:
      return possiblePoints

    possiblePoints = []

    # partition adjacencies into climbable (up or down) and slideable
    adjacentPoints = hive.getAdjacentPoints(self.point)
    climbableAdjacentPoints = []
    slideableAdjacentPoints = []
    
    if self.point.z > 0 and self == hive.getTopPieceAtPoint(self.point): # beetle on top: can possibly climb onto any adjacent hex
      climbableAdjacentPoints = adjacentPoints
    else: # beetle on ground: can move 1 hex away (occupied or not), but cannot enter gates
      for index, adjacentPoint in enumerate(adjacentPoints):
        if hive.getTopPieceAtPoint(adjacentPoint):
          climbableAdjacentPoints.append(adjacentPoint)
        else:
          easterPoint = hive.getAdjacentPoint(self.point, ((index - 1) % 6))
          westerPoint = hive.getAdjacentPoint(self.point, ((index + 1) % 6))
          if not hive.getTopPieceAtPoint(easterPoint) or not hive.getTopPieceAtPoint(westerPoint):
            slideableAdjacentPoints.append(adjacentPoint)


    hive.pickupPiece(self)

    # queen style move on ground 
    for slidableAdjacentPoint in slideableAdjacentPoints:
      for climbableAdjacentPoint in climbableAdjacentPoints:
        if hive.arePointsAdjacent(slidableAdjacentPoint, climbableAdjacentPoint):
          possiblePoints.append(slidableAdjacentPoint)
          break

    # climbing style move (can't climb through gates)
    for adjacentPoint in climbableAdjacentPoints:
      index = hive.getAdjacencyIndex(self.point, adjacentPoint)
      adjacentPiece = hive.getTopPieceAtPoint(adjacentPoint)
      adjacentHeight = -1
      if adjacentPiece:
        adjacentHeight = adjacentPiece.point.z
      easterPoint = hive.getAdjacentPoint(self.point, ((index - 1) % 6))
      easterPiece = hive.getTopPieceAtPoint(easterPoint)
      westerPoint = hive.getAdjacentPoint(self.point, ((index + 1) % 6))
      westerPiece = hive.getTopPieceAtPoint(westerPoint)
      minSideHeight = float('inf')
      if easterPiece: 
        minSideHeight = min(minSideHeight, easterPiece.point.z)
      if westerPiece: 
        minSideHeight = min(minSideHeight, westerPiece.point.z)
      if minSideHeight == float('inf') or minSideHeight <= self.point.z or minSideHeight < adjacentHeight:
        possiblePoints.append(adjacentPoint)

    hive.putdownPiece(self, self.point)

    return possiblePoints


class AntPiece(Piece):
  """
    The Ant piece. It moves anywhere on the outside of the hive.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'A', number)

  def getPossiblePoints(self, hive):
    possiblePoints = Piece.getPossiblePoints(self, hive)
    if not possiblePoints == None:
      return possiblePoints

    # can move to any non-gate hex around hive
    possiblePoints = []

    hive.pickupPiece(self)
    self._visitPoint(self.point, possiblePoints, hive, 1)
    possiblePoints.remove(self.point)
    hive.putdownPiece(self, self.point)

    return possiblePoints

  def _visitPoint(self, point, possiblePoints, hive):
    possiblePoints.append(point)
    adjacentPoints = hive.getAdjacentPoints(point)

    # partition into occupied and slideable
    occupiedAdjacentPoints = []
    slideableAdjacentPoints = []
    for index, adjacentPoint in enumerate(adjacentPoints):
      if hive.getTopPieceAtPoint(adjacentPoint):
        occupiedAdjacentPoints.append(adjacentPoint)
      else:
        easterPoint = hive.getAdjacentPoint(point, ((index - 1) % 6))
        westerPoint = hive.getAdjacentPoint(point, ((index + 1) % 6))
        easterPiece = hive.getTopPieceAtPoint(easterPoint)
        westerPiece = hive.getTopPieceAtPoint(westerPoint)
        if not hive.getTopPieceAtPoint(easterPoint) or not hive.getTopPieceAtPoint(westerPoint):
          slideableAdjacentPoints.append(adjacentPoint)

    for slidableAdjacentPoint in slideableAdjacentPoints:
      for occupiedAdjacentPoint in occupiedAdjacentPoints:
        if hive.arePointsAdjacent(slidableAdjacentPoint, occupiedAdjacentPoint) and not slidableAdjacentPoint in possiblePoints: 
          self._visitPoint(slidableAdjacentPoint, possiblePoints, hive)
          break


  def isPinned(self, hive):
    return Piece.isPinned(self, hive) and not hive.hasTwoEmptyAdjacentPoints(self.point)


class GrasshopperPiece(Piece):
  """
    The Grasshopper piece. It moves in a straight line over other pieces.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'G', number)


  def getPossiblePoints(self, hive):
    possiblePoints = Piece.getPossiblePoints(self, hive)
    if not possiblePoints == None:
      return possiblePoints

    # can move in straight lines from current hex, but must stop at first space 
    # in each direction, starting one occupied space over, find first borderPoint
    possiblePoints = []

    #(x+1, y) NORTHEAST
    point = Point(self.point.x + 1, self.point.y, 0)
    piece = hive.getTopPieceAtPoint(point)
    if piece:
      while True:
        point = Point(point.x + 1, point.y, 0)
        if not hive.getTopPieceAtPoint(point):
          possiblePoints.append(point)
          break

    #(x+1, y+1) EAST
    point = Point(self.point.x + 1, self.point.y + 1, 0)
    piece = hive.getTopPieceAtPoint(point)
    if piece:
      while True:
        point = Point(point.x + 1, point.y + 1, 0)
        if not hive.getTopPieceAtPoint(point):
          possiblePoints.append(point)
          break

    #(x, y+1) SOUTHEAST
    point = Point(self.point.x, self.point.y + 1, 0)
    piece = hive.getTopPieceAtPoint(point)
    if piece:
      while True:
        point = Point(point.x, point.y + 1, 0)
        if not hive.getTopPieceAtPoint(point):
          possiblePoints.append(point)
          break

    #(x-1, y) SOUTHWEST
    point = Point(self.point.x - 1, self.point.y, 0)
    piece = hive.getTopPieceAtPoint(point)
    if piece:
      while True:
        point = Point(point.x - 1, point.y, 0)
        if not hive.getTopPieceAtPoint(point):
          possiblePoints.append(point)
          break

    #(x-1, y-1) WEST
    point = Point(self.point.x - 1, self.point.y - 1, 0)
    piece = hive.getTopPieceAtPoint(point)
    if piece:
      while True:
        point = Point(point.x - 1, point.y - 1, 0)
        if not hive.getTopPieceAtPoint(point):
          possiblePoints.append(point)
          break

    #(x, y-1) NORTHWEST
    point = Point(self.point.x, self.point.y - 1, 0)
    piece = hive.getTopPieceAtPoint(point)
    if piece:
      while True:
        point = Point(point.x, point.y - 1, 0)
        if not hive.getTopPieceAtPoint(point):
          possiblePoints.append(point)
          break

    return possiblePoints


  
class LadybugPiece(Piece):
  """
    The Ladybug piece. It moves 2 hexes ontop of the hive and then one hex to get off the hive.
  """
  def __init__(self, color, number = ''):
    Piece.__init__(self, color, 'L', number)


  def getPossiblePoints(self, hive):
    possiblePoints = Piece.getPossiblePoints(self, hive)
    if not possiblePoints == None:
      return possiblePoints

    possiblePoints = []

    hive.pickupPiece(self)
    self._visitPoint(self.point, 0, [], possiblePoints, hive)
    hive.putdownPiece(self, self.point)

    return possiblePoints


  def _visitPoint(self, point, depth, currentPath, possiblePoints, hive):
    if depth == 3:
      if not point in possiblePoints:
        possiblePoints.append(point)
        return

    currentPath.append(point)

    pieceHeight = -1
    piece = hive.getTopPieceAtPoint(point)
    if piece:
      pieceHeight = piece.point.z
    
    for index, adjacentPoint in enumerate(hive.getAdjacentPoints(point)):
      if not adjacentPoint in currentPath:
        adjacentPiece = hive.getTopPieceAtPoint(adjacentPoint)
        adjacentHeight = -1
        if adjacentPiece:
          adjcentHeight = adjacentPiece.point.z

        easterPoint = hive.getAdjacentPoint(point, ((index - 1) % 6))
        easterPiece = hive.getTopPieceAtPoint(easterPoint)
        westerPoint = hive.getAdjacentPoint(point, ((index + 1) % 6))
        westerPiece = hive.getTopPieceAtPoint(westerPoint)
        minSideHeight = float('inf')
        if easterPiece: 
          minSideHeight = min(minSideHeight, easterPiece.point.z)
        if westerPiece: 
          minSideHeight = min(minSideHeight, westerPiece.point.z)

        if minSideHeight == float('inf') or minSideHeight <= pieceHeight or minSideHeight < adjacentHeight:
          if depth in (0,1) and adjacentPiece:
              self._visitPoint(adjacentPoint, depth + 1, currentPath, possiblePoints, hive)
          elif depth == 2 and not adjacentPiece:
            self._visitPoint(adjacentPoint, depth + 1, currentPath, possiblePoints, hive)

    currentPath.pop()


class MosquitoPiece(QueenBeePiece, SpiderPiece, BeetlePiece, AntPiece, GrasshopperPiece, LadybugPiece, Piece):
  """
    The Mosquito piece. It moves like any of the piece types that it is adjacent to (unless it is beetling on top of the hive)
  """
  def __init__(self, color, number = ''):
    Piece.__init__(self, color, 'M', number)


  def getPossiblePoints(self, hive):
    possiblePoints = Piece.getPossiblePoints(self, hive)
    if not possiblePoints == None:
      return possiblePoints

    possiblePoints = []

    if self.point.z > 0 and self == hive.getTopPieceAtPoint(self.point): # on top: can only move as beetle
      possiblePoints = BeetlePiece.getPossiblePoints(self, hive)
    else:
      for adjacentPoint in hive.getAdjacentPoints(point):
        piece = hive.getTopPieceAtPoint(adjacentPoint)
        if piece:
          kindPossiblePoints = piece.__class__.getPossiblePoints(self, hive)
          possiblePoints = possiblePoints + filter(lambda x:x not in possiblePoints, kindPossiblePoints)

    return possiblePoints

