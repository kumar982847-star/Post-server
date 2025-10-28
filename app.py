from flask import Flask, render_template, request, jsonify
import requests
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_posting():
    post_id = request.form.get('post_id')
    hater_name = request.form.get('hater_name')
    access_token = request.form.get('access_token')
    message_file = request.files['messages']
    speed = int(request.form.get('speed', 20))

    messages = message_file.read().decode('utf-8').splitlines()
    logs = []

    for msg in messages:
        full_msg = f"{hater_name}: {msg}"
        try:
            response = requests.post(
                f'https://graph.facebook.com/{post_id}/comments',   # 👈 feed → comments
                params={
                    'message': full_msg,
                    'access_token': access_token
                }
            )

            if response.status_code == 200:
                logs.append(f"✅ Commented: {full_msg}")
            else:
                logs.append(f"❌ Failed ({response.status_code}): {response.text}")

        except Exception as e:
            logs.append(f"⚠️ Error: {e}")

        time.sleep(speed)

    return jsonify({"logs": logs})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
