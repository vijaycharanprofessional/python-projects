from flask import Flask, render_template_string, request, jsonify, session
import random
import os
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

# Game state with enhanced features
class GameState:
    def __init__(self):  # Fixed: Changed _init_ to __init__
        self.number_to_guess = random.randint(1, 100)
        self.attempts = 0
        self.game_over = False
        self.guess_history = []
        self.difficulty = "normal"  # easy: 1-50, normal: 1-100, hard: 1-200
        self.max_attempts = 10
        self.start_time = time.time()
        self.score = 0

# Store games by session
games = {}

def get_game_state(session_id):
    if session_id not in games:
        games[session_id] = GameState()
    return games[session_id]

def calculate_score(game):
    if not game.game_over:
        return 0
    
    base_score = 1000
    time_penalty = min(int((time.time() - game.start_time) / 10), 500)  # Max 500 point penalty for time
    attempt_penalty = game.attempts * 20  # 20 points per attempt
    
    # Difficulty multiplier
    if game.difficulty == "easy":
        multiplier = 0.7
    elif game.difficulty == "hard":
        multiplier = 1.5
    else:
        multiplier = 1.0
    
    score = max(0, (base_score - time_penalty - attempt_penalty) * multiplier)
    return int(score)

# HTML template with enhanced features
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anime Number Guessing Game</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;800&display=swap');
        
        :root {
            --primary: #ff6b93;
            --secondary: #6bc6ff;
            --accent: #ffd166;
            --dark: #333;
            --light: #fff;
            --success: #8ac926;
            --warning: #ffd166;
            --danger: #ef476f;
            --bg-light: #ffecf1;
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: 'M PLUS Rounded 1c', sans-serif;
            background: linear-gradient(135deg, #ffecf1 0%, #e0f7fa 100%);
            color: var(--dark);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: var(--light);
            border-radius: 25px;
            padding: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            border: 3px solid var(--primary);
            position: relative;
            overflow: hidden;
        }
        
        .container::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 10px;
            background: linear-gradient(90deg, var(--primary), var(--secondary), var(--accent));
        }
        
        h1 {
            color: var(--primary);
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 3px 3px 0px rgba(255, 107, 147, 0.2);
            text-align: center;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.2em;
            text-align: center;
        }
        
        .stats-container {
            display: flex;
            justify-content: space-between;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 15px;
            border-radius: 15px;
            margin-bottom: 25px;
            border: 2px dashed var(--secondary);
        }
        
        .stat-box {
            text-align: center;
            flex: 1;
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: 800;
            color: var(--primary);
        }
        
        .stat-label {
            font-size: 0.9em;
            color: #666;
        }
        
        .game-area {
            margin: 30px 0;
        }
        
        .difficulty-selector {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .difficulty-btn {
            padding: 8px 15px;
            border: 2px solid var(--secondary);
            background: white;
            border-radius: 20px;
            cursor: pointer;
            font-family: 'M PLUS Rounded 1c', sans-serif;
            transition: all 0.3s;
        }
        
        .difficulty-btn.active {
            background: var(--secondary);
            color: white;
        }
        
        .input-group {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        
        input[type="number"] {
            padding: 15px 20px;
            font-size: 1.3em;
            border: 3px solid var(--primary);
            border-radius: 15px 0 0 15px;
            width: 150px;
            text-align: center;
            font-family: 'M PLUS Rounded 1c', sans-serif;
            font-weight: 700;
        }
        
        button {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 15px 25px;
            font-size: 1.3em;
            border-radius: 0 15px 15px 0;
            cursor: pointer;
            font-family: 'M PLUS Rounded 1c', sans-serif;
            transition: all 0.3s;
            font-weight: 700;
        }
        
        button:hover {
            background-color: #ff4d7d;
            transform: translateY(-2px);
        }
        
        .action-buttons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
        }
        
        .action-btn {
            border-radius: 15px;
            padding: 12px 25px;
        }
        
        #new-game-btn {
            background-color: var(--secondary);
        }
        
        #new-game-btn:hover {
            background-color: #4db8ff;
        }
        
        #hint-btn {
            background-color: var(--accent);
            color: var(--dark);
        }
        
        #hint-btn:hover {
            background-color: #ffc233;
        }
        
        .message {
            margin: 20px 0;
            padding: 20px;
            border-radius: 15px;
            font-size: 1.3em;
            min-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            font-weight: 700;
            transition: all 0.5s;
        }
        
        .correct {
            background-color: rgba(138, 201, 38, 0.2);
            color: #2e7d32;
            border: 3px solid var(--success);
            animation: pulse 1s infinite;
        }
        
        .low, .high {
            background-color: rgba(255, 209, 102, 0.2);
            color: #b75b00;
            border: 3px solid var(--warning);
        }
        
        .game-over {
            background-color: rgba(239, 71, 111, 0.2);
            color: #b00020;
            border: 3px solid var(--danger);
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        
        .attempts {
            font-size: 1.2em;
            margin-top: 20px;
            color: #666;
            text-align: center;
        }
        
        .anime-character {
            font-size: 5em;
            margin: 20px 0;
            text-align: center;
            transition: all 0.5s;
        }
        
        .history-container {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            margin-top: 30px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .history-title {
            color: var(--primary);
            margin-bottom: 15px;
            text-align: center;
            font-weight: 700;
        }
        
        .history-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }
        
        .history-item {
            background: white;
            padding: 8px 15px;
            border-radius: 20px;
            border: 2px solid var(--secondary);
            font-weight: 700;
        }
        
        .history-item.correct {
            background: var(--success);
            color: white;
        }
        
        .history-item.low {
            background: var(--warning);
            color: var(--dark);
        }
        
        .history-item.high {
            background: var(--danger);
            color: white;
        }
        
        .instructions {
            background: linear-gradient(135deg, #f0f8ff 0%, #e6f7ff 100%);
            padding: 20px;
            border-radius: 15px;
            margin-top: 30px;
            text-align: left;
            border-left: 5px solid var(--secondary);
        }
        
        .instructions h3 {
            margin-top: 0;
            color: var(--primary);
            text-align: center;
            margin-bottom: 15px;
        }
        
        .instructions ul {
            padding-left: 20px;
        }
        
        .instructions li {
            margin-bottom: 10px;
        }
        
        footer {
            margin-top: 30px;
            color: #888;
            font-size: 0.9em;
            text-align: center;
        }
        
        .hidden {
            display: none;
        }
        
        .progress-bar {
            height: 10px;
            background-color: #e9ecef;
            border-radius: 5px;
            margin: 15px 0;
            overflow: hidden;
        }
        
        .progress {
            height: 100%;
            background: linear-gradient(90deg, var(--secondary), var(--primary));
            width: 0%;
            transition: width 0.5s;
        }
        
        @media (max-width: 600px) {
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 2.2em;
            }
            
            .stats-container {
                flex-direction: column;
                gap: 15px;
            }
            
            .input-group {
                flex-direction: column;
                align-items: center;
            }
            
            input[type="number"] {
                border-radius: 15px;
                margin-bottom: 10px;
                width: 100%;
                max-width: 200px;
            }
            
            button {
                border-radius: 15px;
                width: 100%;
                max-width: 200px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1><i class="fas fa-gamepad"></i> Anime Number Game</h1>
        <div class="subtitle">Guess the secret number and score points!</div>
        
        <div class="stats-container">
            <div class="stat-box">
                <div class="stat-value" id="attempts-display">0</div>
                <div class="stat-label">Attempts</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="score-display">0</div>
                <div class="stat-label">Score</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="range-display">1-100</div>
                <div class="stat-label">Range</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" id="time-display">0s</div>
                <div class="stat-label">Time</div>
            </div>
        </div>
        
        <div class="difficulty-selector">
            <button class="difficulty-btn" data-difficulty="easy">Easy (1-50)</button>
            <button class="difficulty-btn active" data-difficulty="normal">Normal (1-100)</button>
            <button class="difficulty-btn" data-difficulty="hard">Hard (1-200)</button>
        </div>
        
        <div class="progress-bar">
            <div class="progress" id="progress-bar"></div>
        </div>
        
        <div class="anime-character" id="character">(^_^)</div>
        
        <div class="game-area">
            <div class="input-group">
                <input type="number" id="guess-input" min="1" max="100" placeholder="Enter number">
                <button id="guess-btn">Guess! <i class="fas fa-bullseye"></i></button>
            </div>
            
            <div id="message" class="message">
                Select difficulty and guess a number!
            </div>
            
            <div class="action-buttons">
                <button id="hint-btn" class="action-btn">Get Hint <i class="fas fa-lightbulb"></i></button>
                <button id="new-game-btn" class="action-btn">New Game <i class="fas fa-redo"></i></button>
            </div>
        </div>
        
        <div class="history-container">
            <div class="history-title">Your Guesses</div>
            <div class="history-list" id="history-list">
                <!-- Guess history will appear here -->
            </div>
        </div>
        
        <div class="instructions">
            <h3><i class="fas fa-info-circle"></i> How to Play:</h3>
            <ul>
                <li>Select a difficulty level to change the number range</li>
                <li>Guess the secret number in the fewest attempts possible</li>
                <li>Earn more points for fewer attempts and faster times</li>
                <li>Use hints if you get stuck (costs points)</li>
                <li>Track your progress with the guess history</li>
            </ul>
        </div>
        
        <footer>
            <i class="fas fa-heart"></i> Created with Flask and Anime Style <i class="fas fa-heart"></i>
        </footer>
    </div>

    <script>
        let sessionId = Math.random().toString(36).substring(2);
        let gameTimer;
        let seconds = 0;
        
        // DOM elements
        const guessInput = document.getElementById('guess-input');
        const guessBtn = document.getElementById('guess-btn');
        const newGameBtn = document.getElementById('new-game-btn');
        const hintBtn = document.getElementById('hint-btn');
        const messageElement = document.getElementById('message');
        const attemptsDisplay = document.getElementById('attempts-display');
        const scoreDisplay = document.getElementById('score-display');
        const rangeDisplay = document.getElementById('range-display');
        const timeDisplay = document.getElementById('time-display');
        const historyList = document.getElementById('history-list');
        const characterElement = document.getElementById('character');
        const progressBar = document.getElementById('progress-bar');
        const difficultyBtns = document.querySelectorAll('.difficulty-btn');
        
        // Event listeners
        guessBtn.addEventListener('click', makeGuess);
        newGameBtn.addEventListener('click', startNewGame);
        hintBtn.addEventListener('click', getHint);
        guessInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                makeGuess();
            }
        });
        
        difficultyBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                difficultyBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                changeDifficulty(this.dataset.difficulty);
            });
        });
        
        // Game functions
        function startTimer() {
            clearInterval(gameTimer);
            seconds = 0;
            gameTimer = setInterval(() => {
                seconds++;
                timeDisplay.textContent = seconds + 's';
            }, 1000);
        }
        
        function stopTimer() {
            clearInterval(gameTimer);
        }
        
        function makeGuess() {
            const guess = parseInt(guessInput.value);
            const max = parseInt(guessInput.max);
            
            if (isNaN(guess) || guess < 1 || guess > max) {
                alert('Please enter a valid number between 1 and ' + max + '!');
                return;
            }
            
            fetch('/guess', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    guess: guess,
                    session_id: sessionId
                }),
            })
            .then(response => response.json())
            .then(data => {
                updateGameState(data);
            })
            .catch(error => {
                console.error('Error:', error);
            });
            
            guessInput.value = '';
            guessInput.focus();
        }
        
        function startNewGame() {
            fetch('/new_game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId
                }),
            })
            .then(response => response.json())
            .then(data => {
                updateGameState(data);
                startTimer();
                guessInput.focus();
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
        
        function getHint() {
            fetch('/hint', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.hint) {
                    messageElement.textContent = data.hint;
                    messageElement.className = 'message';
                    updateScore(data.score);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
        
        function changeDifficulty(difficulty) {
            fetch('/change_difficulty', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    difficulty: difficulty
                }),
            })
            .then(response => response.json())
            .then(data => {
                rangeDisplay.textContent = data.range;
                guessInput.min = data.min;
                guessInput.max = data.max;
                guessInput.placeholder = 'Enter number (' + data.range + ')';
                messageElement.textContent = 'Difficulty changed to ' + difficulty + '. Range is now ' + data.range + '.';
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
        
        function updateGameState(data) {
            messageElement.textContent = data.message;
            messageElement.className = 'message ' + (data.result || '');
            
            attemptsDisplay.textContent = data.attempts || 0;
            updateScore(data.score);
            
            if (data.range) {
                rangeDisplay.textContent = data.range;
                guessInput.min = data.min;
                guessInput.max = data.max;
            }
            
            if (data.game_over) {
                guessBtn.disabled = true;
                stopTimer();
                if (data.result === 'correct') {
                    characterElement.textContent = '(★ω★)';
                    confettiEffect();
                } else {
                    characterElement.textContent = '(>_<)';
                }
            } else {
                guessBtn.disabled = false;
                if (data.result === 'low') {
                    characterElement.textContent = '(´･ω･`)';
                } else if (data.result === 'high') {
                    characterElement.textContent = '(╯°□°）╯';
                } else {
                    characterElement.textContent = '(^_^)';
                }
            }
            
            // Update progress bar
            if (data.max_attempts && data.attempts) {
                const progress = Math.min(100, (data.attempts / data.max_attempts) * 100);
                progressBar.style.width = progress + '%';
            }
            
            // Update history
            if (data.guess_history) {
                updateHistory(data.guess_history);
            }
        }
        
        function updateScore(score) {
            if (score !== undefined) {
                scoreDisplay.textContent = score;
            }
        }
        
        function updateHistory(history) {
            historyList.innerHTML = '';
            history.forEach(item => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item ' + item.result;
                historyItem.textContent = item.guess;
                historyList.appendChild(historyItem);
            });
            
            // Scroll to bottom
            historyList.scrollTop = historyList.scrollHeight;
        }
        
        function confettiEffect() {
            // Simple confetti effect
            const colors = ['#ff6b93', '#6bc6ff', '#ffd166', '#8ac926'];
            for (let i = 0; i < 50; i++) {
                setTimeout(() => {
                    const confetti = document.createElement('div');
                    confetti.innerHTML = '•';
                    confetti.style.position = 'fixed';
                    confetti.style.left = Math.random() * 100 + 'vw';
                    confetti.style.top = '-10px';
                    confetti.style.color = colors[Math.floor(Math.random() * colors.length)];
                    confetti.style.fontSize = (Math.random() * 20 + 10) + 'px';
                    confetti.style.zIndex = '9999';
                    confetti.style.pointerEvents = 'none';
                    document.body.appendChild(confetti);
                    
                    // Animate
                    const animation = confetti.animate([
                        { transform: 'translateY(0) rotate(0deg)', opacity: 1 },
                        { transform: 'translateY(' + window.innerHeight + 'px) rotate(' + Math.random() * 360 + 'deg)', opacity: 0 }
                    ], {
                        duration: Math.random() * 3000 + 2000,
                        easing: 'cubic-bezier(0.215, 0.61, 0.355, 1)'
                    });
                    
                    animation.onfinish = () => confetti.remove();
                }, i * 100);
            }
        }
        
        // Initialize game
        startNewGame();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/guess', methods=['POST'])
def make_guess():
    data = request.json
    guess = int(data['guess'])
    session_id = data.get('session_id', 'default')
    
    game = get_game_state(session_id)
    game.attempts += 1
    
    # Add to guess history
    if guess < game.number_to_guess:
        result = 'low'
    elif guess > game.number_to_guess:
        result = 'high'
    else:
        result = 'correct'
    
    game.guess_history.append({'guess': guess, 'result': result})
    
    if guess == game.number_to_guess:
        game.game_over = True
        game.score = calculate_score(game)
        return jsonify({
            'result': 'correct',
            'message': f'🎉 Correct! You guessed it in {game.attempts} attempts! 🎉',
            'attempts': game.attempts,
            'game_over': True,
            'score': game.score,
            'guess_history': game.guess_history
        })
    elif guess < game.number_to_guess:
        # Check if game over due to max attempts
        if game.attempts >= game.max_attempts:
            game.game_over = True
            game.score = calculate_score(game)
            return jsonify({
                'result': 'game-over',
                'message': f'Game Over! The number was {game.number_to_guess}.',
                'attempts': game.attempts,
                'game_over': True,
                'score': game.score,
                'guess_history': game.guess_history
            })
        
        return jsonify({
            'result': 'low',
            'message': 'Too low! Try a higher number! 📈',
            'attempts': game.attempts,
            'game_over': False,
            'max_attempts': game.max_attempts,
            'guess_history': game.guess_history
        })
    else:
        # Check if game over due to max attempts
        if game.attempts >= game.max_attempts:
            game.game_over = True
            game.score = calculate_score(game)
            return jsonify({
                'result': 'game-over',
                'message': f'Game Over! The number was {game.number_to_guess}.',
                'attempts': game.attempts,
                'game_over': True,
                'score': game.score,
                'guess_history': game.guess_history
            })
        
        return jsonify({
            'result': 'high',
            'message': 'Too high! Try a lower number! 📉',
            'attempts': game.attempts,
            'game_over': False,
            'max_attempts': game.max_attempts,
            'guess_history': game.guess_history
        })

@app.route('/new_game', methods=['POST'])
def new_game():
    data = request.json
    session_id = data.get('session_id', 'default')
    
    # Create a new game
    games[session_id] = GameState()
    game = games[session_id]
    
    # Set range based on difficulty
    if game.difficulty == "easy":
        range_text = "1-50"
        min_val, max_val = 1, 50
    elif game.difficulty == "hard":
        range_text = "1-200"
        min_val, max_val = 1, 200
    else:
        range_text = "1-100"
        min_val, max_val = 1, 100
    
    return jsonify({
        'message': f'New game started! Guess a number between {range_text}!',
        'attempts': 0,
        'game_over': False,
        'range': range_text,
        'min': min_val,
        'max': max_val,
        'score': 0,
        'max_attempts': game.max_attempts
    })

@app.route('/hint', methods=['POST'])
def get_hint():
    data = request.json
    session_id = data.get('session_id', 'default')
    
    game = get_game_state(session_id)
    
    # Deduct points for hint
    hint_cost = 50
    game.score = max(0, (game.score or 0) - hint_cost)
    
    # Generate hint
    hints = [
        f"The number is {'even' if game.number_to_guess % 2 == 0 else 'odd'}.",
        f"The number is between {max(1, game.number_to_guess-10)} and {min(game.number_to_guess+10, 100 if game.difficulty == 'normal' else 50 if game.difficulty == 'easy' else 200)}.",
        f"The number has a {'' if game.number_to_guess < 10 else 'two-'}digit.",
        f"The sum of digits is {sum(int(d) for d in str(game.number_to_guess))}." if game.number_to_guess >= 10 else "The number is a single digit."
    ]
    
    hint = random.choice(hints)
    
    return jsonify({
        'hint': f"💡 Hint: {hint} (Cost: {hint_cost} points)",
        'score': game.score
    })

@app.route('/change_difficulty', methods=['POST'])
def change_difficulty():
    data = request.json
    session_id = data.get('session_id', 'default')
    difficulty = data.get('difficulty', 'normal')
    
    game = get_game_state(session_id)
    game.difficulty = difficulty
    
    # Adjust game parameters based on difficulty
    if difficulty == "easy":
        game.number_to_guess = random.randint(1, 50)
        game.max_attempts = 8
        range_text = "1-50"
        min_val, max_val = 1, 50
    elif difficulty == "hard":
        game.number_to_guess = random.randint(1, 200)
        game.max_attempts = 12
        range_text = "1-200"
        min_val, max_val = 1, 200
    else:
        game.number_to_guess = random.randint(1, 100)
        game.max_attempts = 10
        range_text = "1-100"
        min_val, max_val = 1, 100
    
    # Reset game state
    game.attempts = 0
    game.game_over = False
    game.guess_history = []
    game.start_time = time.time()
    game.score = 0
    
    return jsonify({
        'range': range_text,
        'min': min_val,
        'max': max_val,
        'message': f'Difficulty changed to {difficulty}.'
    })

if __name__ == '__main__':
    app.run(debug=True)