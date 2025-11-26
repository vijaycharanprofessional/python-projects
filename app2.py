from flask import Flask, render_template_string, request, jsonify
import random
import json
from threading import Lock
import time

app = Flask(__name__)
game_states = {}
game_lock = Lock()

# Tetris constants
GRID_WIDTH = 10
GRID_HEIGHT = 20
GRID_SIZE = 30

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]]   # L
]

COLORS = [
    "#00FFFF",  # CYAN - I
    "#FFFF00",  # YELLOW - O
    "#FF00FF",  # MAGENTA - T
    "#00FF00",  # GREEN - S
    "#FF0000",  # RED - Z
    "#0000FF",  # BLUE - J
    "#FFA500"   # ORANGE - L
]

class TetrisGame:
    def __init__(self, game_id):
        self.game_id = game_id
        self.reset()
    
    def reset(self):
        self.board = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.last_update = time.time()
        self.fall_speed = 1.0
        self.started = False
    
    def new_piece(self):
        shape_idx = random.randint(0, len(SHAPES) - 1)
        return {
            'shape': SHAPES[shape_idx],
            'color': COLORS[shape_idx],
            'x': GRID_WIDTH // 2 - len(SHAPES[shape_idx][0]) // 2,
            'y': 0
        }
    
    def valid_move(self, piece, x, y):
        shape = piece['shape']
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell:
                    if (x + j < 0 or x + j >= GRID_WIDTH or 
                        y + i >= GRID_HEIGHT or 
                        (y + i >= 0 and self.board[y + i][x + j])):
                        return False
        return True
    
    def rotate_piece(self):
        if not self.started or self.game_over:
            return False
            
        shape = self.current_piece['shape']
        rotated = list(zip(*shape[::-1]))
        rotated = [list(row) for row in rotated]
        
        old_shape = self.current_piece['shape']
        self.current_piece['shape'] = rotated
        
        if not self.valid_move(self.current_piece, self.current_piece['x'], self.current_piece['y']):
            self.current_piece['shape'] = old_shape
            return False
        return True
    
    def move(self, dx, dy):
        if not self.started or self.game_over:
            return False
            
        new_x = self.current_piece['x'] + dx
        new_y = self.current_piece['y'] + dy
        
        if self.valid_move(self.current_piece, new_x, new_y):
            self.current_piece['x'] = new_x
            self.current_piece['y'] = new_y
            return True
        elif dy > 0:  # Moving down and can't
            self.lock_piece()
            self.clear_lines()
            self.current_piece = self.next_piece
            self.next_piece = self.new_piece()
            
            # Check if game over
            if not self.valid_move(self.current_piece, self.current_piece['x'], self.current_piece['y']):
                self.game_over = True
            return False
        return False
    
    def lock_piece(self):
        for i, row in enumerate(self.current_piece['shape']):
            for j, cell in enumerate(row):
                if cell and self.current_piece['y'] + i >= 0:
                    self.board[self.current_piece['y'] + i][self.current_piece['x'] + j] = self.current_piece['color']
    
    def clear_lines(self):
        lines_to_clear = []
        for i, row in enumerate(self.board):
            if all(cell != 0 for cell in row):
                lines_to_clear.append(i)
        
        for line in lines_to_clear:
            del self.board[line]
            self.board.insert(0, [0 for _ in range(GRID_WIDTH)])
        
        # Update score
        if lines_to_clear:
            self.lines_cleared += len(lines_to_clear)
            self.score += [0, 40, 100, 300, 1200][len(lines_to_clear)] * self.level
            self.level = self.lines_cleared // 10 + 1
            self.fall_speed = max(0.1, 1.0 - (self.level - 1) * 0.1)
    
    def drop(self):
        if not self.started or self.game_over:
            return
        while self.move(0, 1):
            pass
    
    def update(self):
        if not self.started or self.game_over:
            return
            
        current_time = time.time()
        if current_time - self.last_update > self.fall_speed:
            self.move(0, 1)
            self.last_update = current_time
    
    def start(self):
        self.started = True
        self.last_update = time.time()
    
    def get_state(self):
        # Create a copy of board with current piece
        display_board = [row[:] for row in self.board]
        
        if self.started and not self.game_over:
            for i, row in enumerate(self.current_piece['shape']):
                for j, cell in enumerate(row):
                    if cell:
                        y_pos = self.current_piece['y'] + i
                        x_pos = self.current_piece['x'] + j
                        if 0 <= y_pos < GRID_HEIGHT and 0 <= x_pos < GRID_WIDTH:
                            display_board[y_pos][x_pos] = self.current_piece['color']
        
        return {
            'board': display_board,
            'next_piece': self.next_piece,
            'score': self.score,
            'level': self.level,
            'lines_cleared': self.lines_cleared,
            'game_over': self.game_over,
            'started': self.started
        }

