# drag_puzzle_game.py
from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import random
import os
from PIL import Image
import base64
import io
from urllib.parse import quote

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Puzzle</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            max-width: 1000px;
            width: 100%;
            background-color: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        
        h1 {
            margin-bottom: 20px;
            font-size: 2.5rem;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .upload-section {
            background: rgba(255, 255, 255, 0.2);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            border: 2px dashed rgba(255, 255, 255, 0.5);
        }
        
        .upload-btn {
            background: linear-gradient(to right, #ff8a00, #da1b60);
            border: none;
            color: white;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 1.1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            display: inline-block;
            margin: 10px;
        }
        
        .upload-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 7px 20px rgba(0, 0, 0, 0.3);
        }
        
        #file-input {
            display: none;
        }
        
        .preview-container {
            margin: 20px 0;
            display: none;
        }
        
        #image-preview {
            max-width: 300px;
            max-height: 300px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .game-section {
            display: none;
        }
        
        .game-info {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 10px;
        }
        
        .puzzle-area {
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin: 20px 0;
        }
        
        .puzzle-board {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 2px;
            width: 400px;
            height: 400px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            overflow: hidden;
            background: rgba(0, 0, 0, 0.2);
            position: relative;
        }
        
        .puzzle-slot {
            aspect-ratio: 1;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }
        
        .puzzle-slot.hover {
            background: rgba(255, 255, 255, 0.3);
            border: 2px dashed #ffd700;
        }
        
        .puzzle-pieces-container {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 5px;
            width: 400px;
            height: 400px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        
        .puzzle-piece {
            aspect-ratio: 1;
            background-size: 400% 400%;
            border: 2px solid white;
            border-radius: 8px;
            cursor: grab;
            transition: all 0.3s ease;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            position: relative;
            z-index: 1;
        }
        
        .puzzle-piece:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4);
            z-index: 10;
        }
        
        .puzzle-piece.dragging {
            transform: scale(1.1) rotate(5deg);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.5);
            z-index: 100;
            cursor: grabbing;
        }
        
        .puzzle-piece.correct {
            border: 2px solid #00ff00;
            box-shadow: 0 0 10px #00ff00;
        }
        
        .empty-slot {
            background: rgba(255, 255, 255, 0.05);
            border: 2px dashed rgba(255, 255, 255, 0.5);
        }
        
        .controls {
            margin-top: 20px;
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        button {
            background: linear-gradient(to right, #4facfe, #00f2fe);
            border: none;
            color: white;
            padding: 12px 25px;
            border-radius: 50px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }
        
        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 7px 20px rgba(0, 0, 0, 0.3);
        }
        
        button:active {
            transform: translateY(1px);
        }
        
        .message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 10px;
            font-size: 1.2rem;
            display: none;
        }
        
        .success {
            background-color: rgba(46, 204, 113, 0.8);
            display: block;
        }
        
        @keyframes confetti {
            0% { transform: translateY(0) rotate(0); opacity: 1; }
            100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
        }
        
        .confetti {
            position: fixed;
            width: 10px;
            height: 10px;
            background-color: #f00;
            opacity: 0;
            top: 0;
            animation: confetti 3s ease-in-out forwards;
        }
        
        .difficulty-selector {
            margin: 15px 0;
        }
        
        select {
            padding: 8px 15px;
            border-radius: 5px;
            border: none;
            background: rgba(255, 255, 255, 0.9);
            font-size: 1rem;
        }
        
        .moves-counter {
            font-size: 1.2rem;
            font-weight: bold;
        }
        
        .instructions {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            text-align: left;
        }
        
        .instructions h3 {
            margin-bottom: 10px;
            color: #ffd700;
        }
        
        .instructions ul {
            padding-left: 20px;
        }
        
        .instructions li {
            margin-bottom: 8px;
        }
        
        .game-stats {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: #ffd700;
        }
        
        @media (max-width: 768px) {
            .puzzle-area {
                flex-direction: column;
                align-items: center;
            }
            
            .puzzle-board, .puzzle-pieces-container {
                width: 300px;
                height: 300px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Drag & Drop Image Puzzle</h1>
        
        <div class="instructions">
            <h3>How to Play:</h3>
            <ul>
                <li>Upload an image from your computer</li>
                <li>Select puzzle difficulty (3x3, 4x4, or 5x5)</li>
                <li>Drag puzzle pieces from the right container to the board on the left</li>
                <li>Drop pieces into the correct positions to reconstruct the image</li>
                <li>Correct pieces will snap into place with a green border</li>
            </ul>
        </div>
        
        <div class="upload-section" id="upload-section">
            <h2>Upload Your Image</h2>
            <p>Choose an image to create your custom puzzle</p>
            <input type="file" id="file-input" accept="image/*">
            <label for="file-input" class="upload-btn">Choose Image</label>
            <div class="preview-container" id="preview-container">
                <img id="image-preview" src="" alt="Preview">
            </div>
            <div class="difficulty-selector">
                <label for="difficulty">Select Difficulty: </label>
                <select id="difficulty">
                    <option value="3">3x3 (Easy)</option>
                    <option value="4" selected>4x4 (Medium)</option>
                    <option value="5">5x5 (Hard)</option>
                </select>
            </div>
            <button class="upload-btn" id="start-game-btn" style="display: none;">Start Puzzle</button>
        </div>
        
        <div class="game-section" id="game-section">
            <div class="game-stats">
                <div class="stat-item">
                    <div class="stat-value" id="placed-pieces">0</div>
                    <div>Pieces Placed</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="moves">0</div>
                    <div>Moves</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="timer">0</div>
                    <div>Seconds</div>
                </div>
            </div>
            
            <div class="puzzle-area">
                <div class="puzzle-board" id="puzzle-board"></div>
                <div class="puzzle-pieces-container" id="puzzle-pieces"></div>
            </div>
            
            <div class="controls">
                <button id="shuffle-btn">Shuffle Pieces</button>
                <button id="solve-btn">Show Solution</button>
                <button id="new-image-btn">New Image</button>
            </div>
            
            <div id="message" class="message"></div>
        </div>
    </div>

    <script>
        let puzzleSize = 4;
        let moves = 0;
        let timer = 0;
        let timerInterval;
        let placedPieces = 0;
        let currentImage = null;
        let piecePositions = {}; // Track where each piece is placed
        let draggedPiece = null;
        
        // DOM elements
        const fileInput = document.getElementById('file-input');
        const previewContainer = document.getElementById('preview-container');
        const imagePreview = document.getElementById('image-preview');
        const startGameBtn = document.getElementById('start-game-btn');
        const uploadSection = document.getElementById('upload-section');
        const gameSection = document.getElementById('game-section');
        const puzzleBoard = document.getElementById('puzzle-board');
        const puzzlePiecesContainer = document.getElementById('puzzle-pieces');
        
        // File input handler
        fileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    imagePreview.src = event.target.result;
                    previewContainer.style.display = 'block';
                    startGameBtn.style.display = 'inline-block';
                    currentImage = event.target.result;
                };
                reader.readAsDataURL(file);
            }
        });
        
        // Start game button handler
        startGameBtn.addEventListener('click', function() {
            if (currentImage) {
                uploadSection.style.display = 'none';
                gameSection.style.display = 'block';
                initGame();
            }
        });
        
        // Initialize the game
        function initGame() {
            clearInterval(timerInterval);
            moves = 0;
            timer = 0;
            placedPieces = 0;
            piecePositions = {};
            
            document.getElementById('moves').textContent = moves;
            document.getElementById('timer').textContent = timer;
            document.getElementById('placed-pieces').textContent = placedPieces;
            
            // Get selected difficulty
            puzzleSize = parseInt(document.getElementById('difficulty').value);
            
            // Generate puzzle
            generatePuzzle();
            
            // Start timer
            timerInterval = setInterval(() => {
                timer++;
                document.getElementById('timer').textContent = timer;
            }, 1000);
            
            // Hide success message
            document.getElementById('message').style.display = 'none';
        }
        
        // Generate the puzzle
        function generatePuzzle() {
            // Clear containers
            puzzleBoard.innerHTML = '';
            puzzlePiecesContainer.innerHTML = '';
            
            // Set grid templates
            puzzleBoard.style.gridTemplateColumns = `repeat(${puzzleSize}, 1fr)`;
            puzzlePiecesContainer.style.gridTemplateColumns = `repeat(${puzzleSize}, 1fr)`;
            
            // Create puzzle slots
            for (let i = 0; i < puzzleSize * puzzleSize; i++) {
                const slot = document.createElement('div');
                slot.className = 'puzzle-slot';
                slot.dataset.position = i;
                slot.dataset.correctPiece = i;
                
                // Add drag and drop events
                slot.addEventListener('dragover', handleDragOver);
                slot.addEventListener('dragenter', handleDragEnter);
                slot.addEventListener('dragleave', handleDragLeave);
                slot.addEventListener('drop', handleDrop);
                
                puzzleBoard.appendChild(slot);
            }
            
            // Create puzzle pieces (shuffled)
            const pieceOrder = Array.from({length: puzzleSize * puzzleSize}, (_, i) => i);
            shuffleArray(pieceOrder);
            
            for (let i = 0; i < pieceOrder.length; i++) {
                const pieceIndex = pieceOrder[i];
                const piece = document.createElement('div');
                piece.className = 'puzzle-piece';
                piece.dataset.pieceId = pieceIndex;
                piece.draggable = true;
                
                // Calculate background position for the image
                const row = Math.floor(pieceIndex / puzzleSize);
                const col = pieceIndex % puzzleSize;
                const xPos = (col / (puzzleSize - 1)) * 100;
                const yPos = (row / (puzzleSize - 1)) * 100;
                
                // Set the background image and position
                piece.style.backgroundImage = `url(${currentImage})`;
                piece.style.backgroundPosition = `${xPos}% ${yPos}%`;
                piece.style.backgroundSize = `${puzzleSize * 100}% ${puzzleSize * 100}%`;
                
                // Add drag events
                piece.addEventListener('dragstart', handleDragStart);
                piece.addEventListener('dragend', handleDragEnd);
                
                puzzlePiecesContainer.appendChild(piece);
                
                // Initialize piece position (all in pieces container)
                piecePositions[pieceIndex] = -1;
            }
        }
        
        // Drag and Drop Handlers
        function handleDragStart(e) {
            draggedPiece = this;
            this.classList.add('dragging');
            e.dataTransfer.setData('text/plain', this.dataset.pieceId);
            
            // Add a slight delay for better visual feedback
            setTimeout(() => {
                this.style.opacity = '0.4';
            }, 0);
        }
        
        function handleDragEnd(e) {
            this.classList.remove('dragging');
            this.style.opacity = '1';
            draggedPiece = null;
            
            // Remove hover effects from all slots
            document.querySelectorAll('.puzzle-slot.hover').forEach(slot => {
                slot.classList.remove('hover');
            });
        }
        
        function handleDragOver(e) {
            e.preventDefault(); // Necessary to allow drop
        }
        
        function handleDragEnter(e) {
            e.preventDefault();
            this.classList.add('hover');
        }
        
        function handleDragLeave(e) {
            this.classList.remove('hover');
        }
        
        function handleDrop(e) {
            e.preventDefault();
            this.classList.remove('hover');
            
            const pieceId = parseInt(e.dataTransfer.getData('text/plain'));
            const slotPosition = parseInt(this.dataset.position);
            const correctPieceId = parseInt(this.dataset.correctPiece);
            
            // If there's already a piece here, return it to pieces container
            if (this.children.length > 0) {
                const existingPiece = this.children[0];
                puzzlePiecesContainer.appendChild(existingPiece);
                piecePositions[parseInt(existingPiece.dataset.pieceId)] = -1;
                placedPieces--;
            }
            
            // Move the dragged piece to this slot
            this.appendChild(draggedPiece);
            piecePositions[pieceId] = slotPosition;
            placedPieces++;
            
            // Check if piece is in correct position
            if (pieceId === correctPieceId) {
                draggedPiece.classList.add('correct');
            } else {
                draggedPiece.classList.remove('correct');
            }
            
            // Update stats
            moves++;
            document.getElementById('moves').textContent = moves;
            document.getElementById('placed-pieces').textContent = placedPieces;
            
            // Check if puzzle is solved
            if (isSolved()) {
                clearInterval(timerInterval);
                showSuccessMessage();
                createConfetti();
            }
        }
        
        // Shuffle array using Fisher-Yates algorithm
        function shuffleArray(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
        }
        
        // Check if the puzzle is solved
        function isSolved() {
            for (let pieceId = 0; pieceId < puzzleSize * puzzleSize; pieceId++) {
                if (piecePositions[pieceId] !== pieceId) {
                    return false;
                }
            }
            return true;
        }
        
        // Show success message
        function showSuccessMessage() {
            const message = document.getElementById('message');
            message.textContent = `Congratulations! You solved the puzzle in ${moves} moves and ${timer} seconds!`;
            message.className = 'message success';
            message.style.display = 'block';
        }
        
        // Create confetti animation
        function createConfetti() {
            const colors = ['#f94144', '#f3722c', '#f8961e', '#f9c74f', '#90be6d', '#43aa8b', '#577590'];
            
            for (let i = 0; i < 100; i++) {
                const confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.left = Math.random() * 100 + 'vw';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.animationDelay = Math.random() * 3 + 's';
                document.body.appendChild(confetti);
                
                // Remove confetti after animation
                setTimeout(() => {
                    confetti.remove();
                }, 3000);
            }
        }
        
        // Event listeners for controls
        document.getElementById('shuffle-btn').addEventListener('click', () => {
            // Return all pieces to pieces container
            document.querySelectorAll('.puzzle-piece').forEach(piece => {
                puzzlePiecesContainer.appendChild(piece);
                piece.classList.remove('correct');
            });
            
            // Reset positions
            for (let pieceId in piecePositions) {
                piecePositions[pieceId] = -1;
            }
            
            // Shuffle pieces in container
            const pieces = Array.from(puzzlePiecesContainer.children);
            shuffleArray(pieces);
            pieces.forEach(piece => puzzlePiecesContainer.appendChild(piece));
            
            // Reset stats
            placedPieces = 0;
            moves = 0;
            document.getElementById('moves').textContent = moves;
            document.getElementById('placed-pieces').textContent = placedPieces;
        });
        
        document.getElementById('solve-btn').addEventListener('click', () => {
            // Clear the board and pieces container
            puzzleBoard.innerHTML = '';
            puzzlePiecesContainer.innerHTML = '';
            
            // Create solved puzzle
            for (let i = 0; i < puzzleSize * puzzleSize; i++) {
                const slot = document.createElement('div');
                slot.className = 'puzzle-slot';
                slot.dataset.position = i;
                slot.dataset.correctPiece = i;
                
                const piece = document.createElement('div');
                piece.className = 'puzzle-piece correct';
                piece.dataset.pieceId = i;
                
                // Calculate background position for the image
                const row = Math.floor(i / puzzleSize);
                const col = i % puzzleSize;
                const xPos = (col / (puzzleSize - 1)) * 100;
                const yPos = (row / (puzzleSize - 1)) * 100;
                
                // Set the background image and position
                piece.style.backgroundImage = `url(${currentImage})`;
                piece.style.backgroundPosition = `${xPos}% ${yPos}%`;
                piece.style.backgroundSize = `${puzzleSize * 100}% ${puzzleSize * 100}%`;
                
                slot.appendChild(piece);
                puzzleBoard.appendChild(slot);
                
                piecePositions[i] = i;
            }
            
            placedPieces = puzzleSize * puzzleSize;
            document.getElementById('placed-pieces').textContent = placedPieces;
            
            clearInterval(timerInterval);
            showSuccessMessage();
            createConfetti();
        });
        
        document.getElementById('new-image-btn').addEventListener('click', () => {
            gameSection.style.display = 'none';
            uploadSection.style.display = 'block';
            previewContainer.style.display = 'none';
            startGameBtn.style.display = 'none';
            fileInput.value = '';
            currentImage = null;
        });
        
        document.getElementById('difficulty').addEventListener('change', function() {
            if (gameSection.style.display === 'block') {
                initGame();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    app.run(debug=True)