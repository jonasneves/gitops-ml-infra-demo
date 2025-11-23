from flask import Flask, Response, jsonify
from flask_cors import CORS
import subprocess
import json
import time
import threading
import os

app = Flask(__name__)
CORS(app)

# Get base domain from environment
BASE_DOMAIN = os.environ.get('BASE_DOMAIN', '')

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

def is_pod_ready(pod):
    """Check if a pod has all containers ready."""
    ready = pod["ready"]
    if ready == "0/0":
        return False
    parts = ready.split("/")
    return parts[0] == parts[1]

def get_deployment_stats(apps, pods):
    """Calculate deployment statistics."""
    return {
        "total_apps": len(apps),
        "synced_apps": sum(1 for app in apps if app["sync"] == "Synced"),
        "healthy_apps": sum(1 for app in apps if app["health"] == "Healthy"),
        "total_pods": len(pods),
        "running_pods": sum(1 for pod in pods if pod["status"] == "Running"),
        "ready_pods": sum(1 for pod in pods if is_pod_ready(pod))
    }

def calculate_progress():
    apps = deployment_state["argocd_apps"]
    pods = deployment_state["pods"]
    if not apps:
        return 10

    stats = get_deployment_stats(apps, pods)

    score = (stats["synced_apps"] / max(len(apps), 1)) * 40
    score += (stats["healthy_apps"] / max(len(apps), 1)) * 30
    score += (stats["running_pods"] / max(len(pods), 1)) * 20 if pods else 0
    score += (stats["ready_pods"] / max(len(pods), 1)) * 10 if pods else 0

    return min(int(score), 100)

def update_state():
    while True:
        try:
            deployment_state["argocd_apps"] = get_argocd_status()
            deployment_state["pods"] = get_pods_status()
            deployment_state["progress"] = calculate_progress()
            p = deployment_state["progress"]

            pods = deployment_state["pods"]
            running_count = sum(1 for pod in pods if pod["status"] == "Running")
            pending_count = sum(1 for pod in pods if pod["status"] == "Pending")

            if p < 20:
                deployment_state["phase"] = "Initializing ArgoCD"
            elif p < 70:
                deployment_state["phase"] = "Syncing Applications"
            elif pending_count > 0:
                deployment_state["phase"] = f"Starting Pods ({running_count}/{len(pods)} running)"
            elif p < 100:
                deployment_state["phase"] = "Waiting for Ready"
            else:
                deployment_state["phase"] = "Deployment Complete"
        except:
            pass
        time.sleep(3)

threading.Thread(target=update_state, daemon=True).start()

