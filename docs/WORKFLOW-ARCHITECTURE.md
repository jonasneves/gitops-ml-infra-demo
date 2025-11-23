# Workflow Architecture

Parallelized GitHub Actions workflow optimized for efficiency and reliability.

## Pipeline Overview

```mermaid
graph LR
    Build["Build<br/>(10 min)"]
    Deploy["Deploy<br/>(15 min)"]
    Test["Test<br/>(10 min)"]
    Demo["Demo<br/>(10 min)"]
    Report["Report<br/>(5 min)"]

    Build --> Deploy
    Deploy --> Test
    Deploy --> Demo
    Test --> Report
    Demo --> Report

    style Build fill:#3776ab,stroke:#333,stroke-width:2px,color:#fff
    style Deploy fill:#326ce5,stroke:#333,stroke-width:2px,color:#fff
    style Test fill:#009688,stroke:#333,stroke-width:2px,color:#fff
    style Demo fill:#ef7b4d,stroke:#333,stroke-width:2px,color:#fff
    style Report fill:#f05032,stroke:#333,stroke-width:2px,color:#fff
```

**Total Duration:** ~15 minutes (vs ~25 minutes sequential)

**Time Savings:** 40% reduction through parallelization

## Job Dependencies

```mermaid
graph TB
    subgraph Legend
        direction LR
        P["Runs in Parallel"]
        S["Sequential Dependency"]
        A["Always Runs"]
    end

    Build["build<br/>no dependencies"]
    Deploy["deploy<br/>needs: [build]"]
    Test["test<br/>needs: [deploy]"]
    Demo["demo<br/>needs: [deploy]"]
    Report["report<br/>needs: [test]<br/>if: always()"]

    Build --> Deploy
    Deploy --> Test
    Deploy --> Demo
    Test --> Report
    Demo -.->|no dependency| Report

    style Build fill:#3776ab,stroke:#333,stroke-width:2px,color:#fff
    style Deploy fill:#326ce5,stroke:#333,stroke-width:2px,color:#fff
    style Test fill:#009688,stroke:#333,stroke-width:2px,color:#fff
    style Demo fill:#ef7b4d,stroke:#333,stroke-width:2px,color:#fff
    style Report fill:#f05032,stroke:#333,stroke-width:2px,color:#fff
```

## Jobs

### Build
- Build Docker image with buildx
- Push to GHCR with layer caching
- Output: image tag and digest

### Deploy
- Start Minikube cluster
- Install ArgoCD
- Deploy ML inference and observability via ArgoCD
- Save cluster state artifacts

### Test
- Fresh Minikube cluster
- Deploy and test endpoints: `/health`, `/ready`, `/predict`
- Verify Prometheus metrics
- Upload test results

### Demo
- Fresh Minikube cluster
- Demonstrates GitOps self-healing:
  1. Deploy with 2 replicas
  2. Manually scale to 5 (simulate drift)
  3. ArgoCD detects out-of-sync state
  4. Auto-reverts to 2 replicas (declarative healing)
- Only runs with `demo_mode: full`

**Self-Healing Flow:**

```mermaid
sequenceDiagram
    participant Git as Git Repository
    participant ArgoCD as ArgoCD
    participant K8s as Kubernetes

    Git->>ArgoCD: Declares 2 replicas
    ArgoCD->>K8s: Sync deployment (2 replicas)
    Note over K8s: Manual change
    K8s->>K8s: Scale to 5 replicas (drift)
    ArgoCD->>K8s: Detect drift (health check)
    Note over ArgoCD: Out of sync detected
    ArgoCD->>K8s: Auto-sync back to 2 replicas
    Note over K8s: Self-healed to desired state
```

### Report
- Download all artifacts
- Generate comprehensive report
- Comment on PR if applicable
- Runs even if other jobs fail

## Workflow Triggers

```mermaid
graph LR
    Schedule["Daily Schedule<br/>(9:00 AM UTC)"]
    Manual["Manual Dispatch<br/>(workflow_dispatch)"]
    Push["Push to main"]

    Schedule --> Workflow
    Manual --> Workflow
    Push --> Workflow

    Workflow["GitOps Demo<br/>Workflow"]

    style Schedule fill:#f39c12,stroke:#333,stroke-width:2px,color:#fff
    style Manual fill:#3498db,stroke:#333,stroke-width:2px,color:#fff
    style Push fill:#e74c3c,stroke:#333,stroke-width:2px,color:#fff
    style Workflow fill:#2ecc71,stroke:#333,stroke-width:2px,color:#fff
```

- **Schedule**: Daily at 9:00 AM UTC (automated validation)
- **Manual**: workflow_dispatch with demo_mode option
- **Push**: Triggered on push to main branch

## Artifacts

| Job | Artifact | Contents |
|-----|----------|----------|
| Deploy | cluster-state | Kubeconfig, ArgoCD password |
| Test | test-results | Pod status, logs, events |
| Demo | demo-artifacts | ArgoCD state, history |
| Report | final-demo-report | Complete report |
