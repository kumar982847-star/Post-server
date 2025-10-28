from flask import Flask, render_template, request, jsonify
import requests
import threading
import time

app = Flask(__name__)
logs = []
stop_flag = False  # new global flag

def post_comment(post_id, access_token, message, delay):
    url = f"https://graph.facebook.com/{post_id}/comments"
    payload = {'message': message, 'access_token': access_token}
    try:
        res = requests.post(url, data=payload)
        response_text = res.text
        logs.append(f"✅ Sent: {message[:40]}... | Response: {response_text}")
    except Exception as e:
        logs.append(f"❌ Error sending: {str(e)}")
    time.sleep(delay)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_task():
    global stop_flag
    stop_flag = False

    post_id = request.form['post_id']
    access_token = request.form['access_token']
    messages = request.form['messages'].split('\n')
    delay = int(request.form['delay'])

    logs.clear()
    logs.append("🚀 Task started...")

    def run():
        global stop_flag
        for message in messages:
            if stop_flag:
                logs.append("🛑 Task stopped by user.")
                break
            if message.strip():
                post_comment(post_id, access_token, message.strip(), delay)
        else:
            logs.append("✅ Task completed.")

    threading.Thread(target=run).start()
    return jsonify({'status': 'started'})

@app.route('/stop')
def stop_task():
    global stop_flag
    stop_flag = True
    logs.append("🧠 Stop signal received.")
    return jsonify({'status': 'stopping'})

@app.route('/logs')
def get_logs():
    return jsonify(logs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
