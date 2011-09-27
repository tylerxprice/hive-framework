import logging

class Piece:
  (COLORSTRING, KINDSTRING) = ('wb', 'ABGQS')

  def __init__(self, color, kind, number):
    self.color = color # w, b
    self.kind = kind # A, B, G, Q, S
    self.number = number # '', 1, 2, 3
    self.coordinates = (None, None, None) # (x,y,z)


  def getColorIndex(self):
    return Piece.COLORSTRING.index(self.color)


  def getKindIndex(self):
    return Piece.KINDSTRING.index(self.kind)


  def getNotation(self):
    return self.color + self.kind + str(self.number)#+ ' @ ' + str(self.coordinates)


  def getPossibleCoordinatesList(self, hive):
    if self.coordinates == (None,None,None): # not on board yet
      logging.debug('Piece.getPossibleCoordinatesList: piece not on board')
      return hive.getEntryCoordinatesList(self.color)
    elif not self == hive.getTopPieceAtCoordinates(self.coordinates): # beetle pinned
      logging.debug('Piece.getPossibleCoordinatesList: piece beetle pinned')
      return []
    elif hive.isBrokenWithoutPiece(self): # if picking up breaks hive: 0 possible coordinates
      logging.debug('Piece.getPossibleCoordinatesList: breaks hive')
      return []

    return None


  def __repr__(self):
    return self.color + self.kind + str(self.number) + ' @ ' + str(self.coordinates)



class QueenBeePiece(Piece):
  """
    The Queen Bee piece. It moves one hex at a time and cannot be surrounded or the player looses.
  """
  def __init__(self, color):
    Piece.__init__(self, color, 'Q', '')


  def getPossibleCoordinatesList(self, hive):
    possibleCoordinatesList = Piece.getPossibleCoordinatesList(self, hive)
    if not possibleCoordinatesList == None:
      return possibleCoordinatesList

    # can move 1 empty hex away, but cannot enter gates
    possibleCoordinatesList = []
    
    # get adjacencies
    adjacentCoordinatesList = hive.getAdjacentCoordinatesList(self.coordinates)

    # partition into occupied and free (exclude gates)
    occupiedAdjacentCoordinatesList = []
    freeAdjacentCoordinatesList = []
    for adjacentCoordinates in adjacentCoordinatesList:
      if hive.getTopPieceAtCoordinates(adjacentCoordinates):
        occupiedAdjacentCoordinatesList.append(adjacentCoordinates)
      elif not hive.areCoordinatesInGate(adjacentCoordinates):
        freeAdjacentCoordinatesList.append(adjacentCoordinates)

    # check free adjacencies for valid moves (must be adjacent to one of the occupied adjacencies)
    for freeAdjacentCoordinates in freeAdjacentCoordinatesList:
      for occupiedAdjacentCoordinates in occupiedAdjacentCoordinatesList:
        if hive.areCoordinatesAdjacent(freeAdjacentCoordinates, occupiedAdjacentCoordinates):
          possibleCoordinatesList.append(freeAdjacentCoordinates)
          break

    return possibleCoordinatesList



class SpiderPiece(Piece):
  """
    The Spider piece. It moves exactly three hexes at a time.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'S', number)


  def getPossibleCoordinatesList(self, hive):
    possibleCoordinatesList = Piece.getPossibleCoordinatesList(self, hive)
    if not possibleCoordinatesList == None:
      return possibleCoordinatesList

    # can move 3 emtpy hex away, but cannot enter gates and cannot backtrack
    possibleCoordinatesList = []

    # find all 3 node segments in the graph that is the non-gate border nodes starting at the current node
    hive.pickupPiece(self)
    self._visitCoordinate(self.coordinates, 0, [], possibleCoordinatesList, hive)
    hive.putdownPiece(self, self.coordinates)

    return possibleCoordinatesList


  def _visitCoordinate(self, coordinates, depth, currentPath, possibleCoordinatesList, hive):
    if depth == 3:
      if not coordinates in possibleCoordinatesList:
        possibleCoordinatesList.append(coordinates)
        return

    currentPath.append(coordinates)

    # get adjacencies
    adjacentCoordinatesList = hive.getAdjacentCoordinatesList(coordinates)

    # partition into occupied and free (exclude) gates
    occupiedAdjacentCoordinatesList = []
    freeAdjacentCoordinatesList = []
    for adjacentCoordinates in adjacentCoordinatesList:
      if hive.getTopPieceAtCoordinates(adjacentCoordinates):
        occupiedAdjacentCoordinatesList.append(adjacentCoordinates)
      elif not hive.areCoordinatesInGate(adjacentCoordinates):
        freeAdjacentCoordinatesList.append(adjacentCoordinates)
    
    for freeAdjacentCoordinates in freeAdjacentCoordinatesList:
      for occupiedAdjacentCoordinates in occupiedAdjacentCoordinatesList:
        if not freeAdjacentCoordinates in currentPath and hive.areCoordinatesAdjacent(freeAdjacentCoordinates, occupiedAdjacentCoordinates):
          self._visitCoordinate(freeAdjacentCoordinates, depth + 1, currentPath, possibleCoordinatesList, hive)
          break



class BeetlePiece(Piece):
  """
    The Beetle piece. It moves exactly one hexes at a time, but can cover other pieces.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'B', number)


  def getPossibleCoordinatesList(self, hive):
    possibleCoordinatesList = Piece.getPossibleCoordinatesList(self, hive)
    if not possibleCoordinatesList == None:
      return possibleCoordinatesList

    possibleCoordinatesList = []

    if self == hive.getTopPieceAtCoordinates(self.coordinates): # beetle on top: can move to any adjacent hex
      possibleCoordinatesList = hive.getAdjacentCoordinatesList(self.coordinates)
    else: # beetle on ground: can move 1 hex away (occupied or not), but cannot enter gates
      # get adjacencies
      adjacentCoordinatesList = hive.getAdjacentCoordinatesList(self.coordinates)

      # partition into occupied and free (exclude) gates
      occupiedAdjacentCoordinatesList = []
      freeAdjacentCoordinatesList = []
      for adjacentCoordinates in adjacentCoordinatesList:
        if hive.getTopPieceAtCoordinates(adjacentCoordinates):
          occupiedAdjacentCoordinatesList.append(adjacentCoordinates)
        elif not hive.areCoordinatesInGate(adjacentCoordinates):
          freeAdjacentCoordinatesList.append(adjacentCoordinates)

      # check free adjacencies for valid moves (must be adjacent to one of the occupied adjacencies)
      for freeAdjacentCoordinates in freeAdjacentCoordinatesList:
        for occupiedAdjacentCoordinates in occupiedAdjacentCoordinatesList:
          if hive.areCoordinatesAdjacent(freeAdjacentCoordinates, occupiedAdjacentCoordinates):
            possibleCoordinatesList.append(freeAdjacentCoordinates)
            break

      # can also move on to occupied adjacent hexes
      possibleCoordinatesList.extend(occupiedAdjacentCoordinatesList)

    return possibleCoordinatesList


