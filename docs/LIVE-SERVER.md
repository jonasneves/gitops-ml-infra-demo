# Live Server Hosting

Host the ML inference API and dashboard publicly using GitHub Actions and Cloudflare Tunnel.

## Overview

This workflow runs the services on a GitHub Actions runner and exposes them via Cloudflare Tunnel, providing a public URL without any cloud infrastructure costs.

**Services:**
- ML Inference API (FastAPI) - port 8000
- Live Dashboard (Flask) - port 8080

## Prerequisites

1. Cloudflare account with a domain
2. GitHub repository secrets configured

## Setup

### 1. Create Cloudflare Tunnel

In Cloudflare Zero Trust dashboard:

1. Go to **Networks** > **Tunnels**
2. Click **Create a tunnel**
3. Name it (e.g., `gitops-ml-demo`)
4. Copy the tunnel token

### 2. Configure Public Hostnames

Add public hostnames for your tunnel:

| Subdomain | Domain | Service |
|-----------|--------|---------|
| `ml-demo` | `yourdomain.com` | `HTTP://localhost:8080` |
| `ml-api` | `yourdomain.com` | `HTTP://localhost:8000` |

Or use path-based routing with a single hostname.

### 3. Add GitHub Secret

| Secret | Description |
|--------|-------------|
| `CLOUDFLARE_TUNNEL_TOKEN` | Token from step 1 |

## Architecture

```
Internet
    │
Cloudflare Edge
    │
    └── Tunnel ── GitHub Actions Runner
                      │
                      ├── Dashboard :8080 (Flask)
                      │   └── Real-time deployment monitoring
                      │
                      └── ML API :8000 (FastAPI)
                          └── Sentiment analysis endpoints
```

## Usage

### Start via GitHub Actions UI

1. Go to Actions tab
2. Select "Live Server"
3. Click "Run workflow"
4. Configure duration and auto-restart

### Start via CLI

```bash
# Default 5.5 hours with auto-restart
gh workflow run live-server.yml

# Custom duration
gh workflow run live-server.yml -f duration_hours=2

# Disable auto-restart
gh workflow run live-server.yml -f auto_restart=false
```

### Auto-trigger

The workflow automatically starts when changes are pushed to:
- `app/ml-inference/**`
- `scripts/dashboard_server.py`

## 6-Hour Timeout Handling

GitHub Actions has a 6-hour job limit. The workflow handles this by:

1. Running for 5.5 hours by default
2. Triggering a new workflow 5 minutes before timeout
3. New runner takes over with fresh tunnel connection

This provides near-continuous availability without manual intervention.

## Monitoring

The workflow outputs health status every 30 seconds:

```
[14:32:15] API: OK | Dashboard: OK | Tunnel: OK | Elapsed: 45m | Remaining: 285m
```

Services are automatically restarted if they go down.

## Endpoints

### ML Inference API

- `GET /health` - Health check
- `GET /ready` - Readiness check
- `POST /predict` - Single text sentiment analysis
- `POST /predict/batch` - Batch prediction
- `GET /metrics` - Prometheus metrics

### Dashboard

- `GET /` - Live monitoring UI
- `GET /api/status` - Current deployment state
- `GET /api/stream` - SSE event stream
- `GET /api/debug` - Detailed debug info

## Limitations

- Not for production workloads
- ~30 second cold start when no runner is active
- GitHub Actions minutes consumption
- Tunnel connection may briefly drop during restarts

## Troubleshooting

### Tunnel not connecting

Check the tunnel token is correctly set in GitHub secrets.

### Services crashing

View workflow logs for error details. The workflow automatically restarts crashed services.

### High latency

GitHub Actions runners are shared infrastructure. Response times may vary.
