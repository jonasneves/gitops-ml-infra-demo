# GitOps ML Infrastructure Demo

[![ArgoCD](https://img.shields.io/badge/ArgoCD-EF7B4D?logo=argo&logoColor=white)](https://argoproj.github.io/cd/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![VictoriaMetrics](https://img.shields.io/badge/VictoriaMetrics-621773?logo=victoriametrics&logoColor=white)](https://victoriametrics.com/)
[![Grafana](https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white)](https://grafana.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://python.org/)

**CI/CD Pipeline:**</br>
[![GitOps Demo](https://github.com/jonasneves/gitops-ml-infra-demo/actions/workflows/gitops-demo.yml/badge.svg)](https://github.com/jonasneves/gitops-ml-infra-demo/actions/workflows/gitops-demo.yml)

**Live Status:**</br>
[![Deployment](https://img.shields.io/endpoint?url=https://gitops.neevs.io/api/badge/deployment)](https://gitops.neevs.io)
[![ArgoCD](https://img.shields.io/endpoint?url=https://gitops.neevs.io/api/badge/argocd)](https://gitops.neevs.io)
[![Health](https://img.shields.io/endpoint?url=https://gitops.neevs.io/api/badge/health)](https://gitops.neevs.io)
[![Pods](https://img.shields.io/endpoint?url=https://gitops.neevs.io/api/badge/pods)](https://gitops.neevs.io)

**Production-grade ML infrastructure implementing GitOps practices with ArgoCD, Kubernetes, and automated CI/CD pipelines.**

Built entirely on GitHub Actions free tier, this project demonstrates modern infrastructure patterns including declarative deployments, self-healing systems, and real-time observability.

## Overview

- **GitOps Deployment**: ArgoCD continuously syncs Kubernetes manifests from Git
- **Automated CI/CD**: Parallelized GitHub Actions workflows
- **ML Inference Service**: FastAPI sentiment analysis API with metrics
- **Observability**: VictoriaMetrics + Grafana monitoring stack
- **Live Dashboard**: Real-time deployment tracking via Server-Sent Events
- **Self-Healing**: Automatic drift detection and correction

## Architecture

```mermaid
graph TB
    subgraph GitHub["GitHub Actions Runner"]
        subgraph Cluster["Minikube Cluster"]
            ArgoCD["ArgoCD<br/>(GitOps Controller)"]
            ML["ML Inference Service<br/>(HPA-scaled replicas)"]
            Obs["Observability Stack<br/>(VictoriaMetrics + Grafana)"]

            ArgoCD -->|watches & syncs| ML
        end
    end

    Git["Git Repository<br/>(Kubernetes Manifests)"] -->|monitors| ArgoCD

    style ArgoCD fill:#ef7b4d,stroke:#333,stroke-width:2px,color:#fff
    style ML fill:#009688,stroke:#333,stroke-width:2px,color:#fff
    style Obs fill:#326ce5,stroke:#333,stroke-width:2px,color:#fff
    style Git fill:#f05032,stroke:#333,stroke-width:2px,color:#fff
```

### CI/CD Pipeline

```mermaid
graph TB
    Build["Build Job<br/>(8 min)"]
    Deploy["Deploy Job"]
    Test["Test Job"]
    Demo["Demo Job"]
    Report["Report Job"]

    Build --> Deploy
    Build --> Test
    Build --> Demo
    Deploy --> Report
    Test --> Report
    Demo --> Report

    style Build fill:#3776ab,stroke:#333,stroke-width:2px,color:#fff
    style Deploy fill:#326ce5,stroke:#333,stroke-width:2px,color:#fff
    style Test fill:#009688,stroke:#333,stroke-width:2px,color:#fff
    style Demo fill:#ef7b4d,stroke:#333,stroke-width:2px,color:#fff
    style Report fill:#f05032,stroke:#333,stroke-width:2px,color:#fff
```

Jobs run in parallel after build completion for optimal performance.

## Quick Start

**GitHub Actions (Recommended):**
1. Go to [Actions tab](../../actions/workflows/gitops-demo.yml)
2. Click "Run workflow"
3. Monitor the deployment (~10 min)

**Local:** See [Deployment Guide](docs/DEPLOYMENT.md)

## Project Structure

```
.
├── .github/workflows/
│   ├── gitops-demo.yml              # Main GitOps workflow
│   ├── live-server.yml              # Public hosting via Cloudflare
│   └── debug-ssh-access.yml         # SSH debugging
│
├── app/ml-inference/
│   ├── app.py                       # FastAPI service
│   └── Dockerfile
│
├── k8s/
│   ├── inference-service/           # ML service manifests
│   └── observability/               # Monitoring stack
│
├── scripts/
│   └── dashboard_server.py          # Live dashboard server
│
└── docs/                            # Documentation
```

## Key Features

### GitOps Workflow
Pull-based deployment model where ArgoCD monitors Git and syncs changes automatically, providing complete audit trails and easy rollbacks.

### Self-Healing
Automatic drift detection and correction when cluster state diverges from Git-declared manifests.

### Production Patterns
- Health probes (liveness, readiness, startup)
- Horizontal Pod Autoscaler
- Resource constraints
- Prometheus-compatible metrics

## Technologies

| Category | Technology |
|----------|------------|
| GitOps | ArgoCD |
| Orchestration | Kubernetes (Minikube) |
| CI/CD | GitHub Actions |
| ML Service | FastAPI, Python |
| Monitoring | VictoriaMetrics, Grafana |
| Registry | GitHub Container Registry |

## Documentation

- **[API Reference](docs/API.md)** - ML inference endpoints and examples
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Local and CI/CD setup
- **[Workflow Architecture](docs/WORKFLOW-ARCHITECTURE.md)** - CI/CD pipeline design
- **[Live Server](docs/LIVE-SERVER.md)** - Public hosting via Cloudflare Tunnel
- **[Modular Infrastructure](docs/MODULAR-INFRASTRUCTURE.md)** - Distributed architecture patterns
- **[Debug Workflow](docs/DEBUG-WORKFLOW.md)** - SSH-based debugging

## License

MIT License - see [LICENSE](LICENSE)
