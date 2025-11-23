# Live Server Hosting

Host the complete GitOps infrastructure publicly using GitHub Actions and Cloudflare Tunnel.

## Overview

This workflow runs the full stack on a GitHub Actions runner:
- **Minikube** - Kubernetes cluster
- **ArgoCD** - GitOps controller with UI
- **ML Inference API** - FastAPI sentiment analysis
- **Grafana** - Monitoring dashboards
- **VictoriaMetrics** - Metrics storage
- **Live Dashboard** - Real-time deployment monitoring

All services are exposed via Cloudflare Tunnel for public access.

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

Add public hostnames for each service:

| Subdomain | Domain | Service | Type |
|-----------|--------|---------|------|
| `gitops` | `yourdomain.com` | `http://localhost:8080` | HTTP |
| `argocd` | `yourdomain.com` | `https://localhost:8443` | HTTPS |
| `ml-api` | `yourdomain.com` | `http://localhost:8000` | HTTP |
| `grafana` | `yourdomain.com` | `http://localhost:3000` | HTTP |
| `metrics` | `yourdomain.com` | `http://localhost:8428` | HTTP |

**Note:** For ArgoCD, enable "No TLS Verify" in the tunnel settings since it uses a self-signed certificate.

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
                      ├── Minikube Cluster
                      │   ├── ArgoCD (GitOps)
                      │   ├── ML Inference (FastAPI)
                      │   ├── VictoriaMetrics
                      │   └── Grafana
                      │
                      └── Dashboard (Flask)
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Dashboard | 8080 | Real-time deployment monitoring |
| ArgoCD UI | 8443 | GitOps controller interface |
| ML API | 8000 | Sentiment analysis endpoints |
| Grafana | 3000 | Metrics visualization |
| VictoriaMetrics | 8428 | Prometheus-compatible TSDB |

## Usage

### Start via GitHub Actions UI

1. Go to Actions tab
2. Select "Live Server"
3. Click "Run workflow"
4. Configure duration and auto-restart
5. Check logs for ArgoCD password

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

The workflow starts when changes are pushed to:
- `app/ml-inference/**`
- `k8s/**`
- `scripts/dashboard_server.py`

## ArgoCD Access

The ArgoCD admin password is displayed in the workflow logs:

```
ArgoCD Credentials:
  Username: admin
  Password: <generated-password>
```

Features available:
- View application sync status
- Trigger manual syncs
- View Kubernetes resources
- Check application health
- View sync history

## Monitoring

The workflow outputs health status every 30 seconds:

```
[14:32:15] ArgoCD: OK | API: OK | Grafana: OK | Dashboard: OK | Tunnel: OK | 45m/330m
```

Every 5 iterations, it also shows ArgoCD application status:

```
--- ArgoCD Apps ---
NAME           SYNC STATUS   HEALTH STATUS
ml-inference   Synced        Healthy
observability  Synced        Healthy
-------------------
```

## 6-Hour Timeout Handling

GitHub Actions has a 6-hour limit. The workflow:

1. Runs for 5.5 hours by default
2. Triggers restart 5 minutes before timeout
3. New runner takes over (services restart fresh)

**Note:** There will be ~3-5 minute downtime during restarts while Minikube and ArgoCD initialize.

## Grafana Dashboards

Default credentials:
- Username: `admin`
- Password: `admin`

Pre-configured data source: VictoriaMetrics

## Troubleshooting

### ArgoCD not accessible

Check the tunnel configuration has "No TLS Verify" enabled for the ArgoCD hostname (it uses self-signed certs).

### Applications not syncing

View ArgoCD logs:
```bash
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

### Port-forward keeps dying

The workflow auto-restarts failed port-forwards. Check the workflow logs for specific errors.

### Services slow to start

Initial setup takes ~5 minutes:
- Minikube start: ~2 min
- ArgoCD install: ~2 min
- App sync: ~1 min

## Limitations

- Not for production workloads
- ~5 minute cold start for full stack
- ArgoCD password changes on each restart
- GitHub Actions minutes consumption
- Brief downtime during auto-restart rotation
