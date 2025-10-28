# app.py
import os
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import uuid
from jobs import Job, is_domain_allowed
import threading

load_dotenv()

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_DOMAINS = [d.strip() for d in os.environ.get('ALLOWED_DOMAINS', '').split(',') if d.strip()]
MIN_INTERVAL_SECONDS = int(os.environ.get('MIN_INTERVAL_SECONDS', '3'))
PORT = int(os.environ.get('PORT', '3000'))

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')

# In-memory jobs dictionary
jobs = {}
jobs_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

def _save_uploaded_text_file(file_storage):
    filename = secure_filename(file_storage.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4().hex}_{filename}")
    file_storage.save(path)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [l.strip() for l in f.read().splitlines() if l.strip()]
    return path, lines

@app.route('/start', methods=['POST'])
def start_job():
    try:
        postId = request.form.get('postId') or f"job-{uuid.uuid4().hex[:8]}"
        haterName = request.form.get('haterName', '')
        speedSeconds = int(request.form.get('speedSeconds') or 20)
        targetUrl = request.form.get('targetUrl')
        # files
        messages_file = request.files.get('messages')
        tokens_file = request.files.get('tokens')

        if not targetUrl:
            return jsonify({'error': 'targetUrl required (your API endpoint)'}), 400
        if not messages_file or not tokens_file:
            return jsonify({'error': 'messages and tokens files required'}), 400

        # domain whitelist
        if not is_domain_allowed(targetUrl, ALLOWED_DOMAINS):
            return jsonify({'error': 'targetUrl domain is not allowed by server configuration'}), 400

        _, messages = _save_uploaded_text_file(messages_file)
        _, tokens = _save_uploaded_text_file(tokens_file)

        if not messages or not tokens:
            return jsonify({'error': 'Uploaded files are empty or malformed'}), 400

        # clamp speed to MIN_INTERVAL_SECONDS
        speedSeconds = max(speedSeconds, MIN_INTERVAL_SECONDS)

        job_id = postId

        with jobs_lock:
            # stop existing if same id
            if job_id in jobs:
                jobs[job_id].stop()
                del jobs[job_id]

            job = Job(job_id=job_id, target_url=targetUrl, tokens=tokens, messages=messages, speed_seconds=speedSeconds, hater_name=haterName)
            job.start()
            jobs[job_id] = job

        return jsonify({'ok': True, 'jobId': job_id, 'tokenCount': len(tokens), 'messageCount': len(messages)})
    except Exception as e:
        return jsonify({'error': 'server error', 'detail': str(e)}), 500

@app.route('/stop', methods=['POST'])
def stop_job():
    data = request.get_json() or {}
    job_id = data.get('jobId')
    if not job_id:
        return jsonify({'error': 'jobId required'}), 400
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({'error': 'job not found'}), 404
        job.stop()
        del jobs[job_id]
    return jsonify({'ok': True, 'stopped': job_id})

@app.route('/status', methods=['GET'])
def status():
    with jobs_lock:
        summary = [j.to_summary() for j in jobs.values()]
    return jsonify({'jobs': summary})

# static files served automatically by Flask from /static

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=False)
