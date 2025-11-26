# Atlas Game - Web Version
import difflib
from flask import Flask, render_template, request, jsonify, session
import random
import os

app = Flask(__name__)
app.secret_key = 'atlas_game_secret_key_2024'

# Basic set of known real countries and cities (expanded list)
PLACES = {
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria",
    "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi",
    "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China",
    "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
    "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt",
    "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland", "France",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau",
    "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel",
    "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos",
    "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar",
    "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico",
    "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia",
    "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea",
    "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay",
    "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
    "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia",
    "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden",
    "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga",
    "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine",
    "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan",
    "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe",
    # Major cities
    "Paris", "London", "Tokyo", "Beijing", "Moscow", "Cairo", "Rome", "Berlin", "Madrid", "Sydney",
    "Toronto", "Mumbai", "Delhi", "Shanghai", "Seoul", "Jakarta", "Bangkok", "Istanbul", "Lisbon", "Vienna",
    "Prague", "Athens", "Dublin", "Stockholm", "Oslo", "Helsinki", "Warsaw", "Budapest", "Amsterdam", "Brussels",
    "Vancouver", "Montreal", "Rio de Janeiro", "Sao Paulo", "Buenos Aires", "Lima", "Santiago", "Bogota",
    "Mexico City", "Los Angeles", "New York", "Chicago", "Miami", "Dubai", "Singapore", "Hong Kong", "Bangkok"
}

# Convert all to lowercase for consistent comparison
PLACES_LOWER = {place.lower() for place in PLACES}
PLACES_DISPLAY = {place.lower(): place for place in PLACES}

def get_last_letter(word):
    """Return the last alphabetic character."""
    for ch in reversed(word.lower()):
        if ch.isalpha():
            return ch
    return ""

def is_valid_place(word):
    """Check if the entered place is valid (exists in our dataset)."""
    w = word.lower().strip()
    return w in PLACES_LOWER

def get_suggestion(word):
    """Get a spelling suggestion for the entered word."""
    w = word.lower().strip()
    close = difflib.get_close_matches(w, PLACES_LOWER, n=1, cutoff=0.8)
    return close[0] if close else None

def get_valid_next_places(used_places, required_letter):
    """Get list of valid next places for the given letter."""
    return [PLACES_DISPLAY[place] for place in PLACES_LOWER 
            if place[0] == required_letter and place not in used_places]

@app.route('/')
def index():
    """Main game page."""
    session.clear()
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_game():
    """Start a new game."""
    session.clear()
    session['used_places'] = []
    session['current_player'] = 1
    session['game_started'] = True
    session['scores'] = {1: 0, 2: 0}
    
    return jsonify({
        'status': 'ready',
        'message': 'Game started! Player 1, enter any place to begin.',
        'currentPlayer': 1
    })

@app.route('/play', methods=['POST'])
def play_turn():
    """Process a player's move."""
    if not session.get('game_started'):
        return jsonify({'error': 'Game not started'}), 400
    
    data = request.get_json()
    word = data.get('word', '').strip()
    current_player = session['current_player']
    used_places = session['used_places']
    
    # Validation
    if not word:
        return jsonify({'error': 'Please enter a place name'}), 400
    
    # Check if it's the first move
    if used_places:
        last_place = used_places[-1]
        required_letter = get_last_letter(last_place)
        if word[0].lower() != required_letter:
            return jsonify({
                'error': f"Must start with '{required_letter.upper()}'"
            }), 400
    
    # Check if valid place
    word_lower = word.lower()
    if not is_valid_place(word):
        suggestion = get_suggestion(word)
        if suggestion:
            return jsonify({
                'error': f"Place not recognized. Did you mean '{PLACES_DISPLAY[suggestion]}'?"
            }), 400
        else:
            return jsonify({
                'error': 'Place not recognized. Please enter a real country or city.'
            }), 400
    
    # Check if already used
    if word_lower in used_places:
        return jsonify({
            'error': 'This place has already been used. Try another one.'
        }), 400
    
    # Valid move - update game state
    used_places.append(word_lower)
    session['used_places'] = used_places
    session['scores'][current_player] += 1
    
    # Prepare response
    next_letter = get_last_letter(word)
    next_player = 2 if current_player == 1 else 1
    session['current_player'] = next_player
    
    # Check if game should end (no more valid moves)
    valid_next_places = get_valid_next_places(used_places, next_letter)
    
    response = {
        'success': True,
        'word': PLACES_DISPLAY.get(word_lower, word.title()),
        'nextLetter': next_letter.upper(),
        'nextPlayer': next_player,
        'scores': session['scores'],
        'usedCount': len(used_places),
        'gameOver': len(valid_next_places) == 0
    }
    
    if response['gameOver']:
        winner = max(session['scores'], key=session['scores'].get)
        response['winner'] = winner
        response['message'] = f'Game Over! Player {winner} wins!'
    
    return jsonify(response)

