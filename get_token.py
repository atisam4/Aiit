from flask import Flask, request, render_template, redirect, url_for, session, flash
import requests
import secrets
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Facebook App credentials - replace these with your own
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://localhost:5001/callback')

def init_db():
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS tokens
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id TEXT,
         user_name TEXT,
         access_token TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.commit()
    conn.close()

def save_token(user_id, user_name, token):
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute('INSERT INTO tokens (user_id, user_name, access_token) VALUES (?, ?, ?)',
              (user_id, user_name, token))
    conn.commit()
    conn.close()

def get_user_tokens(user_id):
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute('SELECT * FROM tokens WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    tokens = c.fetchall()
    conn.close()
    return tokens

@app.route('/')
def home():
    auth_url = f"https://www.facebook.com/v15.0/dialog/oauth?client_id={FACEBOOK_APP_ID}&redirect_uri={REDIRECT_URI}&scope=public_profile,email,pages_messaging"
    return render_template('get_token.html', auth_url=auth_url)

@app.route('/callback')
def callback():
    error = request.args.get('error')
    if error:
        flash(f"Error: {error}", 'error')
        return redirect(url_for('home'))

    code = request.args.get('code')
    if not code:
        flash("No authorization code received", 'error')
        return redirect(url_for('home'))

    # Exchange code for access token
    token_url = "https://graph.facebook.com/v15.0/oauth/access_token"
    response = requests.get(token_url, params={
        'client_id': FACEBOOK_APP_ID,
        'client_secret': FACEBOOK_APP_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': code
    })

    if response.status_code != 200:
        flash(f"Error getting access token: {response.text}", 'error')
        return redirect(url_for('home'))

    data = response.json()
    access_token = data.get('access_token')
    
    # Get long-lived token
    long_lived_token_url = "https://graph.facebook.com/v15.0/oauth/access_token"
    response = requests.get(long_lived_token_url, params={
        'grant_type': 'fb_exchange_token',
        'client_id': FACEBOOK_APP_ID,
        'client_secret': FACEBOOK_APP_SECRET,
        'fb_exchange_token': access_token
    })

    if response.status_code != 200:
        flash(f"Error getting long-lived token: {response.text}", 'error')
        return redirect(url_for('home'))

    data = response.json()
    long_lived_token = data.get('access_token')

    # Get user info
    user_info_url = "https://graph.facebook.com/me"
    response = requests.get(user_info_url, params={
        'access_token': long_lived_token,
        'fields': 'id,name,email'
    })

    if response.status_code != 200:
        flash(f"Error getting user info: {response.text}", 'error')
        return redirect(url_for('home'))

    user_data = response.json()
    user_id = user_data.get('id')
    user_name = user_data.get('name')

    # Save token to database
    save_token(user_id, user_name, long_lived_token)

    return render_template('get_token.html', 
                         token=long_lived_token,
                         user_name=user_name)

@app.route('/tokens')
def view_tokens():
    if 'user_id' not in session:
        flash("Please log in first", 'error')
        return redirect(url_for('home'))
    
    tokens = get_user_tokens(session['user_id'])
    return render_template('tokens.html', tokens=tokens)

def validate_token(token):
    """Validate if the token is still active"""
    debug_url = "https://graph.facebook.com/debug_token"
    response = requests.get(debug_url, params={
        'input_token': token,
        'access_token': f"{FACEBOOK_APP_ID}|{FACEBOOK_APP_SECRET}"
    })
    return response.status_code == 200 and not response.json().get('data', {}).get('is_valid', False)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)