@app.route('/')
def index():
    html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GitOps Infrastructure Dashboard</title>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({
      startOnLoad: true,
      theme: 'base',
      themeVariables: {
        primaryColor: '#E3F2FD',
        primaryTextColor: '#1565C0',
        primaryBorderColor: '#1976D2',
        lineColor: '#424242',
        secondaryColor: '#FFF3E0',
        tertiaryColor: '#E8F5E9',
        fontSize: '16px',
        fontFamily: 'Google Sans, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif',
        edgeLabelBackground: '#ffffff',
        clusterBkg: '#ffffff',
        clusterBorder: '#90A4AE'
      },
      flowchart: {
        curve: 'basis',
        padding: 20,
        nodeSpacing: 80,
        rankSpacing: 80,
        diagramPadding: 20,
        useMaxWidth: true
      }
    });
  </script>
  <style>
    :root {
      --bg-primary: #fafafa;
      --bg-secondary: #ffffff;
      --text-primary: #202124;
      --text-secondary: #5f6368;
      --border-color: #e8eaed;
      --accent: #1a73e8;
      --success: #34a853;
      --warning: #fbbc04;
      --error: #ea4335;
      --surface-hover: #f1f3f4;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Google Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
    }

    /* Header */
    .header {
      margin-bottom: 32px;
    }

    .header-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .header h1 {
      font-size: 22px;
      font-weight: 400;
      color: var(--text-primary);
    }

    .live-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      background: #e8f5e9;
      color: var(--success);
      border-radius: 16px;
      font-size: 12px;
      font-weight: 500;
    }

    .live-dot {
      width: 8px;
      height: 8px;
      background: var(--success);
      border-radius: 50%;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    .header-subtitle {
      font-size: 14px;
      color: var(--text-secondary);
    }

    /* Cards */
    .card {
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      margin-bottom: 16px;
    }

    .card-header {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border-color);
      font-size: 14px;
      font-weight: 500;
      color: var(--text-primary);
    }

    .card-body {
      padding: 20px;
    }

    /* Progress Section */
    .progress-container {
      margin-bottom: 16px;
    }

    .progress-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .progress-phase {
      font-size: 14px;
      font-weight: 500;
    }

    .progress-percent {
      font-size: 14px;
      color: var(--text-secondary);
    }

    .progress-bar {
      height: 4px;
      background: var(--border-color);
      border-radius: 2px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--accent);
      transition: width 0.3s ease;
    }

    .progress-fill.complete {
      background: var(--success);
    }

    /* Stats Grid */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }

    .stat-card {
      background: var(--bg-secondary);
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 16px;
    }

    .stat-label {
      font-size: 12px;
      color: var(--text-secondary);
      margin-bottom: 4px;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 400;
      color: var(--text-primary);
    }

    /* Service Registry */
    .service-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
    }

    .service-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: var(--bg-primary);
      border-radius: 6px;
      transition: background 0.15s;
    }

    .service-item:hover {
      background: var(--surface-hover);
    }

    .service-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .service-icon {
      width: 32px;
      height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bg-secondary);
      border-radius: 6px;
      font-size: 14px;
    }

    .service-icon img {
      width: 24px;
      height: 24px;
      object-fit: contain;
    }

    /* Colored icons for services */
    .service-icon.argocd img { filter: none; }
    .service-icon.ml-api img { fill: #EE4C2C; filter: invert(35%) sepia(94%) saturate(3065%) hue-rotate(354deg) brightness(97%) contrast(92%); }
    .service-icon.dashboard img { filter: invert(42%) sepia(93%) saturate(1821%) hue-rotate(195deg) brightness(102%) contrast(97%); }
    .service-icon.grafana img { filter: invert(55%) sepia(86%) saturate(2654%) hue-rotate(359deg) brightness(101%) contrast(101%); }
    .service-icon.victoria img { filter: none; }

    .service-name {
      font-size: 14px;
      font-weight: 500;
    }

    .service-desc {
      font-size: 12px;
      color: var(--text-secondary);
    }

    .service-url {
      font-size: 12px;
      color: var(--accent);
      text-decoration: none;
    }

    .service-url:hover {
      text-decoration: underline;
    }

    /* Architecture */
    .architecture {
      background: var(--bg-primary);
      padding: 24px;
      border-radius: 6px;
      overflow-x: auto;
      display: flex;
      justify-content: center;
      min-height: 500px;
    }

    .mermaid {
      background: transparent !important;
      width: 100%;
      min-height: 450px;
    }

    .mermaid svg {
      max-width: 100%;
      height: auto;
    }

    /* Apps and Pods Lists */
    .list-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid var(--border-color);
    }

    .list-item:last-child {
      border-bottom: none;
    }

    .list-item-name {
      font-size: 14px;
      font-weight: 500;
    }

    .list-item-meta {
      font-size: 12px;
      color: var(--text-secondary);
    }

    .badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 500;
      text-transform: uppercase;
    }

    .badge-success {
      background: #e8f5e9;
      color: var(--success);
    }

    .badge-warning {
      background: #fff8e1;
      color: #f57c00;
    }

    .badge-info {
      background: #e3f2fd;
      color: var(--accent);
    }

    .badges {
      display: flex;
      gap: 6px;
    }

    /* Two Column Layout */
    .two-col {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }

    /* Empty State */
    .empty-state {
      text-align: center;
      padding: 24px;
      color: var(--text-secondary);
      font-size: 14px;
    }

    /* Footer */
    .footer {
      text-align: center;
      padding: 24px;
      color: var(--text-secondary);
      font-size: 12px;
    }

    @media (max-width: 768px) {
      .stats-grid { grid-template-columns: repeat(2, 1fr); }
      .two-col { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header -->
    <div class="header">
      <div class="header-top">
        <h1>GitOps Infrastructure Dashboard</h1>
        <span class="live-badge">
          <span class="live-dot"></span>
          Live
        </span>
      </div>
      <p class="header-subtitle">Real-time monitoring for Kubernetes deployments managed by ArgoCD</p>
    </div>

    <!-- Progress -->
    <div class="card">
      <div class="card-body">
        <div class="progress-container">
          <div class="progress-header">
            <span class="progress-phase" id="phaseText">Initializing...</span>
            <span class="progress-percent" id="progressPercent">0%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" id="progressBar" style="width: 0%"></div>
          </div>
        </div>
        <p style="font-size: 12px; color: var(--text-secondary);" id="elapsed">Elapsed: 0m 0s</p>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Applications</div>
        <div class="stat-value" id="appCount">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Pods</div>
        <div class="stat-value" id="podCount">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Running</div>
        <div class="stat-value" id="runningPods">0</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Ready</div>
        <div class="stat-value" id="readyPods">0</div>
      </div>
    </div>

    <!-- Service Registry -->
    <div class="card">
      <div class="card-header">Service Registry</div>
      <div class="card-body">
        <div class="service-grid" id="serviceRegistry">
          <!-- Populated by JS -->
        </div>
      </div>
    </div>

    <!-- Architecture -->
    <div class="card">
      <div class="card-header">Architecture</div>
      <div class="card-body">
        <div class="architecture">
          <div class="mermaid">
%%{init: {'theme':'base', 'themeVariables': {'primaryBorderColor':'#1976D2','lineColor':'#616161'}}}%%
graph TB
    CF([Cloudflare Edge])

    subgraph Host["🖥️ Host Runner"]
        direction TB
        MK([Minikube])
        subgraph K8s["☸️ Kubernetes Cluster"]
            direction LR
            AC([ArgoCD])
            ML([ML API])
        end
        DASH([Dashboard])
    end

    subgraph MON["📊 Monitoring Runner"]
        direction TB
        VM([VictoriaMetrics])
        GR([Grafana])
    end

    CF -.->|HTTPS| Host
    CF -.->|HTTPS| MON
    MK ==>|hosts| K8s
    K8s -.->|metrics| VM
    VM -->|data| GR

    style CF fill:#FFB74D,stroke:#F57C00,stroke-width:3px,color:#000
    style Host fill:#E3F2FD,stroke:#1976D2,stroke-width:3px,rx:15,ry:15
    style MON fill:#E8F5E9,stroke:#43A047,stroke-width:3px,rx:15,ry:15
    style K8s fill:#FFF3E0,stroke:#FB8C00,stroke-width:2px,rx:10,ry:10
    style MK fill:#BBDEFB,stroke:#1976D2,stroke-width:2px,color:#0D47A1
    style AC fill:#FFCCBC,stroke:#E64A19,stroke-width:2px,color:#BF360C
    style ML fill:#C5E1A5,stroke:#689F38,stroke-width:2px,color:#33691E
    style DASH fill:#B3E5FC,stroke:#0288D1,stroke-width:2px,color:#01579B
    style VM fill:#C8E6C9,stroke:#43A047,stroke-width:2px,color:#1B5E20
    style GR fill:#FFAB91,stroke:#FF5722,stroke-width:2px,color:#BF360C
          </div>
        </div>
      </div>
    </div>

    <!-- Apps and Pods -->
    <div class="two-col">
      <div class="card">
        <div class="card-header">ArgoCD Applications</div>
        <div class="card-body" id="appsList">
          <div class="empty-state">Waiting for applications...</div>
        </div>
      </div>
      <div class="card">
        <div class="card-header">Kubernetes Pods</div>
        <div class="card-body" id="podsList">
          <div class="empty-state">Waiting for pods...</div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="footer">
      GitOps ML Infrastructure Demo
    </div>
  </div>

  <script>
    const BASE_DOMAIN = ''' + json.dumps(BASE_DOMAIN) + ''';

    // Service definitions with logo URLs
    const services = [
      {
        name: 'ArgoCD',
        desc: 'GitOps Controller',
        logo: 'https://landscape.cncf.io/logos/argo.svg',
        iconClass: 'argocd',
        port: 8443,
        subdomain: 'argocd',
        https: true
      },
      {
        name: 'ML API',
        desc: 'Inference Service',
        logo: 'https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/pytorch.svg',
        iconClass: 'ml-api',
        port: 8000,
        subdomain: 'ml-api',
        https: false
      },
      {
        name: 'Dashboard',
        desc: 'This Dashboard',
        logo: 'https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/kubernetes.svg',
        iconClass: 'dashboard',
        port: 8080,
        subdomain: 'gitops',
        https: false
      },
      {
        name: 'Grafana',
        desc: 'Metrics Visualization',
        logo: 'https://cdn.jsdelivr.net/npm/simple-icons@v11/icons/grafana.svg',
        iconClass: 'grafana',
        port: 3000,
        subdomain: 'grafana',
        https: false
      },
      {
        name: 'VictoriaMetrics',
        desc: 'Time Series DB',
        logo: 'https://raw.githubusercontent.com/VictoriaMetrics/VictoriaMetrics/master/docs/logo.png',
        iconClass: 'victoria',
        port: 8428,
        subdomain: 'metrics',
        https: false
      }
    ];

    // Render service registry
    function renderServices() {
      const container = document.getElementById('serviceRegistry');
      container.innerHTML = services.map(svc => {
        let url, displayUrl;
        if (BASE_DOMAIN) {
          const protocol = svc.https ? 'https' : 'http';
          url = `${protocol}://${svc.subdomain}.${BASE_DOMAIN}`;
          displayUrl = url; // Show full URL with protocol when using custom domain
        } else {
          const protocol = svc.https ? 'https' : 'http';
          url = `${protocol}://localhost:${svc.port}`;
          displayUrl = `localhost:${svc.port}`; // Show cleaner format for localhost
        }

        return `
          <div class="service-item">
            <div class="service-info">
              <div class="service-icon ${svc.iconClass}"><img src="${svc.logo}" alt="${svc.name}" onerror="this.style.display='none'"/></div>
              <div>
                <div class="service-name">${svc.name}</div>
                <div class="service-desc">${svc.desc}</div>
              </div>
            </div>
            <a href="${url}" target="_blank" class="service-url">${displayUrl}</a>
          </div>
        `;
      }).join('');
    }

    renderServices();

    // SSE connection
    const eventSource = new EventSource('/api/stream');

    eventSource.onmessage = function(e) {
      const data = JSON.parse(e.data);

      // Progress
      const progress = data.progress;
      const progressBar = document.getElementById('progressBar');
      progressBar.style.width = progress + '%';
      if (progress >= 100) {
        progressBar.classList.add('complete');
      }

      document.getElementById('phaseText').textContent = data.phase;
      document.getElementById('progressPercent').textContent = progress + '%';

      // Elapsed
      const mins = Math.floor(data.elapsed / 60);
      const secs = data.elapsed % 60;
      document.getElementById('elapsed').textContent = `Elapsed: ${mins}m ${secs}s`;

      // Stats
      document.getElementById('appCount').textContent = data.argocd_apps.length;
      document.getElementById('podCount').textContent = data.pods.length;

      const running = data.pods.filter(p => p.status === 'Running').length;
      const ready = data.pods.filter(p => {
        const parts = p.ready.split('/');
        return parts[0] === parts[1] && parts[0] !== '0';
      }).length;

      document.getElementById('runningPods').textContent = running;
      document.getElementById('readyPods').textContent = ready;

      // Apps list
      const appsContainer = document.getElementById('appsList');
      if (data.argocd_apps.length) {
        appsContainer.innerHTML = data.argocd_apps.map(app => {
          const syncClass = app.sync === 'Synced' ? 'badge-success' : 'badge-warning';
          const healthClass = app.health === 'Healthy' ? 'badge-success' : 'badge-warning';
          return `
            <div class="list-item">
              <div>
                <div class="list-item-name">${app.name}</div>
              </div>
              <div class="badges">
                <span class="badge ${syncClass}">${app.sync}</span>
                <span class="badge ${healthClass}">${app.health}</span>
              </div>
            </div>
          `;
        }).join('');
      } else {
        appsContainer.innerHTML = '<div class="empty-state">Waiting for applications...</div>';
      }

      // Pods list
      const podsContainer = document.getElementById('podsList');
      if (data.pods.length) {
        podsContainer.innerHTML = data.pods.map(pod => {
          let statusClass = 'badge-info';
          if (pod.status === 'Running') statusClass = 'badge-success';
          else if (pod.status === 'Pending') statusClass = 'badge-warning';

          return `
            <div class="list-item">
              <div>
                <div class="list-item-name">${pod.name.substring(0, 30)}${pod.name.length > 30 ? '...' : ''}</div>
                <div class="list-item-meta">${pod.namespace} · ${pod.ready} ready</div>
              </div>
              <span class="badge ${statusClass}">${pod.status}</span>
            </div>
          `;
        }).join('');
      } else {
        podsContainer.innerHTML = '<div class="empty-state">Waiting for pods...</div>';
      }
    };
  </script>
</body>
</html>'''
    return html

@app.route('/api/status')
def status():
    """Get current status as JSON"""
    elapsed = int(time.time() - deployment_state["start_time"])
    return jsonify({
        **deployment_state,
        "elapsed": elapsed,
        "base_domain": BASE_DOMAIN
    })

@app.route('/api/stream')
def stream():
    def generate():
        while True:
            elapsed = int(time.time() - deployment_state["start_time"])
            data = {**deployment_state, "elapsed": elapsed, "events": [], "start_time": None}
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(3)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/debug')
def debug():
    """Debug endpoint to see detailed pod statuses"""
    pods_detail = [{
        "name": pod["name"],
        "namespace": pod["namespace"],
        "status": pod["status"],
        "ready": pod["ready"],
        "is_running": pod["status"] == "Running",
        "is_ready": is_pod_ready(pod)
    } for pod in deployment_state["pods"]]

    return jsonify({
        "argocd_apps": deployment_state["argocd_apps"],
        "pods": pods_detail,
        "progress": deployment_state["progress"],
        "phase": deployment_state["phase"],
        "summary": get_deployment_stats(deployment_state["argocd_apps"], deployment_state["pods"])
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
