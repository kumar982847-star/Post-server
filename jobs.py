# jobs.py
import threading
import time
import requests
import itertools
from urllib.parse import urlparse

class Job:
    def __init__(self, job_id, target_url, tokens, messages, speed_seconds, hater_name=''):
        self.job_id = job_id
        self.target_url = target_url
        self.tokens = tokens[:]  # list
        self.messages = messages[:]  # list
        self.speed = max(1, int(speed_seconds))
        self.hater_name = hater_name
        self._stop_event = threading.Event()
        self._thread = None
        self.lock = threading.Lock()
        # per-token last sent time
        self.last_sent = {t: 0 for t in self.tokens}
        # iterators
        self._token_cycle = itertools.cycle(self.tokens)
        self._message_cycle = itertools.cycle(self.messages)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self):
        while not self._stop_event.is_set():
            token = next(self._token_cycle)
            message = next(self._message_cycle)

            now = time.time()
            # rate limit per token (do not send if last send too recent)
            with self.lock:
                last = self.last_sent.get(token, 0)
                if now - last < self.speed:
                    # skip sending from this token this cycle
                    # just sleep a bit and continue
                    time.sleep(0.1)
                    continue
                self.last_sent[token] = now

            # construct payload; adapt as needed for your target API
            payload = {
                'postId': self.job_id,
                'haterName': self.hater_name,
                'message': message
            }
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {token}'
            }
            try:
                resp = requests.post(self.target_url, json=payload, headers=headers, timeout=20)
                # If you want to log responses centrally, return tuple or use callback
                print(f"[{self.job_id}] token:{token[:6]}... status:{resp.status_code}")
            except Exception as e:
                print(f"[{self.job_id}] Error sending with token:{token[:6]}... {str(e)}")

            # Sleep a bit to avoid tight loop; main pacing controlled by speed
            # We sleep a small amount to allow other thread operations; main spacing is enforced by last_sent check.
            time.sleep(0.2)

    def to_summary(self):
        return {
            'id': self.job_id,
            'target': self.target_url,
            'tokens': len(self.tokens),
            'messages': len(self.messages),
            'speed': self.speed,
        }

def is_domain_allowed(target_url, allowed_domains):
    if not allowed_domains:
        return True
    try:
        host = urlparse(target_url).hostname
        return host in allowed_domains
    except Exception:
        return False
