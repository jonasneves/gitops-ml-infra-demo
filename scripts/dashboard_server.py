from flask import Flask, Response, jsonify
from flask_cors import CORS
import subprocess
import json
import time
import threading

app = Flask(__name__)
CORS(app)

deployment_state = {
    "start_time": time.time(),
    "argocd_apps": [],
    "pods": [],
    "events": [],
    "progress": 0,
    "phase": "Initializing"
}

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except:
        return ""

def get_argocd_status():
    try:
        output = run_command("argocd app list -o json 2>/dev/null || echo '[]'")
        if output and output != '[]':
            apps = json.loads(output)
            return [{"name": app.get("metadata", {}).get("name", "unknown"),
                     "sync": app.get("status", {}).get("sync", {}).get("status", "Unknown"),
                     "health": app.get("status", {}).get("health", {}).get("status", "Unknown")}
                    for app in apps]
    except:
        pass
    return []

def get_pods_status():
    try:
        output = run_command("kubectl get pods -A -o json 2>/dev/null")
        if output:
            data = json.loads(output)
            pods = []
            for item in data.get("items", []):
                ns = item["metadata"]["namespace"]
                if ns in ["ml-inference", "monitoring", "argocd"]:
                    ready = "0/0"
                    if "containerStatuses" in item["status"]:
                        total = len(item["status"]["containerStatuses"])
                        ready_count = sum(1 for c in item["status"]["containerStatuses"] if c.get("ready"))
                        ready = f"{ready_count}/{total}"
                    pods.append({"namespace": ns, "name": item["metadata"]["name"],
                                "status": item["status"]["phase"], "ready": ready})
            return pods
    except:
        pass
    return []

def calculate_progress():
    apps = deployment_state["argocd_apps"]
    pods = deployment_state["pods"]
    if not apps:
        return 10
    synced = sum(1 for app in apps if app["sync"] == "Synced")
    healthy = sum(1 for app in apps if app["health"] == "Healthy")
    running = sum(1 for pod in pods if pod["status"] == "Running")
    score = (synced / max(len(apps), 1)) * 50 + (healthy / max(len(apps), 1)) * 30
    score += (running / max(len(pods), 1)) * 20 if pods else 0
    return min(int(score), 100)

def update_state():
    while True:
        try:
            deployment_state["argocd_apps"] = get_argocd_status()
            deployment_state["pods"] = get_pods_status()
            deployment_state["progress"] = calculate_progress()
            p = deployment_state["progress"]
            if p < 30:
                deployment_state["phase"] = "Initializing"
            elif p < 70:
                deployment_state["phase"] = "Syncing Applications"
            elif p < 100:
                deployment_state["phase"] = "Starting Services"
            else:
                deployment_state["phase"] = "Deployment Complete"
        except:
            pass
        time.sleep(3)

threading.Thread(target=update_state, daemon=True).start()

@app.route('/')
def index():
    html = '''<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Live GitOps Dashboard</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: system-ui, -apple-system, sans-serif; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
       color: white; padding: 20px; min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; }
.header { text-align: center; margin-bottom: 30px; padding: 20px; background: rgba(255,255,255,0.1);
border-radius: 15px; backdrop-filter: blur(10px); }
.header h1 { font-size: 2.5em; margin-bottom: 10px; }
.progress-section { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 25px; margin-bottom: 20px; }
.progress-bar { background: rgba(0,0,0,0.3); border-radius: 10px; height: 30px; overflow: hidden; margin: 15px 0; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #4CAF50, #8BC34A);
       transition: width 0.5s ease; display: flex; align-items: center;
       justify-content: center; font-weight: bold; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
.card { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; }
.card h3 { font-size: 1em; opacity: 0.9; margin-bottom: 10px; }
.card .value { font-size: 2em; font-weight: bold; }
.item { background: rgba(0,0,0,0.2); border-radius: 8px; padding: 12px; margin-bottom: 10px; }
.badge { padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: bold; display: inline-block; margin-left: 10px; }
.badge-synced, .badge-healthy, .badge-running { background: #4CAF50; }
.badge-pending, .badge-progressing { background: #FF9800; }
.live-indicator { display: inline-block; width: 10px; height: 10px; background: #f44336;
        border-radius: 50%; animation: pulse 2s infinite; margin-right: 8px; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🎭 Live GitOps Dashboard</h1>
    <p><span class="live-indicator"></span>Real-time deployment monitoring</p>
  </div>
  <div class="progress-section">
    <h2 id="phaseText">Initializing...</h2>
    <div class="progress-bar"><div class="progress-fill" id="progressBar" style="width:0%">0%</div></div>
    <p id="elapsed">Elapsed: 0s</p>
  </div>
  <div class="grid">
    <div class="card"><h3>📦 ArgoCD Apps</h3><div class="value" id="appCount">0</div></div>
    <div class="card"><h3>☸️ Pods</h3><div class="value" id="podCount">0</div></div>
    <div class="card"><h3>✅ Running</h3><div class="value" id="runningPods">0</div></div>
    <div class="card"><h3>📈 Progress</h3><div class="value" id="progressPercent">0%</div></div>
  </div>
  <div class="progress-section">
    <h2>🔄 ArgoCD Applications</h2><div id="appsList">Loading...</div>
  </div>
  <div class="progress-section">
    <h2>☸️ Kubernetes Pods</h2><div id="podsList">Loading...</div>
  </div>
</div>
<script>
const eventSource = new EventSource('/api/stream');
eventSource.onmessage = function(e) {
  const data = JSON.parse(e.data);
  document.getElementById('progressBar').style.width = data.progress + '%';
  document.getElementById('progressBar').textContent = data.progress + '%';
  document.getElementById('phaseText').textContent = data.phase;
  document.getElementById('progressPercent').textContent = data.progress + '%';
  const mins = Math.floor(data.elapsed / 60);
  const secs = data.elapsed % 60;
  document.getElementById('elapsed').textContent = `Elapsed: ${mins}m ${secs}s`;
  document.getElementById('appCount').textContent = data.argocd_apps.length;
  document.getElementById('podCount').textContent = data.pods.length;
  const running = data.pods.filter(p => p.status === 'Running').length;
  document.getElementById('runningPods').textContent = running;
  document.getElementById('appsList').innerHTML = data.argocd_apps.length ? data.argocd_apps.map(app =>
    `<div class="item"><strong>${app.name}</strong>
     <span class="badge badge-${app.sync.toLowerCase()}">${app.sync}</span>
     <span class="badge badge-${app.health.toLowerCase()}">${app.health}</span></div>`).join('') :
    '<p>No applications yet...</p>';
  document.getElementById('podsList').innerHTML = data.pods.length ? data.pods.map(pod =>
    `<div class="item"><strong>${pod.name}</strong> (${pod.namespace})
     <span class="badge badge-${pod.status.toLowerCase()}">${pod.status}</span>
     <small style="opacity:0.7; margin-left:10px;">${pod.ready} ready</small></div>`).join('') :
    '<p>No pods yet...</p>';
};
</script>
</body></html>'''
    return html

@app.route('/api/stream')
def stream():
    def generate():
        while True:
            elapsed = int(time.time() - deployment_state["start_time"])
            data = {**deployment_state, "elapsed": elapsed, "events": [], "start_time": None}
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(3)
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
