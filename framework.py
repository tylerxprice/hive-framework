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

  def getPossibleCoordinatesList(self, hive):
    # not on board yet
    if self.coordinates == (None,None,None):
      logging.debug('Piece.getPossibleCoordinatesList: not on board')
      return hive.getEntryCoordinatesList(self.color)

    # if picking up breaks hive: 0 possible coordinates
    if hive.isBrokenWithoutPiece(self):
      logging.debug('Piece.getPossibleCoordinatesList: breaks hive')
      return []

    # can move 1 hex from current coordinates, but cannot enter gates
    possibleCoordinatesList = []
    borderCoordinatesList = hive.getBorderCoordinatesList(False) # False = exclude gates
    for borderCoordinates in borderCoordinatesList:
      if hive.areCoordinatesAdjacent(self.coordinates, borderCoordinates):
        possibleCoordinatesList.append(borderCoordinates)

    return possibleCoordinatesList


class SpiderPiece(Piece):
  """
    The Spider piece. It moves exactly three hexes at a time.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'S', number)

  def getPossibleCoordinatesList(self, hive):
    # not on board yet
    if self.coordinates == (None,None,None):
      logging.debug('Piece.getPossibleCoordinatesList: not on board')
      return hive.getEntryCoordinatesList(self.color)

    # if picking up breaks hive: 0 possible coordinates
    if hive.isBrokenWithoutPiece(self):
      logging.debug('Piece.getPossibleCoordinatesList: breaks hive')
      return []

    # TODO IMPLEMENT
    # can move 1 hex from current coordinates, but cannot enter gates
    possibleCoordinatesList = []
    borderCoordinatesList = hive.getBorderCoordinatesList(False) # False = exclude gates
    for borderCoordinates in borderCoordinatesList:
      if hive.areCoordinatesAdjacent(self.coordinates, borderCoordinates):
        possibleCoordinatesList.append(borderCoordinates)

    return possibleCoordinatesList

class BeetlePiece(Piece):
  """
    The Beetle piece. It moves exactly one hexes at a time, but can cover other pieces.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'B', number)

  def getPossibleCoordinatesList(self, hive):
    # not on board yet
    if self.coordinates == (None,None,None):
      logging.debug('Piece.getPossibleCoordinatesList: not on board')
      return hive.getEntryCoordinatesList(self.color)

    # if picking up breaks hive: 0 possible coordinates
    if hive.isBrokenWithoutPiece(self):
      logging.debug('Piece.getPossibleCoordinatesList: breaks hive')
      return []

    # TODO IMPLEMENT
    # can move 1 hex from current coordinates, but cannot enter gates
    possibleCoordinatesList = []
    borderCoordinatesList = hive.getBorderCoordinatesList(False) # False = exclude gates
    for borderCoordinates in borderCoordinatesList:
      if hive.areCoordinatesAdjacent(self.coordinates, borderCoordinates):
        possibleCoordinatesList.append(borderCoordinates)

    return possibleCoordinatesList

