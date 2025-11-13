# 🔧 Debug SSH Access Workflow

This workflow allows you to SSH into a GitHub Actions runner to debug and explore the environment interactively.

## 🚀 Quick Start

1. **Navigate to Actions tab** in your GitHub repository
2. **Select "🔧 Debug SSH Access"** workflow
3. **Click "Run workflow"** button
4. **Configure options:**
   - ✅ Enable tmate debugging session (default: on)
   - ✅ Setup Minikube cluster (default: on)
   - ⬜ Build and run Docker container (default: off)

5. **Click "Run workflow"** to start

## 📡 Connecting via SSH

Once the workflow starts, look for the tmate connection string in the logs:

```
Setup tmate session
SSH: ssh ABC123@nyc1.tmate.io
Web: https://tmate.io/t/ABC123
```

**Connect via SSH:**
```bash
ssh ABC123@nyc1.tmate.io
```

**Or use your browser:**
Open the Web URL in your browser for a web-based terminal.

## 🎯 Use Cases

### 1. **Explore GitHub Actions Runner**
Connect and explore the Ubuntu 22.04 environment:
```bash
# See what's installed
which kubectl docker minikube
docker version
kubectl version

# Check available resources
free -h
df -h
nproc
```

### 2. **Debug Minikube Cluster**
If you enabled Minikube setup:
```bash
# Check cluster status
kubectl cluster-info
kubectl get nodes
kubectl get pods -A

# Deploy test application
kubectl create deployment nginx --image=nginx
kubectl expose deployment nginx --port=80
kubectl get all

# Access logs
kubectl logs -l app=nginx
```

### 3. **Test Docker Container**
If you enabled Docker container setup:
```bash
# Check running containers
docker ps

# Access container logs
docker logs ml-inference

# Execute commands in container
docker exec -it ml-inference /bin/sh

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is amazing!"}'
```

### 4. **Debug Kubernetes Manifests**
```bash
# Navigate to k8s manifests
cd k8s/inference-service

# Apply and test manifests
kubectl create namespace test
kubectl apply -f deployment.yaml -n test
kubectl get deployment -n test
kubectl describe deployment ml-inference -n test

# Check for issues
kubectl get events -n test --sort-by='.lastTimestamp'
```

### 5. **Test ArgoCD Installation**
```bash
# Install ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward (in background)
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Install CLI and test
curl -sSL -o argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x argocd
sudo mv argocd /usr/local/bin/
argocd version
```

## 🛠️ Advanced Usage

### Continue the Workflow
When you're done debugging, create a file to signal completion:
```bash
touch continue
```

The workflow will then proceed to the next step.

### Session Timeout
- **Default timeout:** 20 minutes
- **Maximum:** 30 minutes (workflow level)
- Session will automatically disconnect after timeout

### Security
- ✅ **Limited access:** Only you (the workflow trigger) can connect
- ✅ **SSH key authentication:** Uses your GitHub registered SSH keys
- ✅ **Temporary:** Session ends when workflow completes

## 💡 Tips

1. **Use `screen` or `tmux`** to create persistent sessions:
   ```bash
   screen -S debug
   # Detach: Ctrl+A, D
   # Reattach: screen -r debug
   ```

2. **Download files from the runner:**
   ```bash
   # On the runner, create files you want
   kubectl get all -A > cluster-state.txt

   # Then upload as artifact (won't work in tmate, but good to know)
   # Better: copy/paste or use GitHub gist
   ```

3. **Upload files to runner:**
   ```bash
   # Use curl or git to fetch files
   curl -O https://example.com/file.yaml
   git clone https://github.com/yourname/repo.git
   ```

4. **Monitor logs in real-time:**
   ```bash
   kubectl logs -f deployment/ml-inference -n ml-inference
   watch -n 2 kubectl get pods -A
   ```

## 🐛 Common Issues

### "Permission denied (publickey)"
- Make sure you have SSH keys registered with your GitHub account
- Use the correct SSH command from the logs
- Try the web URL if SSH doesn't work

### "Session not found"
- The session may have expired (20 min timeout)
- Re-run the workflow to create a new session

### Container not starting
- Check logs: `docker logs ml-inference`
- Check resources: `free -h` and `df -h`
- Verify image built: `docker images`

## 📚 Resources

- [action-tmate documentation](https://github.com/mxschmitt/action-tmate)
- [GitHub Actions runners specs](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners)
- [Minikube documentation](https://minikube.sigs.k8s.io/docs/)

## 🎓 Learning Exercises

Try these to learn more:

1. **Deploy a complete stack:**
   ```bash
   kubectl apply -f k8s/inference-service/
   kubectl apply -f k8s/observability/
   kubectl get all -A
   ```

2. **Simulate production issues:**
   ```bash
   # Kill a pod
   kubectl delete pod <pod-name> -n ml-inference
   # Watch it recover
   watch kubectl get pods -n ml-inference
   ```

3. **Test resource limits:**
   ```bash
   # Deploy with low memory
   kubectl set resources deployment ml-inference -n ml-inference \
     --limits=memory=50Mi --requests=memory=50Mi
   # Watch it get OOMKilled
   kubectl describe pod <pod-name> -n ml-inference
   ```

4. **Explore networking:**
   ```bash
   # Create a debug pod
   kubectl run debug --image=nicolaka/netshoot -it --rm
   # Inside pod:
   nslookup ml-inference.ml-inference.svc.cluster.local
   curl http://ml-inference.ml-inference.svc.cluster.local/health
   ```

---

**Happy Debugging! 🎉**
