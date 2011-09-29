import logging
import sys
from pieces import *
from zobrist import *
from collections import namedtuple

class Point(namedtuple('Point', ['x', 'y', 'z'])):
  __slots__ = ()

class Move(namedtuple('Move', ['piece', 'startCoorindates', 'endCoordinates'])):
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
    This is a three dimensional board with the pieces initially played at z=0 (where z is left out of the coordinates we assume the piece with max(z)).

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


  def getBoardKey(self, coordinates):
    return str(coordinates[0]) + ',' + str(coordinates[1])


  def getTopPieceAtCoordinates(self, coordinates):
    key = self.getBoardKey(coordinates)
    if self.board.has_key(key):
      return self.board[key][len(self.board[key]) - 1]
    return None


  def getPiecesAtCoordinates(self, coordinates):
    key = self.getBoardKey(coordinates)
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


  def getAdjacentCoordinatesList(self, coordinates):
    return [(coordinates[0], coordinates[1] - 1, 0),      # (x, y-1)    TOPRIGHT
            (coordinates[0] + 1, coordinates[1], 0),      # (x+1, y)    RIGHT
            (coordinates[0] + 1, coordinates[1] + 1, 0),  # (x+1, y+1)  BOTTOMRIGHT
            (coordinates[0], coordinates[1] + 1, 0),      # (x, y+1)    BOTTOMLEFT
            (coordinates[0] - 1, coordinates[1], 0),      # (x-1, y)    LEFT
            (coordinates[0] - 1, coordinates[1] - 1, 0)] # (x-1, y-1)  TOPLEFT


  def areCoordinatesAdjacent(self, firstCoordinates, secondCoordinates):
    for coordinates in self.getAdjacentCoordinatesList(firstCoordinates):
      if coordinates[0] == secondCoordinates[0] and coordinates[1] == secondCoordinates[1]:
        return True

    return False

  def doCoordinatesOnlyBorderColor(self, coordinates, color):
    for coordinates in self.getAdjacentCoordinatesList(coordinates):
      coordinatesKey = self.getBoardKey(coordinates)
      if self.board.has_key(coordinatesKey):
        piece = self.board[coordinatesKey][len(self.board[coordinatesKey]) - 1]
        if not piece.color == color:
          return False

    return True


  def areCoordinatesInGate(self, coordinates):
    """ Coordinates must be bordered on 5+ sides """
    borderCount = 0
    for coordinates in self.getAdjacentCoordinatesList(coordinates):
      piece = self.getTopPieceAtCoordinates(coordinates)
      if piece:
        borderCount += 1

    return borderCount >= 5


  def getBorderCoordinatesList(self, includeGates):
    coordinatesList = []
    uniqueCoordinates = dict()
    
    for key, pieces in self.board.iteritems():
      piece = pieces[len(pieces) - 1]
      for coordinates in self.getAdjacentCoordinatesList(piece.coordinates):
        coordinatesKey = self.getBoardKey(coordinates)
        if not self.board.has_key(coordinatesKey) and not uniqueCoordinates.has_key(coordinatesKey):
          if includeGates or not self.areCoordinatesInGate(coordinates):
            uniqueCoordinates[coordinatesKey] = 1
            coordinatesList.append(coordinates)
    
    return coordinatesList; 


  def getEntryCoordinatesList(self, color):
    coordinatesList = []
    uniqueCoordinates = dict()

    for key, pieces in self.board.iteritems():
      piece = pieces[len(pieces) - 1] 

      adjacentCoordinatesList = self.getAdjacentCoordinatesList(piece.coordinates)
      logging.debug('Hive.getEntryCoordinatesList(' + color + '): piece=' + str(piece))
      logging.debug('Hive.getEntryCoordinatesList(' + color + '): adjacentCoordinatesList=' + str(adjacentCoordinatesList))

      for coordinates in adjacentCoordinatesList:
        coordinatesKey = self.getBoardKey(coordinates)
        if not self.board.has_key(coordinatesKey) and not uniqueCoordinates.has_key(coordinatesKey):
          if self.getNumberOfPieces() == 1 or self.doCoordinatesOnlyBorderColor(coordinates, color):
            uniqueCoordinates[coordinatesKey] = 1
            coordinatesList.append(coordinates)

    if len(coordinatesList) == 0:
      coordinatesList.append((0, 0, 0))

    logging.debug('Hive.getEntryCoordinatesList(' + color + '): coordinatesList=' + str(coordinatesList))

    return coordinatesList; 


  def isBrokenWithoutPiece(self, piece):
    if len(self.board) == 0:
      logging.debug('Hive.isBrokenWithoutPiece: no pieces played')
      return False
  
    visitedPieces = dict()

    self.pickupPiece(piece)

    logging.debug('Hive.isBrokenWithoutPiece: start state, board = ' + str(self.board))

    # get a random piece
    key = self.board.keys()[0]
    rootPiece = self.board[key][len(self.board[key]) - 1]
    for p in self.board[key]: visitedPieces[p.getNotation()] = 1

    # try to visit all pieces in the hive
    self._visitPiece(rootPiece, visitedPieces)

    self.putdownPiece(piece, piece.coordinates)

    logging.debug('Hive.isBrokenWithoutPiece: end state, board = ' + str(self.board))
    logging.debug('Hive.isBrokenWithoutPiece: end state, visitedPieces = ' + str(visitedPieces))
    logging.debug('Hive.isBrokenWithoutPiece: end state, numberOFPieces = ' + str(self.getNumberOfPieces()))

    # if all pieces were vistited the hive is still connected
    return not len(visitedPieces) == self.getNumberOfPieces() - 1


  def _visitPiece(self, piece, visitedPieces):
    logging.debug('Hive.visitPice: visiting = ' + str(piece))

    adjacentCoordinatesList = self.getAdjacentCoordinatesList(piece.coordinates)
    
    for coordinates in adjacentCoordinatesList:
      topPiece = self.getTopPieceAtCoordinates(coordinates)
      if topPiece and not visitedPieces.has_key(topPiece.getNotation()):
        for p in self.getPiecesAtCoordinates(coordinates):
          visitedPieces[p.getNotation()] = 1
        self._visitPiece(topPiece, visitedPieces)


  def getPiece(self, (color, kind, number)):
    for key in self.board.keys():
      for piece in self.board[key]:
        if piece.color == color and piece.kind == kind and str(piece.number) == number:
          return piece
    return None 

  
  def getRelativeCoordinates(self, piece, relativePiece, relativePosition):
    logging.debug('Hive.getRelativeCoordinates: piece=' + str(piece))

    newCoordinates = (0,0,0)
    if relativePiece:
      logging.debug('Hive.getRelativeCoordinates: relativePiece=' + str(relativePiece))
      logging.debug('Hive.getRelativeCoordinates: relativePosition=' + relativePosition)

      relativeCoordinates = relativePiece.coordinates
      if relativePosition == Hive.TOPRIGHT:
        logging.debug('Hive.getRelativeCoordinates: TOPRIGHT')
        newCoordinates = (relativeCoordinates[0], relativeCoordinates[1] - 1, 0)
      elif relativePosition == Hive.RIGHT:
        logging.debug('Hive.getRelativeCoordinates: RIGHT')
        newCoordinates = (relativeCoordinates[0] + 1, relativeCoordinates[1], 0)
      elif relativePosition == Hive.BOTTOMRIGHT:
        logging.debug('Hive.getRelativeCoordinates: BOTTOMRIGHT')
        newCoordinates = (relativeCoordinates[0] + 1, relativeCoordinates[1] + 1, 0)
      elif relativePosition == Hive.BOTTOMLEFT:
        logging.debug('Hive.getRelativeCoordinates: BOTTOMLEFT')
        newCoordinates = (relativeCoordinates[0], relativeCoordinates[1] + 1, 0)
      elif relativePosition == Hive.LEFT:
        logging.debug('Hive.getRelativeCoordinates: LEFT')
        newCoordinates = (relativeCoordinates[0] - 1, relativeCoordinates[1], 0)
      elif relativePosition == Hive.TOPLEFT:
        logging.debug('Hive.getRelativeCoordinates: TOPLEFT')
        newCoordinates = (relativeCoordinates[0] - 1, relativeCoordinates[1] - 1, 0)
      elif relativePosition == Hive.COVER:
        logging.debug('Hive.getRelativeCoordinates: COVER')
        newCoordinates = (relativeCoordinates[0], relativeCoordinates[1], relativeCoordinates[2] + 1)
    return newCoordinates


  def pickupPiece(self, piece):
    key = self.getBoardKey(piece.coordinates)
    if len(self.board[key]) == 1:
      del self.board[key]
    else:
      self.board[key].remove(piece)
    self.zobrist.updateState(piece)


  def putdownPiece(self, piece, coordinates):
    key = self.getBoardKey(coordinates)
    if self.board.has_key(key):
      z = -1
      for p in self.board[key]:
        z = max(p.coordinates[2], z)
      z += 1
      coordinates = (coordinates[0], coordinates[1], z)
      self.board[key].append(piece)
    else:
      self.board[key] = [piece]

    piece.coordinates = coordinates
    self.zobrist.updateState(piece)
  

  def getSurroundedQueenColors(self):
    surrounded = []

    for key, pieces in self.board.iteritems():
      for piece in pieces:
        if piece.kind == 'Q':
          isSurrounded = True
          for coordinates in self.getAdjacentCoordinatesList(piece.coordinates):
            if not self.getTopPieceAtCoordinates(coordinates):
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
      s.append([' '] * (4 * width + 2 * height + 1))

    #logging.debug('Hive.printBoard: s_dims=' + str(len(s[0])) + 'x' + str(len(s)))

    for y in range(limits[1], limits[3] + 2): # height/rows
      absy = y - limits[1]
      sy = 2 * absy + 1 #magic mapping formula
      
      if absy < height: # y-axis
        axisy = 4 * width - 2 * absy + 2 * height
        s[sy][axisy] = str(y)

      for x in range(limits[0], limits[2] + 1): # width/columns
        absx = x - limits[0]
        sx = 4 * absx - 2 * absy + 2 * height #magic mapping formula

        if absy == height: # x-axis
          s[sy][sx] = str(x)
        else:
          key = self.getBoardKey((x, y))
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
        

    sys.stderr.write('   ' + (' ' *  (4 * (width + 2)) + 'y\n'))
    for si in s:
      if s.index(si) == len(s) - 1:
        sys.stderr.write('x   ')
      else:
        sys.stderr.write('    ')
      sys.stderr.write(''.join(si) + '\n')

    sys.stderr.write('\n')


  def getBoardLimits(self):
    limits = [0, 0, 0, 0] # xmin, ymin, xmax, ymax
    for key in self.board.keys():
      for piece in self.board[key]:
        limits[0] = min(limits[0], piece.coordinates[0])
        limits[1] = min(limits[1], piece.coordinates[1])
        limits[2] = max(limits[2], piece.coordinates[0])
        limits[3] = max(limits[3], piece.coordinates[1])
    return limits 