@app.route('/hint', methods=['GET'])
def get_hint():
    """Get a hint for the next move."""
    if not session.get('game_started') or not session.get('used_places'):
        return jsonify({'error': 'No game in progress'}), 400
    
    used_places = session['used_places']
    last_place = used_places[-1]
    required_letter = get_last_letter(last_place)
    
    valid_places = get_valid_next_places(used_places, required_letter)
    
    if valid_places:
        hint = random.choice(valid_places[:5])  # Pick from first 5 to avoid giving away too many
        return jsonify({
            'hint': f"Try a place like: {hint}",
            'remaining': len(valid_places)
        })
    else:
        return jsonify({
            'hint': 'No valid moves remaining!',
            'remaining': 0
        })

@app.route('/state', methods=['GET'])
def get_game_state():
    """Get current game state."""
    if not session.get('game_started'):
        return jsonify({'gameStarted': False})
    
    used_places = session.get('used_places', [])
    current_player = session.get('current_player', 1)
    
    state = {
        'gameStarted': True,
        'currentPlayer': current_player,
        'scores': session.get('scores', {1: 0, 2: 0}),
        'usedCount': len(used_places),
        'usedPlaces': [PLACES_DISPLAY[place] for place in used_places[-10:]]  # Last 10 places
    }
    
    if used_places:
        last_place = used_places[-1]
        state['lastPlace'] = PLACES_DISPLAY[last_place]
        state['nextLetter'] = get_last_letter(last_place).upper()
    
    return jsonify(state)

