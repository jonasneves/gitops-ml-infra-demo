# GitOps ML Infrastructure Demo

[![GitOps Demo](https://github.com/GITHUB_USERNAME/eks-ml-inference-platform/actions/workflows/gitops-demo.yml/badge.svg)](https://github.com/GITHUB_USERNAME/eks-ml-inference-platform/actions/workflows/gitops-demo.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**A production-ready ML infrastructure demo using GitOps practices with ArgoCD, Kubernetes, and GitHub Actions.**

🎯 **Zero cost** - Runs entirely in GitHub Actions free tier
⚡ **Fully automated** - One-click deployment demonstration
📊 **Production patterns** - GitOps, observability, auto-scaling
🚀 **Live demos** - [View workflow runs](../../actions/workflows/gitops-demo.yml)

## 🎬 Try It Now

Click the **Actions** tab above → Select **GitOps Infrastructure Demo** → Click **Run workflow**

Watch as the system:
1. Creates a Kubernetes cluster (Minikube)
2. Installs ArgoCD GitOps controller
3. Deploys ML inference service automatically
4. Sets up Prometheus + Grafana observability
5. Demonstrates self-healing infrastructure

**Results available as downloadable artifacts** after each run!

## 🏗️ Architecture

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
│  │  │   - Prometheus Metrics       │ │  │
│  │  └──────────────────────────────┘ │  │
│  │                                    │  │
│  │  ┌──────────────────────────────┐ │  │
│  │  │   Observability Stack        │ │  │
│  │  │   - Prometheus (metrics)     │ │  │
│  │  │   - Grafana (visualization)  │ │  │
│  │  └──────────────────────────────┘ │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
            ▲
            │ Git Repository (Single Source of Truth)
            │
     Changes → ArgoCD Auto-Syncs
```

## ✨ What This Demonstrates

### GitOps Practices
- ✅ **Declarative Infrastructure** - Everything defined in Git
- ✅ **ArgoCD** - Automated deployment and drift detection
- ✅ **Self-Healing** - Automatic correction of manual changes
- ✅ **Git as Source of Truth** - All changes auditable
- ✅ **Continuous Deployment** - Automatic sync on git push

### Production ML Operations
- ✅ **Container Orchestration** - Kubernetes deployment patterns
- ✅ **ML Model Serving** - FastAPI inference API
- ✅ **Auto-Scaling** - HPA based on CPU/memory
- ✅ **Health Checks** - Liveness, readiness, startup probes
- ✅ **Resource Management** - Requests and limits

### Observability
- ✅ **Prometheus** - Metrics collection and alerting
- ✅ **Grafana** - Dashboard visualization
- ✅ **Custom Metrics** - Application-specific monitoring
- ✅ **Service Discovery** - Automatic endpoint detection

### CI/CD Automation
- ✅ **GitHub Actions** - Fully automated workflows
- ✅ **Container Building** - Docker image creation
- ✅ **GHCR Integration** - GitHub Container Registry
- ✅ **Automated Testing** - Health check validation
- ✅ **Artifact Generation** - Downloadable results

## 🚀 Quick Start

### Option 1: GitHub Actions (Recommended)

**For Recruiters/Interviewers:**
1. Visit the [Actions tab](../../actions/workflows/gitops-demo.yml)
2. Click "Run workflow"
3. Watch the live demonstration
4. Download artifacts to see full results

**Duration:** ~8-10 minutes
**Cost:** $0 (GitHub Actions free tier)

### Option 2: Local Deployment

```bash
# Prerequisites: Docker, kubectl, minikube

# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/eks-ml-inference-platform.git
cd eks-ml-inference-platform

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
  --repo https://github.com/YOUR_USERNAME/eks-ml-inference-platform \
  --path k8s/inference-service \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace ml-inference \
  --sync-policy automated
```

## 📁 Project Structure

```
.
├── .github/workflows/
│   └── gitops-demo.yml          # Automated GitOps demonstration
│
├── app/ml-inference/
│   ├── app.py                   # FastAPI ML inference service
│   ├── requirements.txt
│   └── Dockerfile
│
├── k8s/
│   ├── inference-service/       # ML service manifests
│   │   ├── deployment.yaml      # Pod specification
│   │   ├── service.yaml         # ClusterIP service
│   │   ├── hpa.yaml             # Auto-scaling config
│   │   └── servicemonitor.yaml  # Prometheus scraping
│   │
│   └── observability/           # Monitoring stack
│       ├── prometheus-deployment.yaml
│       └── grafana-deployment.yaml
│
├── docs/
│   ├── GITOPS.md               # GitOps concepts explained
│   └── DEMO-GUIDE.md           # How to present this
│
└── README.md
```

## 🎓 Key Concepts Demonstrated

### 1. GitOps Workflow

**Traditional Deployment:**
```
Developer → kubectl apply → Cluster
```

**GitOps Approach:**
```
Developer → Git Push → ArgoCD watches Git → Syncs to Cluster
```

**Benefits:**
- Audit trail (Git history)
- Easy rollback (Git revert)
- Drift detection
- Declarative infrastructure

### 2. Self-Healing

The demo includes a self-healing demonstration:
1. Application deployed with 2 replicas (defined in Git)
2. Manual scale to 5 replicas (simulating drift)
3. ArgoCD detects difference from Git
4. ArgoCD automatically reverts to 2 replicas

### 3. Production Patterns

- **Health Checks**: Liveness, readiness, and startup probes
- **Resource Limits**: CPU and memory constraints
- **Auto-scaling**: HPA based on resource utilization
- **Pod Anti-Affinity**: Distribute pods across nodes
- **Prometheus Metrics**: Custom application metrics

## 📊 What Gets Deployed

### ML Inference Service

- **FastAPI** application with sentiment analysis
- **Endpoints**:
  - `GET /health` - Health check
  - `GET /ready` - Readiness check
  - `POST /predict` - Single text inference
  - `POST /predict/batch` - Batch inference
  - `GET /metrics` - Prometheus metrics

- **Example Usage**:
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This GitOps demo is amazing!"}'

# Response:
{
  "text": "This GitOps demo is amazing!",
  "sentiment": "positive",
  "confidence": 0.85,
  "processing_time_ms": 12.34,
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Observability Stack

- **Prometheus**: Scrapes metrics from ML service every 15s
- **Grafana**: Visualizes metrics with pre-configured dashboards
- **Dashboards**:
  - Request rate
  - Latency (p95, p99)
  - Active requests
  - Error rates

## 🎯 Use Cases

### For Students
- Learn GitOps practices
- Understand Kubernetes patterns
- Build portfolio project
- **Cost**: $0

### For Job Seekers
- Demonstrate infrastructure skills
- Show in interviews
- Prove automation expertise
- Link in resume/LinkedIn

### For Interviews
1. Show the GitHub Actions workflow running
2. Explain GitOps principles
3. Walk through Kubernetes manifests
4. Discuss production considerations
5. Download and show artifacts

**Demo Duration**: 5-10 minutes
**Talking Points**: See [docs/DEMO-GUIDE.md](docs/DEMO-GUIDE.md)

## 🛠️ Technologies

| Category | Technology |
|----------|------------|
| **GitOps** | ArgoCD |
| **Container Orchestration** | Kubernetes (Minikube) |
| **CI/CD** | GitHub Actions |
| **ML Framework** | FastAPI, Python |
| **Monitoring** | Prometheus, Grafana |
| **Container Registry** | GitHub Container Registry (GHCR) |
| **Languages** | Python, YAML, Bash |

## 📚 Documentation

- **[GitOps Explained](docs/GITOPS.md)** - Understand GitOps principles
- **[Demo Guide](docs/DEMO-GUIDE.md)** - How to present this in interviews
- **[Local Setup](docs/LOCAL-SETUP.md)** - Run on your machine

## 🌟 Why This Approach?

### Advantages over Traditional Demos

| Traditional | GitOps Demo |
|-------------|-------------|
| Requires AWS account | GitHub Actions only |
| Costs $50-200/month | Completely free |
| Manual deployment | Automated workflow |
| Static screenshots | Live demonstrations |
| Hard to reproduce | One-click repeatable |
| No audit trail | Full Git history |

### What Recruiters See

✅ **GitOps expertise** - Modern deployment practice
✅ **Kubernetes mastery** - Production patterns
✅ **CI/CD automation** - Full pipeline
✅ **ML operations** - Model serving infrastructure
✅ **Observability** - Monitoring and metrics
✅ **Documentation** - Clear communication

## 🎤 Interview Talking Points

**"Tell me about this project":**

> "This demonstrates production ML infrastructure using GitOps practices. Instead of manually deploying with kubectl, everything is defined in Git and automatically synced by ArgoCD. The workflow runs in GitHub Actions, creating a Kubernetes cluster, deploying a sentiment analysis API, and setting up full observability. It shows I understand not just ML, but the infrastructure needed to run it reliably in production."

**"Why GitOps?":**

> "GitOps provides several benefits: Git becomes the single source of truth with full audit trails, rollbacks are just a git revert, and drift detection ensures the cluster matches what's in Git. It's how modern companies like Anthropic and OpenAI manage their infrastructure at scale."

**"What would you add for production?":**

> "For production, I'd add: secrets management with Sealed Secrets or AWS Secrets Manager, multi-environment support (dev/staging/prod), integration testing in CI, automated rollback on health check failures, and monitoring with actual alerting to PagerDuty/Slack."

## 📈 Project Metrics

- **Files**: ~15 (concise, focused)
- **Lines of Code**: ~1,000
- **Deployment Time**: 8-10 minutes
- **Technologies**: 7+
- **Cost**: $0
- **Runs**: Unlimited (GitHub Actions free tier)

## 🤝 Contributing

This is a portfolio/demo project. Feel free to fork and customize for your own use!

## 📄 License

MIT License - see [LICENSE](LICENSE) file
