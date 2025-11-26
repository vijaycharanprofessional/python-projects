from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session
import csv
import os
import secrets
import string
import re
import hashlib
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production!

# File paths
USERS_FILE = 'users.csv'
PASSWORDS_DIR = 'user_passwords'

# Ensure directories exist
os.makedirs(PASSWORDS_DIR, exist_ok=True)

# HTML template as a string
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PassGen Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; padding: 20px; 
        }
        .container { 
            max-width: 800px; margin: 0 auto; background: white; 
            border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.1); 
            overflow: hidden; 
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; padding: 30px; text-align: center; 
            position: relative;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .user-info { 
            position: absolute; top: 20px; right: 20px; 
            background: rgba(255,255,255,0.2); padding: 10px 15px; 
            border-radius: 20px; font-size: 0.9em;
        }
        .content { padding: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: 600; color: #333; }
        input, select, textarea { 
            width: 100%; padding: 12px; border: 2px solid #e1e5e9; 
            border-radius: 8px; font-size: 16px; transition: border-color 0.3s; 
        }
        input:focus, select:focus, textarea:focus { 
            outline: none; border-color: #667eea; 
        }
        .password-display { 
            background: #f8f9fa; border: 2px solid #e1e5e9; border-radius: 8px; 
            padding: 15px; margin: 20px 0; font-family: 'Courier New', monospace; 
            font-size: 18px; text-align: center; position: relative; 
        }
        .strength-indicator { 
            display: inline-block; padding: 5px 15px; border-radius: 20px; 
            color: white; font-weight: bold; margin-left: 10px; 
        }
        .strength-weak { background: #e74c3c; }
        .strength-medium { background: #f39c12; }
        .strength-strong { background: #27ae60; }
        .btn { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; border: none; padding: 15px 30px; border-radius: 8px; 
            font-size: 16px; font-weight: 600; cursor: pointer; transition: transform 0.2s; 
            width: 100%; margin: 5px 0; 
        }
        .btn:hover { transform: translateY(-2px); }
        .btn-secondary { background: #6c757d; }
        .btn-success { background: #28a745; }
        .btn-danger { background: #dc3545; }
        .btn-copy { background: #3498db; width: auto; padding: 10px 20px; }
        .suggestions { 
            background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; 
            padding: 15px; margin: 15px 0; 
        }
        .history-section { 
            margin-top: 30px; border-top: 2px solid #e1e5e9; padding-top: 20px; 
        }
        .history-item { 
            background: #f8f9fa; border: 1px solid #e1e5e9; border-radius: 8px; 
            padding: 15px; margin: 10px 0; 
        }
        .tab-container { 
            display: flex; margin-bottom: 20px; border-bottom: 2px solid #e1e5e9; 
            flex-wrap: wrap;
        }
        .tab { 
            padding: 15px 30px; cursor: pointer; border-bottom: 3px solid transparent; 
            transition: all 0.3s; 
        }
        .tab.active { border-bottom-color: #667eea; color: #667eea; font-weight: 600; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .password-options { 
            display: grid; grid-template-columns: 1fr 1fr; gap: 15px; 
            margin-bottom: 20px; 
        }
        .auth-container {
            max-width: 400px;
        }
        .message {
            padding: 10px; margin: 10px 0; border-radius: 5px;
        }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .login-links { text-align: center; margin-top: 20px; }
        @media (max-width: 600px) { 
            .password-options { grid-template-columns: 1fr; } 
            .container { margin: 10px; } 
            .tab { padding: 10px 15px; }
        }
    </style>
</head>
<body>
    <div class="container" id="main-container">
        {% if not session.user %}
        <!-- Login/Signup Section -->
        <div class="header">
            <h1>🔐 Secure Password Manager</h1>
            <p>Sign up or login to manage your passwords securely</p>
        </div>
        <div class="content auth-container">
            <div id="login-section">
                <h2>Login</h2>
                <div id="login-message"></div>
                <form id="loginForm">
                    <div class="form-group">
                        <label for="login_username">Username:</label>
                        <input type="text" id="login_username" required>
                    </div>
                    <div class="form-group">
                        <label for="login_password">Password:</label>
                        <input type="password" id="login_password" required>
                    </div>
                    <button type="submit" class="btn">Login</button>
                </form>
                <div class="login-links">
                    <p>Don't have an account? <a href="#" onclick="showSignup()">Sign up here</a></p>
                </div>
            </div>

            <div id="signup-section" style="display: none;">
                <h2>Sign Up</h2>
                <div id="signup-message"></div>
                <form id="signupForm">
                    <div class="form-group">
                        <label for="signup_username">Username:</label>
                        <input type="text" id="signup_username" required>
                    </div>
                    <div class="form-group">
                        <label for="signup_password">Password:</label>
                        <input type="password" id="signup_password" required>
                    </div>
                    <div class="form-group">
                        <label for="confirm_password">Confirm Password:</label>
                        <input type="password" id="confirm_password" required>
                    </div>
                    <button type="submit" class="btn btn-success">Sign Up</button>
                </form>
                <div class="login-links">
                    <p>Already have an account? <a href="#" onclick="showLogin()">Login here</a></p>
                </div>
            </div>
        </div>
        {% else %}
        <!-- Main Application -->
        <div class="header">
            <h1>🔐 Password Manager</h1>
            <p>Welcome back, {{ session.user }}!</p>
            <div class="user-info">
                User: {{ session.user }} | 
                <a href="#" onclick="logout()" style="color: white; margin-left: 10px;">Logout</a>
            </div>
        </div>

        <div class="content">
            <div class="tab-container">
                <div class="tab active" onclick="switchTab('generate')">Generate Password</div>
                <div class="tab" onclick="switchTab('check')">Check Strength</div>
                <div class="tab" onclick="switchTab('history')">My Passwords</div>
                <div class="tab" onclick="switchTab('saved')">Saved Passwords</div>
            </div>

            <!-- Generate Password Tab -->
            <div id="generate-tab" class="tab-content active">
                <form id="passwordForm">
                    <div class="form-group">
                        <label for="website_app">Website/Application:</label>
                        <input type="text" id="website_app" placeholder="e.g., Gmail, Facebook, Bank" required>
                    </div>

                    <div class="form-group">
                        <label for="username">Username/Email:</label>
                        <input type="text" id="username" placeholder="Your username or email" required>
                    </div>

                    <div class="form-group">
                        <label for="purpose">Purpose/Description:</label>
                        <textarea id="purpose" rows="3" placeholder="What will this password be used for?" required></textarea>
                    </div>

                    <div class="password-options">
                        <div class="form-group">
                            <label for="strength">Password Strength:</label>
                            <select id="strength">
                                <option value="weak">Weak</option>
                                <option value="medium" selected>Medium</option>
                                <option value="strong">Strong</option>
                            </select>
                        </div>

                        <div class="form-group">
                            <label for="length">Password Length:</label>
                            <input type="number" id="length" value="12" min="8" max="32" required>
                        </div>
                    </div>

                    <button type="submit" class="btn">Generate Secure Password</button>
                    <button type="button" class="btn btn-secondary" onclick="savePassword()" id="saveBtn" style="display: none;">Save Password</button>
                </form>

                <div id="passwordResult" style="display: none;">
                    <div class="password-display">
                        <span id="generatedPassword"></span>
                        <span id="passwordStrength" class="strength-indicator"></span>
                    </div>
                    <button class="btn btn-copy" onclick="copyPassword()">Copy Password</button>
                    <div id="suggestions" class="suggestions" style="display: none;"></div>
                </div>
            </div>

            <!-- Check Strength Tab -->
            <div id="check-tab" class="tab-content">
                <div class="form-group">
                    <label for="checkPassword">Enter Password to Check:</label>
                    <input type="text" id="checkPassword" placeholder="Enter your password">
                    <button class="btn" onclick="checkPasswordStrength()">Check Strength</button>
                </div>
                <div id="checkResult" style="display: none;">
                    <div class="password-display">
                        Strength: <span id="checkedStrength" class="strength-indicator"></span>
                    </div>
                    <div id="strengthSuggestions" class="suggestions"></div>
                </div>
            </div>

            <!-- History Tab -->
            <div id="history-tab" class="tab-content">
                <button class="btn" onclick="loadHistory()">Load My Password History</button>
                <div id="historyList" class="history-section"></div>
            </div>

            <!-- Saved Passwords Tab -->
            <div id="saved-tab" class="tab-content">
                <button class="btn" onclick="loadSavedPasswords()">Load Saved Passwords</button>
                <div id="savedPasswordsList" class="history-section"></div>
            </div>
        </div>
        {% endif %}
    </div>

    <script>
        {% if not session.user %}
        function showSignup() {
            document.getElementById('login-section').style.display = 'none';
            document.getElementById('signup-section').style.display = 'block';
        }

        function showLogin() {
            document.getElementById('signup-section').style.display = 'block';
            document.getElementById('login-section').style.display = 'none';
        }

        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            login();
        });

        document.getElementById('signupForm').addEventListener('submit', function(e) {
            e.preventDefault();
            signup();
        });

        function login() {
            const username = document.getElementById('login_username').value;
            const password = document.getElementById('login_password').value;

            fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, password: password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    document.getElementById('login-message').innerHTML = 
                        `<div class="message error">${data.message}</div>`;
                }
            });
        }

        function signup() {
            const username = document.getElementById('signup_username').value;
            const password = document.getElementById('signup_password').value;
            const confirmPassword = document.getElementById('confirm_password').value;

            if (password !== confirmPassword) {
                document.getElementById('signup-message').innerHTML = 
                    '<div class="message error">Passwords do not match!</div>';
                return;
            }

            fetch('/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: username, password: password })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('signup-message').innerHTML = 
                        `<div class="message success">${data.message}</div>`;
                    setTimeout(() => showLogin(), 2000);
                } else {
                    document.getElementById('signup-message').innerHTML = 
                        `<div class="message error">${data.message}</div>`;
                }
            });
        }
        {% else %}
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }

        function logout() {
            fetch('/logout')
            .then(() => window.location.reload());
        }

        let currentGeneratedPassword = '';

        document.getElementById('passwordForm').addEventListener('submit', function(e) {
            e.preventDefault();
            generatePassword();
        });

        function generatePassword() {
            const formData = {
                website_app: document.getElementById('website_app').value,
                username: document.getElementById('username').value,
                purpose: document.getElementById('purpose').value,
                strength: document.getElementById('strength').value,
                length: document.getElementById('length').value
            };

            fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                currentGeneratedPassword = data.password;
                document.getElementById('generatedPassword').textContent = data.password;
                const strengthElem = document.getElementById('passwordStrength');
                strengthElem.textContent = data.strength;
                strengthElem.className = 'strength-indicator strength-' + data.strength.toLowerCase();
                
                document.getElementById('passwordResult').style.display = 'block';
                document.getElementById('saveBtn').style.display = 'block';
                
                if (data.strength === 'Weak') {
                    document.getElementById('suggestions').innerHTML = `
                        <h4>💡 Suggestions to improve your password:</h4>
                        <ul>
                            <li>Use at least 12 characters</li>
                            <li>Include uppercase and lowercase letters</li>
                            <li>Add numbers and special characters</li>
                            <li>Avoid common words or patterns</li>
                        </ul>
                    `;
                    document.getElementById('suggestions').style.display = 'block';
                } else {
                    document.getElementById('suggestions').style.display = 'none';
                }
            });
        }

        function savePassword() {
            const formData = {
                website_app: document.getElementById('website_app').value,
                username: document.getElementById('username').value,
                purpose: document.getElementById('purpose').value,
                password: currentGeneratedPassword
            };

            fetch('/save-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.success) {
                    document.getElementById('saveBtn').style.display = 'none';
                }
            });
        }

        function checkPasswordStrength() {
            const password = document.getElementById('checkPassword').value;
            
            fetch('/check-strength', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: password })
            })
            .then(response => response.json())
            .then(data => {
                const strengthElem = document.getElementById('checkedStrength');
                strengthElem.textContent = data.strength;
                strengthElem.className = 'strength-indicator strength-' + data.strength.toLowerCase();
                
                let suggestionsHTML = '<h4>💡 Suggestions:</h4><ul>';
                data.suggestions.forEach(suggestion => {
                    suggestionsHTML += `<li>${suggestion}</li>`;
                });
                if (data.suggestions.length === 0) {
                    suggestionsHTML += '<li>Great! Your password is strong.</li>';
                }
                suggestionsHTML += '</ul>';
                
                document.getElementById('strengthSuggestions').innerHTML = suggestionsHTML;
                document.getElementById('checkResult').style.display = 'block';
            });
        }

        function loadHistory() {
            fetch('/history')
            .then(response => response.json())
            .then(data => {
                const historyList = document.getElementById('historyList');
                if (data.length === 0) {
                    historyList.innerHTML = '<p>No password history found.</p>';
                    return;
                }

                let historyHTML = '<h3>My Password History</h3>';
                data.slice(-10).reverse().forEach(item => {
                    historyHTML += `
                        <div class="history-item">
                            <strong>${item.Website_App || 'N/A'}</strong> - ${item.Username || 'N/A'}<br>
                            <small>Purpose: ${item.Purpose || 'N/A'}</small><br>
                            <small>Strength: <span class="strength-indicator strength-${item.Password_Strength?.toLowerCase() || 'medium'}">${item.Password_Strength || 'Unknown'}</span></small><br>
                            <small>Generated: ${item.Timestamp || 'Unknown'}</small>
                        </div>
                    `;
                });
                historyList.innerHTML = historyHTML;
            });
        }

        function loadSavedPasswords() {
            fetch('/saved-passwords')
            .then(response => response.json())
            .then(data => {
                const savedList = document.getElementById('savedPasswordsList');
                if (data.length === 0) {
                    savedList.innerHTML = '<p>No saved passwords found.</p>';
                    return;
                }

                let savedHTML = '<h3>My Saved Passwords</h3>';
                data.forEach(item => {
                    savedHTML += `
                        <div class="history-item">
                            <strong>${item.website_app}</strong> - ${item.username}<br>
                            <small>Purpose: ${item.purpose}</small><br>
                            <small>Password: <code>${item.password}</code></small><br>
                            <small>Saved: ${item.timestamp}</small><br>
                            <button class="btn btn-copy" onclick="copyText('${item.password}')">Copy</button>
                            <button class="btn btn-danger" onclick="deletePassword('${item.id}')">Delete</button>
                        </div>
                    `;
                });
                savedList.innerHTML = savedHTML;
            });
        }

        function copyPassword() {
            copyText(currentGeneratedPassword);
        }

        function copyText(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert('Copied to clipboard!');
            });
        }

        function deletePassword(passwordId) {
            if (confirm('Are you sure you want to delete this saved password?')) {
                fetch('/delete-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password_id: passwordId })
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    if (data.success) {
                        loadSavedPasswords();
                    }
                });
            }
        }
        {% endif %}
    </script>
