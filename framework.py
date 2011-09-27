import logging
import os
import random
import re
import argparse
import shlex
import subprocess
import sys
import time
from cmd2 import Cmd

logging.basicConfig(level=logging.DEBUG)


class Piece:
  def __init__(self, color, kind, number):
    self.color = color # w, b
    self.kind = kind # A, B, G, Q, S
    self.number = number # '', 1, 2, 3
    self.coordinates = (None, None, None) # (x,y,z)


  def getNotation(self):
    return self.color + self.kind + str(self.number)#+ ' @ ' + str(self.coordinates)


  def getPbemNotation(self):
    notation = self.kind
    if notation == 'G': notation = 'H'
    if self.color == 'b': notation = notation.lower()
    return notation 


  def getPossibleCoordinatesList(self, hive):
    return []


  def __repr__(self):
    return self.color + self.kind + str(self.number) + ' @ ' + str(self.coordinates)



class QueenBeePiece(Piece):
  """
    The Queen Bee piece. It moves one hex at a time and cannot be surrounded or the player looses.
  """
  def __init__(self, color):
    Piece.__init__(self, color, 'Q', '')


  def getPossibleCoordinatesList(self, hive):
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
    logging.debug('Zobrist.changeSide: state = ' + str(self.currentState))


  def updateState(self, piece):
    key = self._getZobristKey(piece.color, piece.kind, piece.number, piece.coordinates)
    self.currentState = self.currentState ^ key
    logging.debug('Zobrist.updateState: state = ' + str(self.currentState))



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

  def __init__(self):
    self.board = dict()
    self.zobrist = Zobrist()


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
           0123456789012345   y
       sy 0   / \ / \ / \                    
          1  | . | . | . |  0
          2 / \ / \ / \ /  
          3| . | . | .  1
          4 \ / \ /    
           0   1   2  x

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
    s = []
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
          # s[sy][sx] = piece.getPbemNotation()
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
  def __init__(self, whiteBot, blackBot, timeControls, moveList):
    self.whitePlayer = Player('white', whiteBot)
    self.blackPlayer = Player('black', blackBot)
    self.currentPlayer = self.whitePlayer
    self.turnNumber = 1
    self.gameTime = 300000 #ms
    self._readTimeControls(timeControls)
    self.moveList = []
    self._readMoveList(moveList)
    self.hive = Hive()
    self.winner = None

  def makeMove(self, moveString):
    self.validateMoveString(moveString)

    # check if the piece hasn't been played yet, otherwise take if from the board
    pieceAttributes = self.parsePieceAttributes(moveString)
    piece = self.currentPlayer.getPiece(pieceAttributes)
    if not piece:
      raise InputError ("The piece you entered is not valid.")

    # may not move a piece until queen is moved
    if self.currentPlayer.hasPlayed(piece.kind, piece.number) and not self.currentPlayer.hasPlayed('Q'):
      raise MoveError("You must play your Queen Bee before you may move other insects.")

    # queen must be played in a player's first 4 moves
    if self.turnNumber / 2 + 1 == 4 and not self.currentPlayer.hasPlayed('Q') and not piece.kind == 'Q':
      raise MoveError("You must play your Queen Bee in your first 4 turns.")

    # get proposed move coordinates
    relativePiece = None
    relativePosition = None
    relativeAttributes = self.parseRelativeAttributes(moveString)
    if (relativeAttributes):
      relativePiece = self.hive.getPiece(relativeAttributes[0])
      if not relativePiece:
        raise InputError ("The relative piece you entered is not valid.")
      relativePosition = relativeAttributes[1]
    proposedCoordinates = self.hive.getRelativeCoordinates(piece, relativePiece, relativePosition)

    # check if valid move
    if piece.coordinates == (None,None,None): # not on board yet
      logging.debug('Game.makeMove: piece not on board')
      possibleCoordinatesList = self.hive.getEntryCoordinatesList(piece.color)
    elif not piece == self.hive.getTopPieceAtCoordinates(piece.coordinates): # beetle pinned
      logging.debug('Game.makeMove: piece beetle pinned')
      possibleCoordinatesList = []
    elif self.hive.isBrokenWithoutPiece(piece): # if picking up breaks hive: 0 possible coordinates
      logging.debug('Game.makeMove: breaks hive')
      possibleCoordinatesList = []
    else:
      possibleCoordinatesList = piece.getPossibleCoordinatesList(self.hive)

    if not self.isValidMove(proposedCoordinates, possibleCoordinatesList):
      raise MoveError ("The move you entered is not valid.")

    # make the move
    if not piece.coordinates == (None, None, None):
      self.hive.pickupPiece(piece)
    self.hive.putdownPiece(piece, proposedCoordinates)

    self.moveList.append(str(self.turnNumber) + '. ' + moveString)
    self.turnNumber += 1
    self.switchCurrentPlayer()


  def isGameOver(self):
    # check for wins/stalemate (via surrounding)
    surrounded = self.hive.getSurroundedQueenColors()
    logging.debug('Game.isGameOver surrounded = ' + str(surrounded))
    if len(surrounded) > 0:
      if len(surrounded) == 2:
        self.winner = 'draw'
      elif surrounded[0] == 'w':
        self.winner = 'black'
      else:
        self.winner = 'white'
      return True
    
    # check for stalemate (via threefold repetition)
    if self.currentPlayer.hasSeenThreefoldRepetition():
      self.winner = 'draw'
      return True

    return False
    

  def isValidMove(self, proposedCoordinates, possibleCoordinatesList):
    logging.debug('Game.isValidMove: proposedCoordinates=' + str(proposedCoordinates))
    logging.debug('Game.isValidMove: possibleCoordinatesList=' + str(possibleCoordinatesList))

    for coordinates in possibleCoordinatesList:
      if coordinates[0] == proposedCoordinates[0] and coordinates[1] == proposedCoordinates[1] and coordinates[2] == proposedCoordinates[2]:
        return True
    return False


  def validateMoveString(self, moveString):
    """ Basic input string validation (note: this is incomplete doesn't validate invalid stuff like wB3 -bQ2) """
    match = re.match('^[bw][ABGQS][0-3]?(?:\\s[\\\/-]?[bw][ABGQS][0-3]?[\\\/-]?)?$', moveString)
    if not match:
      raise InputError("The move you entered is not valid.")


  def parsePieceAttributes(self, moveString):
    matches = re.search('^(?P<color>b|w)(?P<kind>[ABGQS])(?P<number>[0-3]?)', moveString)
    return (matches.group('color'), matches.group('kind'), matches.group('number'))


  def parseRelativeAttributes(self, moveString):
    matches = re.search(' (?P<lm>[\\\/-]?)(?P<color>b|w)(?P<kind>[ABGQS])(?P<number>[0-3]?)(?P<rm>[\\\/-]?)$', moveString)
    if matches:
      position = (matches.group('lm') if matches.group('lm') != '' else ' ') + (matches.group('rm') if matches.group('rm') != '' else ' ')
      return ((matches.group('color'), matches.group('kind'), matches.group('number')), position)
    return None


  def switchCurrentPlayer(self):
    if self.currentPlayer == self.whitePlayer:
      self.currentPlayer = self.blackPlayer
    else:
      self.currentPlayer = self.whitePlayer
    self.hive.zobrist.changeSide()
    self.currentPlayer.addHiveState(self.hive.zobrist.currentState)


  def _readMoveList(self, moveListCsv):
    moveList = moveListCsv.split(', ')
    for move in moveList:
      if not move == '':
        move = re.sub('^[0-9]+. ', '', move)
        self.makeMove(move)

  def getMoveListCsv(self):
    return ','.join(map(str, self.moveList))


  def _readTimeControls(self, timeControlsCsv):
    timeControls = timeControlsCsv.split(',')
    self.gameTime = timeControls[0]
    self.whitePlayer.timeUsed = timeControls[1]
    self.blackPlayer.timeUsed = timeControls[2]

  def getTimeControlsCsv(self):
    return str(self.gameTime) + ',' + str(self.whitePlayer.timeUsed) + ',' + str(self.blackPlayer.timeUsed)
   

  def printBoard(self):
    self.hive.printBoard()