class AntPiece(Piece):
  """
    The Ant piece. It moves anywhere on the outside of the hive.
  """
  def __init__(self, color, number):
    Piece.__init__(self, color, 'A', number)

  def getPossibleCoordinatesList(self, hive):
    # not on board yet
    if self.coordinates == (None,None,None):
      logging.debug('Piece.getPossibleCoordinatesList: not on board')
      return hive.getEntryCoordinatesList(self.color)

    # if picking up breaks hive: 0 possible coordinates
    if hive.isBrokenWithoutPiece(self):
      logging.debug('Piece.getPossibleCoordinatesList: breaks hive')
      return []

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
    # not on board yet
    if self.coordinates == (None,None,None):
      logging.debug('Piece.getPossibleCoordinatesList: not on board')
      return hive.getEntryCoordinatesList(self.color)

    # if picking up breaks hive: 0 possible coordinates
    if hive.isBrokenWithoutPiece(self):
      logging.debug('Piece.getPossibleCoordinatesList: breaks hive')
      return []

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
  def __init__(self, color):
    self.pieces = dict()
    self.setupStartingPieces(color[0])
    self.color = color

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

  def pickupPiece(self, (color, kind, number)):
    key = kind + number
    piece = None
    if self.pieces.has_key(key):
      piece = self.pieces[key]
      del self.pieces[key]
      logging.debug("Pile.pickupPiece: " + str(piece))
    return piece

  def putdownPiece(self, piece):
    key = piece.kind + piece.number
    self.pieces[key] = piece

  def hasPlayed(self, kind, number = ''):
    key = kind + number
    return not self.pieces.has_key(key)


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
  This is a three dimensional board with the pieces initially played at z=0 (where z is left out of the coordinates we assume the piece with max(z)).

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

    self.visitPiece(rootPiece, visitedPieces)

    self.putdownPiece(piece, piece.coordinates)

    logging.debug('Hive.isBrokenWithoutPiece: end state, board = ' + str(self.board))
    logging.debug('Hive.isBrokenWithoutPiece: end state, visitedPieces = ' + str(visitedPieces))
    logging.debug('Hive.isBrokenWithoutPiece: end state, numberOFPieces = ' + str(self.getNumberOfPieces()))

    # if all pieces were vistited the hive is still connected
    return not len(visitedPieces) == self.getNumberOfPieces() - 1

  def visitPiece(self, piece, visitedPieces):
    logging.debug('Hive.visitPice: visiting = ' + str(piece))

    adjacentCoordinatesList = self.getAdjacentCoordinatesList(piece.coordinates)
    
    for coordinates in adjacentCoordinatesList:
      topPiece = self.getTopPieceAtCoordinates(coordinates)
      if topPiece and not visitedPieces.has_key(topPiece.getNotation()):
        for p in self.getPiecesAtCoordinates(coordinates):
          visitedPieces[p.getNotation()] = 1
        self.visitPiece(topPiece, visitedPieces)

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


      for coordinates in adjacentCoordinatesList: #self.getAdjacentCoordinatesList(piece.coordinates)
        coordinatesKey = self.getBoardKey(coordinates)
        if not self.board.has_key(coordinatesKey) and not uniqueCoordinates.has_key(coordinatesKey):
          if self.getNumberOfPieces() == 1 or self.doCoordinatesOnlyBorderColor(coordinates, color):
            uniqueCoordinates[coordinatesKey] = 1
            coordinatesList.append(coordinates)

    if len(coordinatesList) == 0:
      coordinatesList.append((0, 0, 0))

    logging.debug('Hive.getEntryCoordinatesList(' + color + '): coordinatesList=' + str(coordinatesList))

    return coordinatesList; 

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

  def areCoordinatesAdjacent(self, firstCoordinates, secondCoordinates):
    for coordinates in self.getAdjacentCoordinatesList(firstCoordinates):
      if coordinates[0] == secondCoordinates[0] and coordinates[1] == secondCoordinates[1]:
        return True

    return False


  def getPiece(self, (color, kind, number)):
    for key in self.board.keys():
      for piece in self.board[key]:
        if piece.color == color and piece.kind == kind and str(piece.number) == number:
          return piece
    return None 

  
  def getRelativeCoordinates(self, piece, relativePiece, relativePosition):
    logging.debug('Hive.putdownPiece: piece=' + str(piece))

    newCoordinates = (0,0,0)
    if relativePiece:
      logging.debug('Hive.putdownPiece: relativePiece=' + str(relativePiece))
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
    return newCoordinates


  def pickupPiece(self, piece):
    key = self.getBoardKey(piece.coordinates)
    if len(self.board[key]) == 1:
      del self.board[key]
    else:
      self.board[key].remove(piece)


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
    self.turnNumber = 1

  def makeMove(self, moveString):
    self.validateMoveString(moveString)

    # check if the piece hasn't been played yet, otherwise take if from the board
    pieceAttributes = self.parsePieceAttributes(moveString)
    piece = self.currentPlayer.pickupPiece(pieceAttributes) 
    if not piece:
      piece = self.hive.getPiece(pieceAttributes)

    # QueenBee validation
    if self.turnNumber == 5 or self.turnNumber == 6:
      if not self.currentPlayer.hasPlayed('Q') and not piece.kind == 'Q':
        raise MoveError("You must play your QueenBee in your first 4 turns.")
      
    # get list of possible move coordinates
    possibleCoordinatesList = piece.getPossibleCoordinatesList(self.hive)

    # get proposed move coordinates
    relativePiece = None
    relativePosition = None
    relativeAttributes = self.parseRelativeAttributes(moveString)
    if (relativeAttributes):
      relativePiece = self.hive.getPiece(relativeAttributes[0])
      relativePosition = relativeAttributes[1]
    proposedCoordinates = self.hive.getRelativeCoordinates(piece, relativePiece, relativePosition)

    # check if valid move
    if not self.isValidMove(proposedCoordinates, possibleCoordinatesList):
      if piece.coordinates == (None, None, None):
        self.currentPlayer.putdownPiece(piece)
      raise MoveError ("The move you entered is invalid.")

    # make the move
    if not piece.coordinates == (None, None, None):
      self.hive.pickupPiece(piece)
    self.hive.putdownPiece(piece, proposedCoordinates)
  
    self.turnNumber += 1
    self.switchCurrentPlayer()
    self.moveList.append(moveString)
    
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
      raise InputError("I don't understand that move.")

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

  def getMoveListCsv(self):
    return ','.join(map(str, self.moveList))

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


def main():
    game = Game()

    print ('Hive AI Framework')
    print ('-------------------')
    print 

    enteredMove = None
    while True:
      enteredMove = raw_input(game.currentPlayer.color.capitalize() + '\'s turn, enter a move: ')
      if enteredMove == 'exit':
        break

      try:
        game.makeMove(enteredMove)
      except InputError as e:
        print e.value
      except MoveError as e:
        print e.value
      else:
        game.printBoard()

      print


    sys.exit(0)

if __name__ == "__main__": main() 

