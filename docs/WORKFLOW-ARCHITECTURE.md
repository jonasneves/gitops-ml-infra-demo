# Workflow Architecture

Parallelized GitHub Actions workflow for maximum efficiency.

## Pipeline Overview

```
Build (10 min)
    │
    └─► Deploy (15 min)
            │
            ├─► Test (10 min)     ─┐
            │                      ├─► Report (5 min)
            └─► Demo (10 min)     ─┘
```

**Total: ~15 minutes** (vs ~25 minutes sequential)

## Job Dependencies

```yaml
build:     []           # Runs first
deploy:    [build]      # After build
test:      [deploy]     # Parallel with demo
demo:      [deploy]     # Parallel with test
report:    [test]       # After test (always runs)
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
- Demonstrate GitOps self-healing:
  1. Deploy with 2 replicas
  2. Manually scale to 5 (simulate drift)
  3. ArgoCD detects out-of-sync
  4. Auto-reverts to 2 replicas
- Only runs with `demo_mode: full`

### Report
- Download all artifacts
- Generate comprehensive report
- Comment on PR if applicable
- Runs even if other jobs fail

## Triggers

- **Schedule**: Daily at 9:00 AM UTC
- **Manual**: workflow_dispatch with demo_mode option
- **Push**: main branch

## Artifacts

| Job | Artifact | Contents |
|-----|----------|----------|
| Deploy | cluster-state | Kubeconfig, ArgoCD password |
| Test | test-results | Pod status, logs, events |
| Demo | demo-artifacts | ArgoCD state, history |
| Report | final-demo-report | Complete report |