def create_html_template():
    """Create the HTML template file without Unicode encoding issues."""
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Atlas Game</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50, #34495e);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .game-area {
            padding: 30px;
        }
        
        .rules {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
        
        .rules h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }
        
        .rules ul {
            list-style-position: inside;
            color: #555;
        }
        
        .rules li {
            margin-bottom: 5px;
        }
        
        .game-controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
        }
        
        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-2px);
        }
        
        .btn-secondary {
            background: #e9ecef;
            color: #495057;
        }
        
        .btn-secondary:hover {
            background: #dee2e6;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-success:hover {
            background: #218838;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        input[type="text"] {
            width: 100%;
            padding: 15px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .game-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .info-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .info-card h3 {
            color: #495057;
            margin-bottom: 10px;
        }
        
        .info-card .value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        
        .player-turn {
            background: #fff3cd;
            border: 2px solid #ffeaa7;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
            font-weight: bold;
        }
        
        .history {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .history h3 {
            margin-bottom: 10px;
            color: #495057;
        }
        
        .history-item {
            padding: 8px 12px;
            margin-bottom: 5px;
            background: white;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .alert-success {
            background: #d1edff;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .scores {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .score-card {
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            background: #f8f9fa;
        }
        
        .score-card.active {
            background: #667eea;
            color: white;
        }
        
        .score-card .player {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .score-card .score {
            font-size: 1.5em;
            font-weight: bold;
        }
        
        .game-over {
            background: #d4edda;
            border: 2px solid #c3e6cb;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
            display: none;
        }
        
        .game-over h2 {
            color: #155724;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌍 Atlas Game</h1>
            <div class="subtitle">Test your geography knowledge!</div>
        </div>
        
        <div class="game-area">
            <div class="rules">
                <h3>📋 Game Rules</h3>
                <ul>
                    <li>Players take turns naming real countries or cities</li>
                    <li>Each new place must start with the last letter of the previous one</li>
                    <li>No repeating places allowed</li>
                    <li>The game continues until no valid moves remain</li>
                </ul>
            </div>
            
            <div class="game-controls">
                <button class="btn-primary" onclick="startGame()">🎮 Start New Game</button>
                <button class="btn-secondary" onclick="getHint()">💡 Get Hint</button>
            </div>
            
            <div id="alert" class="alert"></div>
            <div id="gameOver" class="game-over"></div>
            
            <div class="scores" id="scoresContainer" style="display: none;">
                <div class="score-card" id="player1Score">
                    <div class="player">Player 1</div>
                    <div class="score">0</div>
                </div>
                <div class="score-card" id="player2Score">
                    <div class="player">Player 2</div>
                    <div class="score">0</div>
                </div>
            </div>
            
            <div class="player-turn" id="playerTurn" style="display: none;">
                Player 1's turn - Enter any place to start
            </div>
            
            <div class="input-group">
                <input type="text" id="placeInput" placeholder="Enter a country or city..." onkeypress="handleKeyPress(event)">
                <button class="btn-success" onclick="submitPlace()" style="width: 100%; margin-top: 10px;">✅ Submit</button>
            </div>
            
            <div class="game-info">
                <div class="info-card">
                    <h3>Next Letter</h3>
                    <div class="value" id="nextLetter">-</div>
                </div>
                <div class="info-card">
                    <h3>Places Used</h3>
                    <div class="value" id="usedCount">0</div>
                </div>
            </div>
            
            <div class="history">
                <h3>Recent Places</h3>
                <div id="historyList"></div>
            </div>
        </div>
    </div>

    <script>
        let currentGameState = {};
        
        function showAlert(message, type = 'error') {
            const alert = document.getElementById('alert');
            alert.textContent = message;
            alert.className = `alert alert-${type}`;
            alert.style.display = 'block';
            
            setTimeout(() => {
                alert.style.display = 'none';
            }, 5000);
        }
        
        function showGameOver(message) {
            const gameOver = document.getElementById('gameOver');
            gameOver.innerHTML = `<h2>🎉 ${message}</h2>`;
            gameOver.style.display = 'block';
        }
        
        function startGame() {
            fetch('/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ready') {
                    currentGameState = data;
                    updateUI();
                    document.getElementById('placeInput').focus();
                    document.getElementById('gameOver').style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Failed to start game');
            });
        }
        
        function submitPlace() {
            const input = document.getElementById('placeInput');
            const word = input.value.trim();
            
            if (!word) {
                showAlert('Please enter a place name');
                return;
            }
            
            fetch('/play', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ word: word })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentGameState = data;
                    updateUI();
                    input.value = '';
                    
                    if (data.gameOver) {
                        showGameOver(data.message);
                    }
                } else {
                    showAlert(data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Failed to submit place');
            });
        }
        
        function getHint() {
            if (!currentGameState.gameStarted) {
                showAlert('Please start a game first');
                return;
            }
            
            fetch('/hint')
            .then(response => response.json())
            .then(data => {
                if (data.hint) {
                    showAlert(data.hint, 'success');
                } else {
                    showAlert(data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Failed to get hint');
            });
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                submitPlace();
            }
        }
        
        function updateUI() {
            // Update scores
            const scoresContainer = document.getElementById('scoresContainer');
            const player1Score = document.getElementById('player1Score');
            const player2Score = document.getElementById('player2Score');
            const playerTurn = document.getElementById('playerTurn');
            const nextLetter = document.getElementById('nextLetter');
            const usedCount = document.getElementById('usedCount');
            const historyList = document.getElementById('historyList');
            
            if (currentGameState.scores) {
                scoresContainer.style.display = 'grid';
                player1Score.querySelector('.score').textContent = currentGameState.scores[1];
                player2Score.querySelector('.score').textContent = currentGameState.scores[2];
                
                // Highlight active player
                player1Score.classList.toggle('active', currentGameState.nextPlayer === 1);
                player2Score.classList.toggle('active', currentGameState.nextPlayer === 2);
            }
            
            if (currentGameState.nextPlayer) {
                playerTurn.style.display = 'block';
                const letterInfo = currentGameState.nextLetter ? 
                    ` starting with '${currentGameState.nextLetter}'` : '';
                playerTurn.textContent = `Player ${currentGameState.nextPlayer}'s turn${letterInfo}`;
            }
            
            if (currentGameState.nextLetter) {
                nextLetter.textContent = currentGameState.nextLetter;
            }
            
            if (currentGameState.usedCount !== undefined) {
                usedCount.textContent = currentGameState.usedCount;
            }
            
            // Update history
            if (currentGameState.usedPlaces) {
                historyList.innerHTML = currentGameState.usedPlaces
                    .map(place => `<div class="history-item">${place}</div>`)
                    .join('');
            }
            
            // Auto-scroll history to bottom
            historyList.scrollTop = historyList.scrollHeight;
        }
        
        // Poll for game state updates
        function pollGameState() {
            fetch('/state')
            .then(response => response.json())
            .then(data => {
                if (data.gameStarted) {
                    currentGameState = { ...currentGameState, ...data };
                    updateUI();
                }
            })
            .catch(error => console.error('Error polling game state:', error));
        }
        
        // Poll every 2 seconds
        setInterval(pollGameState, 2000);
        
        // Initialize
        document.getElementById('placeInput').focus();
    </script>
</body>
</html>'''
    
    # Write with proper encoding
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)

if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template file
    create_html_template()
    
    print("Starting Atlas Game Web Server...")
    print("Open http://localhost:5000 in your browser to play!")
    app.run(debug=True, host='0.0.0.0', port=5000)