from flask import Flask, render_template, request, jsonify
import requests
import time
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_posting():
    post_id = request.form.get('post_id')
    hater_name = request.form.get('hater_name')
    access_token = request.form.get('access_token')   # 👈 single token yahan se milega
    message_file = request.files['messages']
    speed = int(request.form.get('speed', 20))

    # Facebook Page ID (env file me rakho)
    PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")

    # Messages padho
    messages = message_file.read().decode('utf-8').splitlines()
    logs = []

    for msg in messages:
        full_msg = f"{hater_name}: {msg}"
        try:
            response = requests.post(
                f'https://graph.facebook.com/{PAGE_ID}/feed',
                params={
                    'message': full_msg,
                    'access_token': access_token
                }
            )
            logs.append(f"✅ Posted: {full_msg} | Status: {response.status_code}")
        except Exception as e:
            logs.append(f"❌ Error posting: {e}")
        time.sleep(speed)

    return jsonify({"logs": logs})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
