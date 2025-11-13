# GitHub Actions Workflow Architecture

## 🎯 Parallelized Multi-Job Design

This document explains how the GitOps demo workflow is structured for maximum efficiency using GitHub Actions parallelization.

## 📊 Workflow Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                       │
│                   (gitops-demo.yml)                              │
└─────────────────────────────────────────────────────────────────┘

                              START
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Job 1: Build 🏗️     │
                    │   (10 minutes)        │
                    │                       │
                    │  • Docker buildx      │
                    │  • Build ML image     │
                    │  • Push to GHCR       │
                    │  • Cache layers       │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Job 2: Deploy 🚀    │
                    │   (15 minutes)        │
                    │                       │
                    │  • Start Minikube     │
                    │  • Install ArgoCD     │
                    │  • Deploy ML service  │
                    │  • Deploy monitoring  │
                    │  • Save cluster state │
                    └───────────┬───────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
        ┌───────────────────┐   ┌───────────────────┐
        │ Job 3a: Test 🧪   │   │ Job 3b: Demo 🎭   │
        │ (10 minutes)      │   │ (10 minutes)      │
        │                   │   │                   │
        │ • New Minikube    │   │ • New Minikube    │
        │ • Deploy app      │   │ • Deploy app      │
        │ • Health checks   │   │ • Scale up        │
        │ • API tests       │   │ • Show drift      │
        │ • Metrics verify  │   │ • Auto-heal       │
        │ • Upload results  │   │ • Upload results  │
        └─────────┬─────────┘   └─────────┬─────────┘
                  │                       │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │ Job 4: Report 📊      │
                  │ (5 minutes)           │
                  │                       │
                  │ • Download artifacts  │
                  │ • Generate report     │
                  │ • Comment on PR       │
                  │ • Upload final docs   │
                  └───────────────────────┘
                              │
                              ▼
                             END

         TOTAL TIME: ~15 minutes (with parallelization)
         vs. ~25 minutes (sequential execution)
```

## 🔗 Job Dependencies

```yaml
build:
  - No dependencies (runs first)

deploy:
  needs: [build]
  - Waits for build to complete
  - Uses the built Docker image

test:
  needs: [deploy]
  - Runs in parallel with demo
  - Creates fresh test environment

demo:
  needs: [deploy]
  - Runs in parallel with test
  - Optional (controlled by input)
  - Creates separate demo environment

report:
  needs: [build, deploy, test]
  if: always()
  - Runs after test completes
  - Runs even if jobs fail
  - Aggregates all results