class AntPiece(Piece):
  """
    The Ant piece. It moves anywhere on the outside of the hive.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'A', number)

  def getPossibleCoordinatesList(self, hive):
    possibleCoordinatesList = Piece.getPossibleCoordinatesList(self, hive)
    if not possibleCoordinatesList == None:
      return possibleCoordinatesList

    # can move to any non-gate hex around hive
    hive.pickupPiece(self)
    possibleCoordinatesList = hive.getBorderCoordinatesList(False) # False = exclude gates
    possibleCoordinatesList.remove(self.coordinates)
    hive.putdownPiece(self, self.coordinates)

    return possibleCoordinatesList


class GrasshopperPiece(Piece):
  """
    The Grasshopper piece. It moves in a straight line over other pieces.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'G', number)


  def getPossibleCoordinatesList(self, hive):
    possibleCoordinatesList = Piece.getPossibleCoordinatesList(self, hive)
    if not possibleCoordinatesList == None:
      return possibleCoordinatesList

    # can move in straight lines from current hex, but must stop at first space 
    # in each direction, starting one occupied space over, find first borderCoordinates
    possibleCoordinatesList = []

    #(x, y-1) TOPRIGHT
    coordinates = (self.coordinates[0], self.coordinates[1] - 1, 0)
    piece = hive.getTopPieceAtCoordinates(coordinates)
    if piece:
      while True:
        coordinates = (coordinates[0], coordinates[1] - 1, 0)
        if not hive.getTopPieceAtCoordinates(coordinates):
          possibleCoordinatesList.append(coordinates)
          break

    #(x+1, y) RIGHT
    coordinates = (self.coordinates[0] + 1, self.coordinates[1], 0)
    piece = hive.getTopPieceAtCoordinates(coordinates)
    if piece:
      while True:
        coordinates = (coordinates[0] + 1, coordinates[1], 0)
        if not hive.getTopPieceAtCoordinates(coordinates):
          possibleCoordinatesList.append(coordinates)
          break

    #(x+1, y+1) BOTTOMRIGHT
    coordinates = (self.coordinates[0] + 1, self.coordinates[1] + 1, 0)
    piece = hive.getTopPieceAtCoordinates(coordinates)
    if piece:
      while True:
        coordinates = (coordinates[0] + 1, coordinates[1] + 1, 0)
        if not hive.getTopPieceAtCoordinates(coordinates):
          possibleCoordinatesList.append(coordinates)
          break

    #(x, y+1) BOTTOMLEFT
    coordinates = (self.coordinates[0], self.coordinates[1] + 1, 0)
    piece = hive.getTopPieceAtCoordinates(coordinates)
    if piece:
      while True:
        coordinates = (coordinates[0], coordinates[1] + 1, 0)
        if not hive.getTopPieceAtCoordinates(coordinates):
          possibleCoordinatesList.append(coordinates)
          break

    #(x-1, y) LEFT
    coordinates = (self.coordinates[0] - 1, self.coordinates[1], 0)
    piece = hive.getTopPieceAtCoordinates(coordinates)
    if piece:
      while True:
        coordinates = (coordinates[0] - 1, coordinates[1], 0)
        if not hive.getTopPieceAtCoordinates(coordinates):
          possibleCoordinatesList.append(coordinates)
          break

    #(x-1, y-1) TOPLEFT
    coordinates = (self.coordinates[0] - 1, self.coordinates[1] - 1, 0)
    piece = hive.getTopPieceAtCoordinates(coordinates)
    if piece:
      while True:
        coordinates = (coordinates[0] - 1, coordinates[1] - 1, 0)
        if not hive.getTopPieceAtCoordinates(coordinates):
          possibleCoordinatesList.append(coordinates)
          break

    return possibleCoordinatesList
