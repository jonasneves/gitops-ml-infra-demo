# Live Server Hosting

Host the complete GitOps infrastructure publicly using GitHub Actions and Cloudflare Tunnel.

## Overview

Modular workflow architecture with three workflow files:

```mermaid
graph TB
    Orchestrator["live-server.yml<br/>(Orchestrator)"]
    Host["live-host.yml<br/>(Host Runner)"]
    Mon["live-monitoring.yml<br/>(Monitoring Runner)"]

    Orchestrator --> Host
    Orchestrator --> Mon

    subgraph HostComponents["Host Components"]
        Minikube["Minikube Cluster"]
        ArgoCD["ArgoCD"]
        ML["ML Inference API"]
        Dashboard["Live Dashboard"]
    end

    subgraph MonComponents["Monitoring Components"]
        VM["VictoriaMetrics"]
        Grafana["Grafana"]
    end

    Host -.-> HostComponents
    Mon -.-> MonComponents

    style Orchestrator fill:#3498db,stroke:#333,stroke-width:2px,color:#fff
    style Host fill:#2ecc71,stroke:#333,stroke-width:2px,color:#fff
    style Mon fill:#9c27b0,stroke:#333,stroke-width:2px,color:#fff
```

Run everything together via `live-server.yml`, or run components independently for selective deployment.

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

Create two tunnels - one for each runner:

**Main Tunnel (Host Runner):**

| Subdomain | Service | Type |
|-----------|---------|------|
| `gitops` | `http://localhost:8080` | HTTP |
| `argocd` | `https://localhost:8443` | HTTPS |
| `ml-api` | `http://localhost:8000` | HTTP |

**Monitoring Tunnel (Monitoring Runner):**

| Subdomain | Service | Type |
|-----------|---------|------|
| `grafana` | `http://localhost:3000` | HTTP |
| `metrics` | `http://localhost:8428` | HTTP |

**Note:** For ArgoCD, enable "No TLS Verify" in the tunnel settings since it uses a self-signed certificate.

### 3. Add GitHub Secrets

| Secret | Description |
|--------|-------------|
| `CLOUDFLARE_TUNNEL_TOKEN` | Token for host runner tunnel |
| `CLOUDFLARE_TUNNEL_TOKEN_MONITORING` | Token for monitoring runner tunnel (optional) |

## Architecture

```mermaid
graph TB
    Internet["Public Internet"]

    subgraph Cloudflare["Cloudflare Network"]
        Edge["Cloudflare Edge"]
        Tunnel1["Tunnel 1<br/>(Host)"]
        Tunnel2["Tunnel 2<br/>(Monitoring)"]
    end

    subgraph HostRunner["GitHub Actions: Host Runner"]
        subgraph K8s["Minikube Cluster"]
            ArgoCD["ArgoCD<br/>(GitOps)"]
            ML["ML Inference<br/>(FastAPI)"]
        end
        Dashboard["Live Dashboard<br/>(Python)"]
    end

    subgraph MonRunner["GitHub Actions: Monitoring Runner"]
        VM["VictoriaMetrics<br/>(Docker)"]
        Grafana["Grafana<br/>(Docker)"]
    end

    Internet --> Edge
    Edge --> Tunnel1
    Edge --> Tunnel2
    Tunnel1 --> Dashboard
    Tunnel1 --> ArgoCD
    Tunnel1 --> ML
    Tunnel2 --> VM
    Tunnel2 --> Grafana

    VM -.->|scrapes| ML

    style Internet fill:#e0e0e0,stroke:#333,stroke-width:2px
    style Edge fill:#ff9800,stroke:#333,stroke-width:2px,color:#fff
    style HostRunner fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style MonRunner fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style ArgoCD fill:#ef7b4d,stroke:#333,stroke-width:2px,color:#fff
    style ML fill:#009688,stroke:#333,stroke-width:2px,color:#fff
```

## Services

**Host Runner:**

| Service | Port | Description |
|---------|------|-------------|
| Dashboard | 8080 | Real-time deployment monitoring |
| ArgoCD UI | 8443 | GitOps controller interface |
| ML API | 8000 | Sentiment analysis endpoints |

**Monitoring Runner:**

| Service | Port | Description |
|---------|------|-------------|
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

# With base domain (enables service discovery)
gh workflow run live-server.yml -f base_domain=yourdomain.com
```

The `base_domain` input enables convention-based service discovery:
- `ml-api.yourdomain.com`
- `grafana.yourdomain.com`
- `argocd.yourdomain.com`
- etc.

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

Both runners output health status every 30 seconds:

**Host Runner:**
```
[14:32:15] ArgoCD: OK | API: OK | Dashboard: OK | Tunnel: OK | 45m/330m
```

**Monitoring Runner:**
```
[14:32:15] VictoriaMetrics: OK | Grafana: OK | 45m/330m
```

Services auto-restart if they go down.

## 6-Hour Timeout Handling

GitHub Actions has a 6-hour limit. The workflow handles this automatically:

```mermaid
sequenceDiagram
    participant W1 as Workflow Run 1
    participant GH as GitHub Actions
    participant W2 as Workflow Run 2

    W1->>W1: Run for 5.5 hours
    Note over W1: 5 min before timeout
    W1->>GH: Trigger workflow_dispatch
    W1->>W1: Graceful shutdown
    GH->>W2: Start new workflow run
    W2->>W2: Initialize (3-5 min)
    Note over W2: Services ready
    W2->>W2: Run for 5.5 hours
```

**Note:** Brief downtime (~3-5 minutes) during transitions while Minikube and ArgoCD initialize.

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
- ~5 minute cold start for host runner
- ArgoCD password changes on each restart
- Uses 2x GitHub Actions runner minutes (parallel jobs)
- Brief downtime during auto-restart rotation