```

## ⚡ Parallelization Benefits

### Time Savings

| Execution Mode | Duration | Jobs Running |
|---------------|----------|--------------|
| **Sequential** | ~25 minutes | 1 at a time |
| **Parallelized** | ~15 minutes | Up to 2 concurrent |

**Savings: 40% faster** ⚡

### Cost Efficiency

GitHub Actions free tier:
- 2,000 minutes/month for public repos
- Jobs run concurrently but count individually

Example:
- Old workflow: 25 min × 4 runs = 100 minutes
- New workflow: 15 min × 4 runs = 60 minutes
- **Savings: 40 minutes per 4 runs**

### Resource Isolation

Each job runs on a separate runner:
- **Build**: Needs Docker buildx, no Kubernetes
- **Deploy**: Needs full cluster for setup
- **Test**: Fresh cluster for clean testing
- **Demo**: Isolated environment for self-healing demo

## 🎯 Job Details

### Job 1: Build (🏗️)

**Purpose**: Build and publish Docker image

**Runs on**: ubuntu-latest
**Timeout**: 10 minutes
**Permissions**: `contents: read`, `packages: write`

**Key Steps**:
1. Checkout code
2. Setup Docker Buildx
3. Login to GHCR
4. Build and push ML inference image with caching

**Outputs**:
- `image-tag`: Docker image tags
- `image-digest`: Image digest for verification

**Artifacts**: None

---

### Job 2: Deploy (🚀)

**Purpose**: Deploy complete infrastructure

**Runs on**: ubuntu-latest
**Timeout**: 15 minutes
**Permissions**: `contents: read`
**Depends on**: build

**Key Steps**:
1. Start Minikube cluster
2. Install ArgoCD
3. Deploy ML inference via ArgoCD
4. Deploy observability stack
5. Verify deployments
6. Save cluster state

**Outputs**: None

**Artifacts**:
- `cluster-state/`: Kubeconfig, ArgoCD password, resource snapshots

---

### Job 3a: Test (🧪)

**Purpose**: Validate ML inference service

**Runs on**: ubuntu-latest
**Timeout**: 10 minutes
**Permissions**: `contents: read`
**Depends on**: deploy
**Runs in parallel with**: demo

**Key Steps**:
1. Create fresh Minikube cluster
2. Install ArgoCD and deploy app
3. Test `/health` endpoint
4. Test `/ready` endpoint
5. Test `/predict` (single inference)
6. Test `/predict/batch` (batch inference)
7. Verify Prometheus metrics

**Outputs**: None

**Artifacts**:
- `test-results/`: Pod status, logs, events

---

### Job 3b: Demo (🎭)

**Purpose**: Demonstrate GitOps self-healing

**Runs on**: ubuntu-latest
**Timeout**: 10 minutes
**Permissions**: `contents: read`
**Depends on**: deploy
**Runs in parallel with**: test
**Condition**: Only on `workflow_dispatch` with `demo_mode: full`

**Key Steps**:
1. Create fresh Minikube cluster
2. Install ArgoCD and deploy app
3. Record original replica count
4. Manually scale deployment (simulate drift)
5. Show ArgoCD detects out-of-sync state
6. Wait for ArgoCD to auto-heal
7. Verify replicas restored to Git state

**Outputs**: None

**Artifacts**:
- `demo-artifacts/`: ArgoCD state, history, events

---

### Job 4: Report (📊)

**Purpose**: Aggregate results and generate final report

**Runs on**: ubuntu-latest
**Timeout**: 5 minutes
**Permissions**: `contents: read`, `pull-requests: write`
**Depends on**: build, deploy, test
**Condition**: `always()` (runs even if other jobs fail)

**Key Steps**:
1. Download all artifacts from previous jobs
2. Generate comprehensive demo report
3. Include job status (success/failure)
4. Create architecture diagram
5. Comment on PR (if applicable)

**Outputs**: None

**Artifacts**:
- `final-demo-report/`: Complete report with all results

## 🧪 Running the Workflow

### Manual Trigger

```bash
# Via GitHub UI
1. Go to Actions tab
2. Select "GitOps Infrastructure Demo"
3. Click "Run workflow"
4. Choose demo_mode: full or quick
5. Click "Run workflow"
```

### Automatic Triggers

- **Push to main**: Runs all jobs
- **Push to claude/gitops-* branches**: Runs all jobs
- **Pull Request**: Runs all jobs, posts results as comment

## 📈 Monitoring

### View Job Status

Each job shows status independently:
- ✅ **Success**: Job completed without errors
- ❌ **Failure**: Job failed (check logs)
- ⚠️ **Skipped**: Job was skipped (e.g., demo when mode=quick)
- ⏸️ **Cancelled**: Workflow was cancelled

### Download Artifacts

After workflow completes:
1. Go to workflow run page
2. Scroll to "Artifacts" section
3. Download:
   - `cluster-state` (from deploy job)
   - `test-results` (from test job)
   - `demo-artifacts` (from demo job, if ran)
   - `final-demo-report` (from report job)

## 🔧 Customization

### Adjust Parallelization

To run test and demo sequentially instead of parallel:

```yaml
demo:
  needs: [deploy, test]  # Add test as dependency
```

### Skip Demo Job

Demo only runs when:
- Event is `workflow_dispatch` AND `demo_mode` is `full`

To always run demo:

```yaml
demo:
  if: always()  # Remove conditional
```

### Add New Parallel Job

Example: Add a security scan job:

```yaml
security-scan:
  name: 🔒 Security Scan
  runs-on: ubuntu-latest
  needs: build  # Run after build completes
  # Runs in parallel with deploy

  steps:
    - name: Run Trivy scan
      uses: aquasecurity/trivy-action@master
      # ... scan steps
```

## 💡 Best Practices

### ✅ Do

- Keep jobs focused on single responsibility
- Use artifacts to share data between jobs
- Set appropriate timeouts for each job
- Add `if: always()` to cleanup/report jobs
- Use `needs:` to define dependencies explicitly

### ❌ Don't

- Don't share state via external storage
- Don't create circular dependencies
- Don't run long-running processes without timeout
- Don't store secrets in artifacts

## 🎓 Learning Outcomes

This workflow demonstrates:

1. **Job orchestration** - Dependencies and parallelization
2. **Resource efficiency** - Separate runners for different tasks
3. **Fault tolerance** - Report runs even if tests fail
4. **Artifact management** - Sharing data between jobs
5. **Conditional execution** - Optional jobs based on inputs
6. **Clean architecture** - Separation of concerns

Perfect for showing in interviews! 🚀