class InputError(Exception):
  def __init__(self, value):
      self.value = value
  def __str__(self):
      return repr(self.value)



class MoveError(Exception):
  def __init__(self, value):
      self.value = value
  def __str__(self):
      return repr(self.value)



class Framework():
  def __init__(self, args):
    self.args = self._parseArgs(args)

  def _parseArgs(self, args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--white')
    parser.add_argument('--black')
    parser.add_argument('--times', default='30000,0,0')
    parser.add_argument('--moves', default='')
    args = parser.parse_args(args.split())
    args = vars(args)
    logging.debug('Framework._parseArgs: args = ' + str(args))
    return args

  def run(self):
    self.args['white'] = self.readBot('white', self.args['white'])
    self.args['black'] = self.readBot('black', self.args['black'])
    self.game = Game(self.args['white'], self.args['black'], self.args['times'], self.args['moves'])

    while not self.game.isGameOver():
      moveString = self.readMove()
      if moveString == 'quit' or moveString == 'exit':
        break
      try:
        print self.game.currentPlayer.color.capitalize() + ' plays ' + moveString
        self.game.makeMove(moveString)
      except InputError as e:
        print e.value
        if self.game.currentPlayer.bot: break;
      except MoveError as e:
        print e.value
        if self.game.currentPlayer.bot: break;
      else:
        self.game.printBoard()


  def readBot(self, color, bot=''):
    while True:
      if not bot:
        bot = raw_input(color.capitalize() + " player bot (blank for human): ")
      else:
        print color.capitalize() + " player bot (blank for human): " + bot

      if bot == '':
        return None
      elif os.path.exists(bot):
        return bot
      else:
        print "Couldn't locate the bot. Try again."
        bot = None
    return None


  def readMove(self): 
    moveString = 'error'
    if self.game.currentPlayer.bot:
      try:
        commandLine = self.game.currentPlayer.bot + '--times="' + self.game.getTimeControlsCsv() + '" --moves="' + self.game.getMovesListCsv() + '"'
        args = shlex.split(commandLine)
        startTime = time()
        botProcess = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=None)
        moveString = botProcess.communicate()[0]
        endTime = time()
        totalTime = endTime - startTime()
        self.game.currentPlayer.timeUsed += totalTime
        logging.debug('Framework.readMove bottime = ' + str (totalTime))
      except OSError as details:
        logging.debug('Framework.readMOve OSError = ' + str(details))
        raise InputError(player.bot + ' process failed to execute')
    else:
      moveString = raw_input(self.game.currentPlayer.color.capitalize() + "'s turn: ")

    return moveString



class HiveCmd(Cmd):
  """ Hive Bot Framework """
  prompt = 'hive> '
  intro = 'Hive Bot Framework\n------------------'

  def do_game(self, args = ''):
    Framework(args).run()


if __name__ == "__main__": 
  HiveCmd().cmdloop() 

