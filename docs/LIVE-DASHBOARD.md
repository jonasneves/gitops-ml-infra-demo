# Live GitOps Dashboard

Real-time deployment monitoring dashboard with public URL via Cloudflare Tunnel.

## Overview

The dashboard streams deployment progress via Server-Sent Events (SSE):
- ArgoCD application sync status
- Kubernetes pod lifecycle
- Deployment progress percentage
- Interactive API testing

## Quick Start

1. Go to **Actions** > **Live GitOps Dashboard**
2. Click **Run workflow**
3. Set duration (default: 20 minutes)
4. Get public URL from the "Start Cloudflare Tunnel" step logs

## Progress Calculation

```
Progress = 40% (apps synced) + 30% (apps healthy) + 20% (pods running) + 10% (pods ready)
```

## Deployment Phases

| Phase | Progress | Description |
|-------|----------|-------------|
| Initializing | 0-20% | ArgoCD setup |
| Syncing | 20-50% | Deploying resources |
| Starting | 50-80% | Pods pulling images |
| Finalizing | 80-99% | Health checks |
| Complete | 100% | All healthy |

## Architecture

```
GitHub Actions Runner
    │
    ├── Flask Server (port 8080)
    │   ├── HTML dashboard
    │   └── SSE stream (/api/stream)
    │
    └── Minikube Cluster
        ├── ArgoCD
        └── Deployed apps
            │
            └── Cloudflare Tunnel → Public URL
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Dashboard UI |
| `/api/status` | JSON status |
| `/api/stream` | SSE event stream |
| `/api/debug` | Detailed pod info |

## Troubleshooting

**Dashboard not loading:** Check Flask server started on port 8080 in logs.

**No ArgoCD apps:** Wait 30-60 seconds for ArgoCD to sync.

**Pods stuck in Pending:** Normal - watch them progress to Running.

**URL not appearing:** Check "Start Cloudflare Tunnel" step for the URL.

## Cost

Free - GitHub Actions (public repos) + Cloudflare Tunnel (free tier).
