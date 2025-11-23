# Debug SSH Access

SSH into a GitHub Actions runner for interactive debugging via tmate.

## Quick Start

1. Go to **Actions** > **Debug SSH Access**
2. Click **Run workflow**
3. Configure options:
   - Enable tmate session (default: on)
   - Setup Minikube cluster (default: on)
   - Build Docker container (default: off)
4. Find connection string in logs:
   ```
   SSH: ssh ABC123@nyc1.tmate.io
   Web: https://tmate.io/t/ABC123
   ```

## Common Tasks

### Explore Cluster
```bash
kubectl cluster-info
kubectl get nodes
kubectl get pods -A
```

### Debug Deployments
```bash
kubectl describe deployment ml-inference -n ml-inference
kubectl logs -f deployment/ml-inference -n ml-inference
kubectl get events -n ml-inference --sort-by='.lastTimestamp'
```

### Test ArgoCD
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s

# Get password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### Test API
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is amazing!"}'
```

## Session Management

**Exit session:** Create a file to continue workflow:
```bash
touch continue
```

**Timeout:** 20 minutes default, 30 minutes max.

## Troubleshooting

**Permission denied:** Ensure SSH keys are registered with GitHub account.

**Session not found:** Session expired - re-run workflow.

**Container not starting:** Check `docker logs ml-inference` and `free -h`.