</body>
</html>
'''

# Initialize users file
def init_users_file():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['username', 'password_hash'])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_file(username):
    return os.path.join(PASSWORDS_DIR, f'{username}_passwords.csv')

def get_user_saved_file(username):
    return os.path.join(PASSWORDS_DIR, f'{username}_saved.csv')

def init_user_files(username):
    # Initialize history file
    history_file = get_user_file(username)
    if not os.path.exists(history_file):
        with open(history_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Website_App', 'Username', 'Password_Strength', 'Purpose', 'Generated_Password'])
    
    # Initialize saved passwords file
    saved_file = get_user_saved_file(username)
    if not os.path.exists(saved_file):
        with open(saved_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'timestamp', 'website_app', 'username', 'purpose', 'password'])

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({'success': False, 'message': 'Please login first'})
        return f(*args, **kwargs)
    return decorated_function

# Password strength checker
def check_password_strength(password):
    score = 0
    
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'[0-9]', password):
        score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    
    if score <= 3:
        return "Weak"
    elif score <= 5:
        return "Medium"
    else:
        return "Strong"

# Generate password based on strength requirement
def generate_password(strength='medium', length=12):
    characters = string.ascii_letters + string.digits
    
    if strength == 'strong':
        characters += '!@#$%^&*()_+-=[]{}|;:,.<>?'
        length = max(length, 16)
    elif strength == 'weak':
        length = max(8, length)
        characters = string.ascii_letters + string.digits
    else:  # medium
        characters += '!@#$%^&*'
        length = max(12, length)
    
    while True:
        password = ''.join(secrets.choice(characters) for _ in range(length))
        
        if strength == 'strong':
            if (re.search(r'[a-z]', password) and 
                re.search(r'[A-Z]', password) and 
                re.search(r'[0-9]', password) and 
                re.search(r'[!@#$%^&*()_+-=[]{}|;:,.<>?]', password)):
                break
        elif strength == 'medium':
            if (re.search(r'[a-z]', password) and 
                re.search(r'[A-Z]', password) and 
                re.search(r'[0-9]', password)):
                break
        else:
            break
    
    return password

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})
    
    if len(username) < 3:
        return jsonify({'success': False, 'message': 'Username must be at least 3 characters'})
    
    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'})
    
    # Check if user already exists
    init_users_file()
    with open(USERS_FILE, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username:
                return jsonify({'success': False, 'message': 'Username already exists'})
    
    # Create new user
    with open(USERS_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([username, hash_password(password)])
    
    # Initialize user's password files
    init_user_files(username)
    
    return jsonify({'success': True, 'message': 'Account created successfully! You can now login.'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})
    
    # Check credentials
    init_users_file()
    with open(USERS_FILE, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['username'] == username and row['password_hash'] == hash_password(password):
                session['user'] = username
                return jsonify({'success': True, 'message': 'Login successful!'})
    
    return jsonify({'success': False, 'message': 'Invalid username or password'})

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
@login_required
def generate_password_route():
    data = request.json
    website_app = data.get('website_app', '')
    username = data.get('username', '')
    purpose = data.get('purpose', '')
    strength_preference = data.get('strength', 'medium')
    length = int(data.get('length', 12))
    
    generated_password = generate_password(strength_preference, length)
    actual_strength = check_password_strength(generated_password)
    
    # Save to user's history file
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    user_file = get_user_file(session['user'])
    
    with open(user_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, website_app, username, actual_strength, purpose, generated_password])
    
    return jsonify({
        'password': generated_password,
        'strength': actual_strength,
        'message': f'Password generated! Strength: {actual_strength}'
    })

@app.route('/save-password', methods=['POST'])
@login_required
def save_password():
    data = request.json
    website_app = data.get('website_app', '')
    username = data.get('username', '')
    purpose = data.get('purpose', '')
    password = data.get('password', '')
    
    if not all([website_app, username, purpose, password]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    # Save to user's saved passwords file
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    saved_file = get_user_saved_file(session['user'])
    
    # Generate unique ID
    password_id = secrets.token_hex(8)
    
    with open(saved_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([password_id, timestamp, website_app, username, purpose, password])
    
    return jsonify({'success': True, 'message': 'Password saved successfully!'})

@app.route('/check-strength', methods=['POST'])
@login_required
def check_strength():
    data = request.json
    password = data.get('password', '')
    
    strength = check_password_strength(password)
    suggestions = []
    
    if len(password) < 8:
        suggestions.append("Use at least 8 characters")
    if not re.search(r'[a-z]', password):
        suggestions.append("Add lowercase letters")
    if not re.search(r'[A-Z]', password):
        suggestions.append("Add uppercase letters")
    if not re.search(r'[0-9]', password):
        suggestions.append("Add numbers")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        suggestions.append("Add special characters")
    
    return jsonify({
        'strength': strength,
        'suggestions': suggestions
    })

@app.route('/history')
@login_required
def get_history():
    try:
        user_file = get_user_file(session['user'])
        passwords = []
        with open(user_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                passwords.append(dict(row))
        return jsonify(passwords)
    except FileNotFoundError:
        return jsonify([])

@app.route('/saved-passwords')
@login_required
def get_saved_passwords():
    try:
        saved_file = get_user_saved_file(session['user'])
        passwords = []
        with open(saved_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                passwords.append(dict(row))
        return jsonify(passwords)
    except FileNotFoundError:
        return jsonify([])

@app.route('/delete-password', methods=['POST'])
@login_required
def delete_password():
    data = request.json
    password_id = data.get('password_id', '')
    
    try:
        saved_file = get_user_saved_file(session['user'])
        passwords = []
        
        # Read all passwords
        with open(saved_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['id'] != password_id:
                    passwords.append(row)
        
        # Write back without the deleted password
        with open(saved_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['id', 'timestamp', 'website_app', 'username', 'purpose', 'password'])
            writer.writeheader()
            writer.writerows(passwords)
        
        return jsonify({'success': True, 'message': 'Password deleted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error deleting password: {str(e)}'})

if __name__ == '__main__':
    init_users_file()
    print("Secure Password Manager starting...")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True)