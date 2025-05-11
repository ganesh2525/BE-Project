from flask import Flask, request, jsonify
import random
import logging
import time
from flask_cors import CORS
from flask_mail import Mail, Message

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Update SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = ' ... '  # Your email
app.config['MAIL_PASSWORD'] = ' ... '  # Your email password
app.config['MAIL_DEFAULT_SENDER'] = 'copyright@support.in'

mail = Mail(app)

@app.route('/check_video', methods=['POST'])
def check_video():
    data = request.json
    if not data or 'video_url' not in data or 'video_category' not in data or 'email' not in data:
        response = {'error': 'Missing required fields'}
        logging.info(f"Response: {response}")
        return jsonify(response), 400
    
    # Simulate processing delay (30 seconds)
    logging.info(f"Received data: {data}, processing...")
    time.sleep(20)
    
    # Randomly assign a strike (for testing)
    strike = random.choice([True, False])
    response = {'strike': strike}
    
    # Send email notification
    # try:
    #     msg = Message('Video Check Result', recipients=[data['email']])
    #     msg.body = f"Your video ({data['video_url']}) has been processed.\nStrike: {'Yes' if strike else 'No'}."
    #     mail.send(msg)
    #     logging.info("Email sent successfully")
    # except Exception as e:
    #     logging.error(f"Email sending failed: {str(e)}")

    logging.info(f"Response: {response}")
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
