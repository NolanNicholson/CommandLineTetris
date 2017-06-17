# Tetris in a command line
import _thread, time, os, random
FPS = 30
B_HEIGHT = 22
B_RENDERHEIGHT = 20
B_WIDTH = 10
BLANK_CHAR = '.'
LAYOUTS = {
    'T': [[0, 0], [1, -1], [1, 0], [1, 1]],
    'O': [[0, 0], [0, 1], [1, 0], [1, 1]],
    'I': [[0, -1], [0, 0], [0, 1], [0, 2]],
    'S': [[0, 0], [0, 1], [1, -1], [1, 0]],
    'Z': [[0, -1], [0, 0], [1, 0], [1, 1]],
    'L': [[0, -1], [0, 0], [0, 1], [1, -1]],
    'J': [[0, -1], [0, 0], [0, 1], [1, 1]],
}
PIECES = list(LAYOUTS.keys())
SCORE_COEFFICIENTS = [40, 100, 300, 1200]

# Getch (Windows only)
class _Getch:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _Getch()

def getNewActivePiece(gameState):
    # Retrieve the next piece and generate more pieces if we're running out
    pieceType = gameState['nextPieceQueue'].pop(0)
    if len(gameState['nextPieceQueue']) < 2:
        replenishNextQueue(gameState)

    newPieceBlocks = []
    for b in LAYOUTS[pieceType]:
        newPieceBlocks.append([b[0] + B_HEIGHT - B_RENDERHEIGHT, b[1]+4])
    activePiece = {
        'type':     pieceType,
        'blocks':   newPieceBlocks
    }
    return activePiece

def initialize():
    # Initialize board
    bHeight = 22
    bWidth = 10
    board = []
    for r in range(bHeight):
        row = []
        for c in range(bWidth):
            row.append(BLANK_CHAR)
        board.append(row)
    gameState = {
        'score': 0,
        'lines': 0,
        'gameOver': False,
        'softDropped': 0,
        'freq': FPS / 1.5,
        'level': 3,
        'nextPieceQueue': [],
        'cinematicTimer': 0,
        'clearingLines': [],
    }
    updateGameSpeed(gameState)
    gameState['timer'] = gameState['freq']
    replenishNextQueue(gameState)
    gameState['activePiece'] = getNewActivePiece(gameState)

    return board, gameState

def replenishNextQueue(gameState):
    # Replenishes the upcoming piece queue with a random shuffle of
    # one of each of the game pieces (to ensure the pieces come out balanced overall)
    piecesCopy = PIECES[:]
    while len(piecesCopy) > 0:
        gameState['nextPieceQueue'].append(piecesCopy.pop(random.randint(0, len(piecesCopy)-1)))

def renderBoard(board, gameState):
    # Clear previous render
    os.system('cls')

    # Make a copy of the board, to draw things on
    boardCopy = []
    for r in range(B_HEIGHT):
        row = []
        for c in range(B_WIDTH):
            row.append(board[r][c])
        boardCopy.append(row)

    # Add active game piece to board copy
    ap = gameState['activePiece']
    for b in ap['blocks']:
        boardCopy[b[0]][b[1]] = ap['type']
    if gameState['cinematicTimer'] > 0:
        cleared = gameState['clearingLines']
        for r in cleared:
            for c in range(len(board[0])):
                boardCopy[r][c] = '█' if gameState['cinematicTimer'] % 10 > 5 else ' '

    # Build other game information
    otherInfo = [['']] * B_HEIGHT
    otherInfo[3] = ['Next:']
    nextPieceRow = 5
    for i in range(nextPieceRow, nextPieceRow+2):
        otherInfo[i] = [' '] * 5
    otherInfo[9] = ['Score:']
    otherInfo[10] = [' ', gameState['score']]
    otherInfo[13] = ['Lines:']
    otherInfo[14] = [' ', gameState['lines']]
    otherInfo[17] = ['Level:']
    otherInfo[18] = [' ', gameState['level']]

    nextPiece = gameState['nextPieceQueue'][0]
    nextPieceLayout = LAYOUTS[nextPiece]
    for b in nextPieceLayout:
        otherInfo[nextPieceRow+b[0]][b[1]+2] = nextPiece


    # Draw game
    print('\n\n')
    for r in range(B_HEIGHT-B_RENDERHEIGHT, B_HEIGHT):
        # Draw gameboard
        print('  |', end='')
        for c in range(B_WIDTH):
            print(boardCopy[r][c], end='')
        print('| ', end='')
        # Draw other game information
        for c in otherInfo[r]:
            print(c, end='')
        print('')
    print('')

def inputGatherer(inputQueue):
    while True:
        keycode = getch()[0]
        if keycode not in inputQueue:
            inputQueue.append(keycode)

def moveX(activePiece, dx):
    # First, check if active piece can be moved without exiting range
    for b in activePiece['blocks']:
        if b[1] + dx > 9 or b[1] + dx < 0:
            return False
        elif board[b[0]][b[1] + dx] != BLANK_CHAR:
            return False
    # Okay, now we can move it
    for b in activePiece['blocks']:
        b[1] += dx

def moveY(gameState, board, dy):
    activePiece = gameState['activePiece']
    # First, check if active piece can be moved without exiting range
    for b in activePiece['blocks']:
        if b[0] + dy > B_HEIGHT - 1:
            # If the piece has hit the floor, we commit it to the board
            commit(gameState, board)
            return False
        elif b[0] + dy < 0:
            return False
        else:
            if board[b[0] + dy][b[1]] != BLANK_CHAR:
                commit(gameState, board)
                return False
    # Okay, now we can move it
    for b in activePiece['blocks']:
        b[0] += dy
    return True

