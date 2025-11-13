# GitOps ML Infrastructure Demo

[![GitOps Demo](https://github.com/jonasneves/gitops-ml-infra-demo/actions/workflows/gitops-demo.yml/badge.svg)](https://github.com/jonasneves/gitops-ml-infra-demo/actions/workflows/gitops-demo.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Production-grade ML infrastructure implementing GitOps practices with ArgoCD, Kubernetes, and automated CI/CD pipelines.**

Built entirely on GitHub Actions free tier with zero cloud costs, this project demonstrates modern infrastructure patterns including declarative deployments, self-healing systems, real-time observability, and automated testing.

## Overview

This project implements a complete MLOps infrastructure stack featuring:

- **GitOps Deployment**: ArgoCD continuously syncs Kubernetes manifests from Git
- **Automated CI/CD**: Parallelized GitHub Actions workflows for build, deploy, test, and demo phases
- **ML Inference Service**: FastAPI-based sentiment analysis API with Prometheus-compatible metrics
- **Observability Stack**: VictoriaMetrics monitoring and Grafana visualization
- **Live Dashboard**: Real-time deployment progress tracking via Server-Sent Events
- **Public Exposure**: Cloudflare Tunnel integration for external access
- **Self-Healing**: Automatic drift detection and correction

The infrastructure runs on Minikube within GitHub Actions runners, demonstrating that complex cloud-native patterns can be implemented without cloud provider costs.

## Architecture

### Infrastructure Stack

```
┌─────────────────────────────────────────┐
│       GitHub Actions Runner              │
│  ┌───────────────────────────────────┐  │
│  │      Minikube Cluster             │  │
│  │                                    │  │
│  │  ┌──────────────────────────────┐ │  │
│  │  │         ArgoCD               │ │  │
│  │  │   (GitOps Controller)        │ │  │
│  │  └────────┬─────────────────────┘ │  │
│  │           │ watches & syncs       │  │
│  │           ▼                        │  │
│  │  ┌──────────────────────────────┐ │  │
│  │  │   ML Inference Service       │ │  │
│  │  │   (2-5 replicas, HPA)        │ │  │
│  │  │   - FastAPI                  │ │  │
│  │  │   - Sentiment Analysis       │ │  │
│  │  │   - Metrics Exposition       │ │  │
│  │  └──────────────────────────────┘ │  │
│  │                                    │  │
│  │  ┌──────────────────────────────┐ │  │
│  │  │   Observability Stack        │ │  │
│  │  │   - VictoriaMetrics          │ │  │
│  │  │   - Grafana                  │ │  │
│  │  └──────────────────────────────┘ │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
            ▲
            │ Git Repository (Single Source of Truth)
            │
     Changes → ArgoCD Auto-Syncs
```

### CI/CD Pipeline

The workflow implements a parallelized job structure for optimal performance:

```
Build Job (8 min)
    │
    ├─ Build Docker image
    ├─ Push to GHCR
    └─ Store artifacts
         │
         ├──────────────┬──────────────┬──────────────┐
         │              │              │              │
    Deploy Job     Test Job      Demo Job     Dashboard Job
    (5 min)        (3 min)       (2 min)      (15 min)
         │              │              │              │
    ├─ Minikube    ├─ Health     ├─ Self-heal ├─ Minikube
    ├─ ArgoCD      ├─ API tests  ├─ Drift det ├─ ArgoCD
    └─ Sync apps   └─ Metrics    └─ Validate  ├─ Dashboard
                                                └─ Public URL
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                                │
                           Report Job
                            (1 min)
```

Jobs run in parallel after build completion. Dashboard job provides real-time public monitoring via Cloudflare Tunnel.

## Technical Implementation

### GitOps Practices
- **Declarative Infrastructure**: All resources defined in version-controlled YAML manifests
- **ArgoCD Integration**: Automated deployment with continuous synchronization from Git
- **Self-Healing**: Automatic drift detection and correction when cluster state diverges from Git
- **Audit Trail**: Complete history of infrastructure changes via Git commits
- **Continuous Deployment**: Automatic sync on repository changes

### ML Operations
- **Container Orchestration**: Kubernetes deployment with replica management
- **Inference Service**: FastAPI-based REST API for sentiment analysis
- **Auto-Scaling**: Horizontal Pod Autoscaler (HPA) based on CPU/memory utilization
- **Health Probes**: Liveness, readiness, and startup probes for reliability
- **Resource Management**: CPU and memory requests/limits for optimal scheduling

### Observability
- **VictoriaMetrics**: High-performance metrics collection and storage (Prometheus-compatible)
- **Grafana**: Visualization dashboards for monitoring
- **Custom Metrics**: Application-specific instrumentation
- **Service Discovery**: Automatic endpoint detection via pod annotations

### CI/CD Pipeline
- **Parallelized Workflows**: Independent jobs run concurrently for faster feedback
- **Container Registry**: GitHub Container Registry (GHCR) integration
- **Automated Testing**: Health checks and API validation
- **Artifact Generation**: Deployment reports and logs
- **Fail-Fast**: Concurrency control cancels outdated runs

## Getting Started

### GitHub Actions Workflow

The primary workflow runs the complete infrastructure stack:

1. Navigate to the [Actions tab](../../actions/workflows/gitops-demo.yml)
2. Select "GitOps Infrastructure Demo"
3. Click "Run workflow"
4. Monitor the parallelized build, deploy, test, and demo jobs
5. Download artifacts containing deployment reports and logs

**Duration:** ~10 minutes | **Cost:** $0 (GitHub Actions free tier)

### Local Deployment

```bash
# Prerequisites: Docker, kubectl, minikube

# 1. Clone repository
git clone https://github.com/jonasneves/gitops-ml-infra-demo.git
cd gitops-ml-infra-demo

# 2. Start Minikube
minikube start --cpus=2 --memory=4096 --kubernetes-version=v1.28.0

# 3. Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# 4. Get ArgoCD password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# 5. Access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080 (admin / password from step 4)

# 6. Deploy via ArgoCD
argocd app create ml-inference \
  --repo https://github.com/jonasneves/gitops-ml-infra-demo \
  --path k8s/inference-service \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace ml-inference \
  --sync-policy automated
```

## Project Structure

```
.
├── .github/workflows/
│   ├── gitops-demo.yml                # Main parallelized GitOps workflow with dashboard
│   ├── live-gitops-dashboard.yml      # Standalone real-time deployment dashboard
│   └── debug-ssh-access.yml           # Interactive debugging via SSH
│
├── app/ml-inference/
│   ├── app.py                         # FastAPI sentiment analysis service
│   ├── requirements.txt
│   └── Dockerfile
│
├── k8s/
│   ├── inference-service/             # ML service manifests
│   │   ├── deployment.yaml            # Pod specification with HPA
│   │   ├── service.yaml               # ClusterIP service
│   │   └── hpa.yaml                   # Horizontal Pod Autoscaler
│   │
│   └── observability/                 # Monitoring stack
│       ├── victoriametrics-deployment.yaml
│       └── grafana-deployment.yaml
│
├── docs/
│   ├── WORKFLOW-ARCHITECTURE.md       # CI/CD pipeline design
│   ├── LIVE-DASHBOARD.md              # Real-time monitoring setup
│   └── DEBUG-WORKFLOW.md              # SSH debugging documentation
│
└── README.md
```

## Key Features

### GitOps Workflow

The infrastructure implements a pull-based deployment model where ArgoCD continuously monitors Git and automatically syncs changes to the cluster:

```
Git Repository (Source of Truth)
      ↓
ArgoCD Watches for Changes
      ↓
Automatic Sync to Kubernetes
      ↓
Drift Detection & Self-Healing
```

This approach provides complete audit trails through Git history, easy rollbacks via Git reverts, and automatic drift correction when cluster state diverges from the declared manifests.

### Self-Healing Demonstration

The workflow includes an automated self-healing test:
1. Deploy application with 2 replicas (declared in Git)
2. Manually scale to 5 replicas (simulate configuration drift)
3. ArgoCD detects the divergence from Git
4. System automatically reverts to the declared state (2 replicas)

### Production Patterns

- **Health Probes**: Liveness, readiness, and startup probes ensure reliability
- **Resource Constraints**: CPU and memory requests/limits for proper scheduling
- **Horizontal Scaling**: HPA automatically adjusts replicas based on utilization
- **Pod Anti-Affinity**: Distribute pods across nodes for high availability
- **Custom Metrics**: Prometheus-compatible metrics instrumentation for monitoring

## Deployed Services

### ML Inference API

FastAPI-based sentiment analysis service with the following endpoints:

- `GET /health` - Health check for liveness probes
- `GET /ready` - Readiness check for traffic routing
- `POST /predict` - Single text sentiment analysis
- `POST /predict/batch` - Batch processing for multiple texts
- `GET /metrics` - Prometheus-compatible metrics exposition

**Example request:**
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This GitOps demo is amazing!"}'
```

**Response:**
```json
{
  "text": "This GitOps demo is amazing!",
  "sentiment": "positive",
  "confidence": 0.85,
  "processing_time_ms": 12.34,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Observability Stack

- **VictoriaMetrics**: High-performance time-series database with 15-second scrape interval
  - Prometheus-compatible query language (PromQL)
  - Lower resource usage compared to Prometheus
  - Better compression and faster queries
- **Grafana**: Visualization dashboards
- **Metrics tracked**:
  - Request rate and throughput
  - Latency percentiles (p95, p99)
  - Active concurrent requests
  - Error rates and HTTP status codes

## Additional Workflows

### Live GitOps Dashboard

Real-time monitoring dashboard streaming deployment progress via Server-Sent Events. The main workflow includes an integrated dashboard job that provides a public URL (via Cloudflare Tunnel) for observing ArgoCD sync status, Kubernetes pod lifecycle, and deployment progress in real-time.

**Standalone Workflow:** `.github/workflows/live-gitops-dashboard.yml`
**Integrated:** Available as parallel job in main `gitops-demo.yml` workflow

### Debug SSH Access

Interactive debugging via tmate for troubleshooting:

- Direct SSH access to GitHub Actions runner
- Optional Minikube cluster setup
- Limited to workflow initiator
- 20-minute session timeout

**Workflow:** `.github/workflows/debug-ssh-access.yml`
**Documentation:** [docs/DEBUG-WORKFLOW.md](docs/DEBUG-WORKFLOW.md)

## Technologies

| Category | Technology |
|----------|------------|
| **GitOps** | ArgoCD |
| **Container Orchestration** | Kubernetes (Minikube) |
| **CI/CD** | GitHub Actions |
| **ML Framework** | FastAPI, Python |
| **Monitoring** | VictoriaMetrics, Grafana |
| **Container Registry** | GitHub Container Registry (GHCR) |
| **Languages** | Python, YAML, Bash |

## Documentation

- **[Workflow Architecture](docs/WORKFLOW-ARCHITECTURE.md)** - CI/CD pipeline design and parallelization
- **[Live Dashboard](docs/LIVE-DASHBOARD.md)** - Real-time deployment monitoring
- **[Debug Workflow](docs/DEBUG-WORKFLOW.md)** - SSH-based debugging

## License

MIT License - see [LICENSE](LICENSE) file
