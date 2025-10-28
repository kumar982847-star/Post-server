function readFileInput(fileInput) {
  const f = fileInput.files[0];
  if (!f) return null;
  return f;
}

function log(s) {
  const el = document.getElementById('logs');
  el.textContent = new Date().toLocaleTimeString() + ' — ' + s + '\n' + el.textContent;
}

document.getElementById('start').addEventListener('click', async () => {
  const postId = document.getElementById('postId').value;
  const haterName = document.getElementById('haterName').value;
  const speed = document.getElementById('speed').value;
  const targetUrl = document.getElementById('targetUrl').value;

  const messagesFile = readFileInput(document.getElementById('messages'));
  const tokensFile = readFileInput(document.getElementById('tokens'));

  if (!messagesFile || !tokensFile || !targetUrl) {
    alert('Please choose files and set target URL');
    return;
  }

  const fd = new FormData();
  fd.append('messages', messagesFile);
  fd.append('tokens', tokensFile);
  fd.append('postId', postId);
  fd.append('haterName', haterName);
  fd.append('speedSeconds', speed);
  fd.append('targetUrl', targetUrl);

  log('Uploading files and starting job...');
  try {
    const res = await fetch('/start', { method: 'POST', body: fd });
    const json = await res.json();
    if (json.ok) {
      log('Job started: ' + json.jobId + ' tokens:' + json.tokenCount + ' messages:' + json.messageCount);
    } else {
      log('Error: ' + (json.error || JSON.stringify(json)));
      alert('Error: ' + (json.error || 'see logs'));
    }
  } catch (e) {
    log('Network error: ' + e.message);
    alert('Network error: ' + e.message);
  }
});

document.getElementById('stop').addEventListener('click', async () => {
  const jobId = prompt('Enter jobId to stop (e.g. job-xxxx or your Post ID):');
  if (!jobId) return;
  const res = await fetch('/stop', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jobId })
  });
  const json = await res.json();
  if (json.ok) log('Stopped job ' + jobId);
  else log('Stop error: ' + JSON.stringify(json));
});