def commit(gameState, board):
    # Commit a piece to the gameboard
    activePiece = gameState['activePiece']
    for b in activePiece['blocks']:
        board[b[0]][b[1]] = activePiece['type']

    gameState['score'] += gameState['softDropped']
    gameState['softDropped'] = 0

    # Check for game-over condition
    for b in activePiece['blocks']:
        if b[0] < 3:
            gameOver(gameState, board)
            return

    # Check for line completions
    checkForLines(gameState, board)

    # Spawn a new piece
    gameState['activePiece'] = getNewActivePiece(gameState)

def gameOver(gameState, board):
    # inputThread.exit()
    gameState['gameOver'] = True

def checkForLines(gameState, board):
    # Sweep the board for lines. If there are any, remove them.
    completedRows = []
    for r in range(len(board)):
        if BLANK_CHAR not in board[r]:
            completedRows.append(r)
    if len(completedRows) > 0:
        startClearingLines(gameState, board, completedRows)

def updateGameSpeed(gameState):
    # Calculate new time between auto-drops, but give it a minimum
    newSpeed = FPS / 1.5 - 2 * gameState['level']
    gameState['freq'] = max(newSpeed, 2)

def startClearingLines(gameState, board, completedRows):
    # Increase line count, level count, and score
    if ((gameState['lines'] + len(completedRows)) // 10) > (gameState['lines'] // 10):
        gameState['level'] += 1
        updateGameSpeed(gameState)
    gameState['lines'] += len(completedRows)
    gameState['score'] += SCORE_COEFFICIENTS[len(completedRows)-1] * (gameState['level'] + 1)
    # Set up line-clear cinematic
    gameState['clearingLines'] = completedRows
    gameState['cinematicTimer'] = 20

def finishClearingLines(gameState, board):
    while len(gameState['clearingLines']) > 0:
        filledRow = gameState['clearingLines'].pop(0)
        for i in range(filledRow, 0, -1):
            board[i] = board[i-1]

def rotate(activePiece, board, clockwise):
    # Rotate a piece counterclockwise
    # Get hypothetical rotation
    newBlocks = getRotatedVersion(activePiece, clockwise)
    for b in newBlocks:
        # Check if outside game bounds
        if b[0] > B_HEIGHT or b[1] > B_WIDTH or b[1] < 0:
            return False
        # Check for interference with other pieces
        # (only for pieces already on the board!)
        if board[b[0]][b[1]] != BLANK_CHAR:
            if b[0] >= 0:
                return False
    # If the rotation checks out, complete it
    activePiece['blocks'] = newBlocks

def getRotatedVersion(piece, clockwise):
    # Gets the hypothetical coordinates of a rotated piece.
    # Doesn't actually save the rotation yet.

    # First, get the axis of rotation (center of mass of the piece)
    rSum, cSum = 0, 0
    for b in piece['blocks']:
        rSum += b[0]
        cSum += b[1]
    rAvg = round(rSum/len(piece['blocks']))
    cAvg = round(cSum/len(piece['blocks']))

    # Then, get relative coords (relative to center of mass)
    rel = []
    for b in piece['blocks']:
        rel.append([b[0] - rAvg, b[1] - cAvg])

    # Clockwise rotation
    new = []
    if clockwise:
        for b in rel:
            new.append([b[1], -b[0]])
    else:
        for b in rel:
            new.append([-b[1], b[0]])

    # Get absolute coords again
    for b in new:
        b[0] += rAvg
        b[1] += cAvg

    return new

def gameStep(board, gameState, inputQueue):
    # TODO: Only re-render if board state has changed (for performance)
    renderBoard(board, gameState)
    activePiece = gameState['activePiece']

    if gameState['gameOver']:
        print("GAME OVER!")
        return False

    # Input listener
    if gameState['cinematicTimer'] > 0:
        inputQueue = []
    while len(inputQueue) > 0:
        keycode = inputQueue.pop(0)
        if keycode == 27:
            return False # end game
        elif keycode == 75:
            moveX(activePiece, -1)
        elif keycode == 77:
            moveX(activePiece, 1)
        elif keycode == 80:
            # moveY will commit the piece if it detects it has hit the floor
            if moveY(gameState, board, 1):
                # Record that the key-press move worked, for scoring
                gameState['softDropped'] += 1
            gameState['timer'] = gameState['freq']
        elif keycode == 72:
            # Up arrow key - snap piece down
            pass
        elif keycode == 122:
            # Key 122 is 'x' - rotate piece counterclockwise
            rotate(activePiece, board, False)
        elif keycode == 120:
            # Key 120 is 'x' - rotate piece clockwise
            rotate(activePiece, board, True)
        # else:
        #     print(keycode)

    if gameState['cinematicTimer'] > 0:
        # Advance line-clearing cinematic
        gameState['cinematicTimer'] -= 1
        if gameState['cinematicTimer'] <= 0:
            finishClearingLines(gameState, board)
    else:
        # Decrement timer and auto-drop pieces
        if gameState['timer'] <= 0:
            # moveY will commit the piece if it detects it has hit the floor
            result = moveY(gameState, board, 1)
            gameState['timer'] = gameState['freq']
        gameState['timer'] -= 1
    time.sleep(1/FPS)
    # print("Keycode:",keycode)
    return True # can continue game

board, gameState = initialize()
inputQueue = []
inputThread = _thread.start_new_thread(inputGatherer, (inputQueue,))

while True:
    if not gameStep(board, gameState, inputQueue):
        break