# HTML Template with embedded CSS and JavaScript
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Web Tetris</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            font-family: 'Arial', sans-serif;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            overflow-x: hidden;
        }
        
        #game-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
            align-items: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            max-width: 100%;
            position: relative;
        }
        
        @media (min-width: 768px) {
            #game-container {
                flex-direction: row;
                align-items: flex-start;
                gap: 30px;
            }
        }
        
        #game-board-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 15px;
        }
        
        #game-board {
            border: 3px solid #fff;
            border-radius: 5px;
            background: #111;
            max-width: 100%;
            height: auto;
        }
        
        #sidebar {
            width: 100%;
            max-width: 300px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        @media (min-width: 768px) {
            #sidebar {
                width: 200px;
            }
        }
        
        .panel {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        h2 {
            color: #00ffff;
            margin-bottom: 10px;
            font-size: 1.2em;
            text-shadow: 0 0 10px #00ffff;
        }
        
        #next-piece-canvas {
            border: 2px solid #333;
            background: #111;
            margin-top: 10px;
            max-width: 100%;
            height: auto;
        }
        
        #score-info {
            font-size: 1.1em;
            line-height: 1.6;
        }
        
        #score-info div {
            margin: 5px 0;
            color: #ffff00;
        }
        
        #controls {
            font-size: 0.9em;
            line-height: 1.8;
        }
        
        #controls kbd {
            background: #333;
            padding: 2px 6px;
            border-radius: 4px;
            border: 1px solid #555;
        }
        
        #mobile-controls {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 15px;
            width: 100%;
        }
        
        @media (min-width: 768px) {
            #mobile-controls {
                display: none;
            }
        }
        
        .mobile-row {
            display: flex;
            justify-content: center;
            gap: 10px;
        }
        
        .mobile-btn {
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.5);
            border-radius: 10px;
            color: white;
            font-size: 1.5em;
            padding: 15px 20px;
            min-width: 60px;
            text-align: center;
            cursor: pointer;
            user-select: none;
            transition: all 0.2s;
        }
        
        .mobile-btn:active {
            background: rgba(255, 255, 255, 0.4);
            transform: scale(0.95);
        }
        
        #rotate-btn {
            background: rgba(0, 255, 255, 0.3);
        }
        
        #drop-btn {
            background: rgba(255, 255, 0, 0.3);
        }
        
        #start-screen {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            z-index: 100;
            border-radius: 15px;
        }
        
        #start-screen h1 {
            color: #00ffff;
            font-size: 3em;
            margin-bottom: 30px;
            text-shadow: 0 0 20px #00ffff;
            text-align: center;
        }
        
        @media (max-width: 480px) {
            #start-screen h1 {
                font-size: 2em;
            }
        }
        
        #start-btn {
            background: #00ffff;
            color: #000;
            border: none;
            padding: 20px 40px;
            font-size: 1.5em;
            border-radius: 10px;
            cursor: pointer;
            margin: 20px;
            transition: all 0.3s;
            font-weight: bold;
        }
        
        #start-btn:hover {
            background: #ffff00;
            transform: scale(1.1);
            box-shadow: 0 0 20px #ffff00;
        }
        
        #game-over {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            z-index: 1000;
        }
        
        #game-over h1 {
            color: #ff4444;
            font-size: 3em;
            margin-bottom: 20px;
            text-shadow: 0 0 20px #ff0000;
        }
        
        @media (max-width: 480px) {
            #game-over h1 {
                font-size: 2em;
            }
        }
        
        #game-over button {
            background: #00ffff;
            color: #000;
            border: none;
            padding: 15px 30px;
            font-size: 1.2em;
            border-radius: 10px;
            cursor: pointer;
            margin: 10px;
            transition: all 0.3s;
        }
        
        #game-over button:hover {
            background: #ffff00;
            transform: scale(1.1);
        }
        
        #restart-btn {
            background: #ffff00;
            color: #000;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin-top: 10px;
            transition: all 0.3s;
            width: 100%;
        }
        
        #restart-btn:hover {
            background: #00ffff;
            transform: scale(1.05);
        }
        
        #pause-btn {
            background: #ff00ff;
            color: #000;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin-top: 5px;
            transition: all 0.3s;
            width: 100%;
        }
        
        #pause-btn:hover {
            background: #00ffff;
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div id="game-container">
        <div id="start-screen">
            <h1>PYTHON TETRIS</h1>
            <button id="start-btn">START GAME</button>
        </div>
        
        <div id="game-board-container">
            <canvas id="game-board" width="300" height="600"></canvas>
            
            <div id="mobile-controls">
                <div class="mobile-row">
                    <div class="mobile-btn" id="left-btn">←</div>
                    <div class="mobile-btn" id="rotate-btn">↻</div>
                    <div class="mobile-btn" id="right-btn">→</div>
                </div>
                <div class="mobile-row">
                    <div class="mobile-btn" id="down-btn">↓</div>
                    <div class="mobile-btn" id="drop-btn">↓ ↓</div>
                </div>
            </div>
        </div>
        
        <div id="sidebar">
            <div class="panel">
                <h2>NEXT PIECE</h2>
                <canvas id="next-piece-canvas" width="120" height="120"></canvas>
            </div>
            
            <div class="panel" id="score-info">
                <h2>SCORE</h2>
                <div id="score">0</div>
                <div id="level">Level: 1</div>
                <div id="lines">Lines: 0</div>
            </div>
            
            <div class="panel" id="controls">
                <h2>CONTROLS</h2>
                <div>← → : Move</div>
                <div>↑ : Rotate</div>
                <div>↓ : Soft Drop</div>
                <div>Space : Hard Drop</div>
                <div>P : Pause</div>
                <div>R : Restart</div>
            </div>
            
            <button id="restart-btn">RESTART GAME</button>
            <button id="pause-btn">PAUSE</button>
        </div>
    </div>
    
    <div id="game-over">
        <h1>GAME OVER</h1>
        <div id="final-score" style="font-size: 1.5em; margin-bottom: 20px;"></div>
        <button onclick="restartGame()">PLAY AGAIN</button>
    </div>

    <script>
        const gameId = 'player_' + Math.random().toString(36).substr(2, 9);
        let gameState = null;
        let isPaused = false;
        let gameStarted = false;
        
        const mainCanvas = document.getElementById('game-board');
        const nextCanvas = document.getElementById('next-piece-canvas');
        const mainCtx = mainCanvas.getContext('2d');
        const nextCtx = nextCanvas.getContext('2d');
        const gridSize = 30;
        
        // Responsive canvas sizing
        function resizeCanvas() {
            const container = document.getElementById('game-board-container');
            const maxWidth = container.clientWidth - 40; // Account for padding
            
            if (maxWidth < 300) {
                const scale = maxWidth / 300;
                mainCanvas.style.width = maxWidth + 'px';
                mainCanvas.style.height = (600 * scale) + 'px';
            } else {
                mainCanvas.style.width = '300px';
                mainCanvas.style.height = '600px';
            }
        }
        
        // Game loop
        function gameLoop() {
            if (gameStarted && !isPaused) {
                updateGame();
            }
            drawGame();
            requestAnimationFrame(gameLoop);
        }
        
        // Update game state from server
        async function updateGame() {
            try {
                const response = await fetch('/game/state/' + gameId);
                gameState = await response.json();
                
                // Update UI
                document.getElementById('score').textContent = gameState.score;
                document.getElementById('level').textContent = 'Level: ' + gameState.level;
                document.getElementById('lines').textContent = 'Lines: ' + gameState.lines_cleared;
                
                if (gameState.game_over) {
                    document.getElementById('final-score').textContent = 'Final Score: ' + gameState.score;
                    document.getElementById('game-over').style.display = 'flex';
                    gameStarted = false;
                }
            } catch (error) {
                console.error('Error updating game:', error);
            }
        }
        
        // Draw game
        function drawGame() {
            if (!gameState) return;
            
            // Clear canvases
            mainCtx.fillStyle = '#111';
            mainCtx.fillRect(0, 0, mainCanvas.width, mainCanvas.height);
            
            nextCtx.fillStyle = '#111';
            nextCtx.fillRect(0, 0, nextCanvas.width, nextCanvas.height);
            
            // Draw main board
            drawBoard(mainCtx, gameState.board, 0, 0);
            
            // Draw next piece
            if (gameState.next_piece) {
                drawPiece(nextCtx, gameState.next_piece, 30, 30);
            }
        }
        
        // Draw game board
        function drawBoard(ctx, board, offsetX, offsetY) {
            for (let y = 0; y < board.length; y++) {
                for (let x = 0; x < board[y].length; x++) {
                    if (board[y][x]) {
                        ctx.fillStyle = board[y][x];
                        ctx.fillRect(x * gridSize, y * gridSize, gridSize, gridSize);
                        
                        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
                        ctx.strokeRect(x * gridSize, y * gridSize, gridSize, gridSize);
                    }
                }
            }
        }
        
        // Draw a piece
        function drawPiece(ctx, piece, offsetX, offsetY) {
            const shape = piece.shape;
            const color = piece.color;
            
            for (let y = 0; y < shape.length; y++) {
                for (let x = 0; x < shape[y].length; x++) {
                    if (shape[y][x]) {
                        ctx.fillStyle = color;
                        ctx.fillRect(offsetX + x * gridSize, offsetY + y * gridSize, gridSize, gridSize);
                        
                        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
                        ctx.strokeRect(offsetX + x * gridSize, offsetY + y * gridSize, gridSize, gridSize);
                    }
                }
            }
        }
        
        // Start the game
        async function startGame() {
            await fetch('/game/start/' + gameId, {method: 'POST'});
            document.getElementById('start-screen').style.display = 'none';
            gameStarted = true;
            isPaused = false;
        }
        
        // Handle keyboard input
        document.addEventListener('keydown', async (e) => {
            if (!gameStarted || (gameState && gameState.game_over)) return;
            
            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    await fetch('/game/move/' + gameId, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({dx: -1, dy: 0})
                    });
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    await fetch('/game/move/' + gameId, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({dx: 1, dy: 0})
                    });
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    await fetch('/game/move/' + gameId, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({dx: 0, dy: 1})
                    });
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    await fetch('/game/rotate/' + gameId, {method: 'POST'});
                    break;
                case ' ':
                    e.preventDefault();
                    await fetch('/game/drop/' + gameId, {method: 'POST'});
                    break;
                case 'p':
                case 'P':
                    e.preventDefault();
                    togglePause();
                    break;
                case 'r':
                case 'R':
                    e.preventDefault();
                    restartGame();
                    break;
            }
        });
        
        // Mobile controls
        document.getElementById('left-btn').addEventListener('click', async () => {
            if (!gameStarted) return;
            await fetch('/game/move/' + gameId, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dx: -1, dy: 0})
            });
        });
        
        document.getElementById('right-btn').addEventListener('click', async () => {
            if (!gameStarted) return;
            await fetch('/game/move/' + gameId, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dx: 1, dy: 0})
            });
        });
        
        document.getElementById('down-btn').addEventListener('click', async () => {
            if (!gameStarted) return;
            await fetch('/game/move/' + gameId, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({dx: 0, dy: 1})
            });
        });
        
        document.getElementById('rotate-btn').addEventListener('click', async () => {
            if (!gameStarted) return;
            await fetch('/game/rotate/' + gameId, {method: 'POST'});
        });
        
        document.getElementById('drop-btn').addEventListener('click', async () => {
            if (!gameStarted) return;
            await fetch('/game/drop/' + gameId, {method: 'POST'});
        });
        
        // Pause functionality
        function togglePause() {
            if (!gameStarted) return;
            isPaused = !isPaused;
            document.getElementById('pause-btn').textContent = isPaused ? 'RESUME' : 'PAUSE';
        }
        
        document.getElementById('pause-btn').addEventListener('click', togglePause);
        
        // Restart game
        async function restartGame() {
            await fetch('/game/reset/' + gameId, {method: 'POST'});
            document.getElementById('game-over').style.display = 'none';
            document.getElementById('start-screen').style.display = 'flex';
            gameStarted = false;
            isPaused = false;
            document.getElementById('pause-btn').textContent = 'PAUSE';
        }
        
        // Initialize game
        document.getElementById('start-btn').addEventListener('click', startGame);
        document.getElementById('restart-btn').addEventListener('click', restartGame);
        
        // Handle window resize
        window.addEventListener('resize', resizeCanvas);
        
        // Start the game loop (but not the actual game)
        resizeCanvas();
        gameLoop();
        
        // Initialize game on server (but don't start it yet)
        fetch('/game/init/' + gameId, {method: 'POST'});
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/game/init/<game_id>', methods=['POST'])
def init_game(game_id):
    with game_lock:
        game_states[game_id] = TetrisGame(game_id)
    return jsonify({'status': 'initialized'})

@app.route('/game/start/<game_id>', methods=['POST'])
def start_game(game_id):
    with game_lock:
        if game_id in game_states:
            game = game_states[game_id]
            game.start()
            return jsonify({'status': 'started'})
        return jsonify({'error': 'Game not found'}), 404

@app.route('/game/state/<game_id>')
def get_game_state(game_id):
    with game_lock:
        if game_id in game_states:
            game = game_states[game_id]
            game.update()
            return jsonify(game.get_state())
        return jsonify({'error': 'Game not found'}), 404

@app.route('/game/move/<game_id>', methods=['POST'])
def move_piece(game_id):
    with game_lock:
        if game_id in game_states:
            data = request.get_json()
            game = game_states[game_id]
            game.move(data.get('dx', 0), data.get('dy', 0))
            return jsonify({'status': 'moved'})
        return jsonify({'error': 'Game not found'}), 404

@app.route('/game/rotate/<game_id>', methods=['POST'])
def rotate_piece(game_id):
    with game_lock:
        if game_id in game_states:
            game = game_states[game_id]
            game.rotate_piece()
            return jsonify({'status': 'rotated'})
        return jsonify({'error': 'Game not found'}), 404

@app.route('/game/drop/<game_id>', methods=['POST'])
def drop_piece(game_id):
    with game_lock:
        if game_id in game_states:
            game = game_states[game_id]
            game.drop()
            return jsonify({'status': 'dropped'})
        return jsonify({'error': 'Game not found'}), 404

@app.route('/game/reset/<game_id>', methods=['POST'])
def reset_game(game_id):
    with game_lock:
        if game_id in game_states:
            game_states[game_id].reset()
            return jsonify({'status': 'reset'})
        return jsonify({'error': 'Game not found'}), 404

if __name__ == '__main__':
    print("Starting Tetris Web Server...")
    print("Open http://localhost:5000 in your browser to play!")
    app.run(debug=True, host='0.0.0.0', port=5000)