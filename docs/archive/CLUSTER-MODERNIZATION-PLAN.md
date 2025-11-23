# Cluster Modernization Plan
## From Demo to Production-Grade ML Infrastructure

**Document Version:** 1.0
**Last Updated:** 2025-11-14
**Status:** Planning Phase
**Estimated Timeline:** 6-8 weeks
**Risk Level:** Medium

---

## 📋 Executive Summary

This document outlines a comprehensive plan to evolve the current GitOps ML infrastructure from a demonstration-quality setup to a production-grade, enterprise-ready system following patterns used by leading AI companies like Anthropic.

### Current State
- **Strengths:** Solid GitOps foundation, working CI/CD, basic observability
- **Gaps:** Single environment, limited security, no policy enforcement, basic logging
- **Technical Debt:** Flat directory structure, manual secret management, no multi-tenancy

### Target State
- **Multi-environment** deployment pipeline (dev → staging → prod)
- **Enterprise-grade security** with zero-trust networking and policy enforcement
- **Complete observability** stack (metrics + logs + traces)
- **Production patterns** for ML workloads (versioning, A/B testing, progressive delivery)
- **Operational excellence** with SLOs, runbooks, and incident response procedures

### Success Metrics
- **Deployment Velocity:** < 15 min from commit to production
- **Reliability:** 99.9% uptime SLO (error budget: 43 min/month)
- **Security:** 100% policy compliance, zero secrets in Git
- **Observability:** < 5 min mean time to detection (MTTD)
- **Developer Experience:** < 10 min for new developer onboarding

---

## 🎯 Strategic Objectives

| Objective | Why It Matters | Success Criteria |
|-----------|---------------|------------------|
| **Environment Segregation** | Prevent prod incidents from dev/test changes | 3 fully isolated environments operational |
| **Security Hardening** | Meet enterprise security standards | Pass security audit with zero critical findings |
| **Complete Observability** | Debug issues in < 5 minutes | Full request tracing from ingress to response |
| **ML-Specific Features** | Support rapid model iteration | Deploy new model versions with zero downtime |
| **Operational Excellence** | Reduce on-call burden by 80% | Automated remediation for 90% of common issues |

---

## 📅 Implementation Phases

### Phase 0: Foundation & Planning (Week 1)
**Goal:** Establish baseline and prepare for transformation

#### Architecture Decision Records (ADRs)

**Tasks:**
- [ ] Document current architecture baseline
- [ ] Create ADR-001: Why Kustomize over Helm
- [ ] Create ADR-002: VictoriaMetrics vs Prometheus
- [ ] Create ADR-003: Environment promotion strategy
- [ ] Create ADR-004: Secret management approach
- [ ] Create ADR-005: Service mesh evaluation (Istio vs Linkerd vs none)

**Success Criteria:**
- ✅ All architectural decisions documented with rationale
- ✅ Team alignment on implementation approach
- ✅ Risk register created and reviewed

**Deliverables:**
```
docs/
├── architecture/
│   ├── adr/
│   │   ├── 001-kustomize-over-helm.md
│   │   ├── 002-victoriametrics-rationale.md
│   │   ├── 003-environment-strategy.md
│   │   ├── 004-secrets-management.md
│   │   └── 005-service-mesh-decision.md
│   ├── current-state-diagram.md
│   └── target-state-diagram.md
└── CLUSTER-MODERNIZATION-PLAN.md (this file)
```

**Dependencies:** None
**Risk:** Low
**Rollback:** N/A (documentation only)

---

### Phase 1: Configuration Management & Structure (Week 1-2)
**Goal:** Reorganize infrastructure for scalability and maintainability

#### 1.1: Kustomize Migration

**Rationale:** Eliminate YAML duplication, enable environment-specific configurations without copy-paste

**Tasks:**
- [ ] Create base Kustomize configurations
- [ ] Define overlays for dev/staging/prod environments
- [ ] Migrate ml-inference deployment to Kustomize
- [ ] Migrate observability stack to Kustomize
- [ ] Update ArgoCD applications to use Kustomize
- [ ] Test builds for all environments

**Directory Structure:**
```
infrastructure/
├── base/                           # Environment-agnostic configs
│   ├── ml-inference/
│   │   ├── kustomization.yaml
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── hpa.yaml
│   │   └── servicemonitor.yaml
│   └── observability/
│       ├── kustomization.yaml
│       ├── victoriametrics/
│       ├── grafana/
│       └── loki/
├── overlays/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   └── patches/
│   │       ├── replicas.yaml      # 1 replica in dev
│   │       └── resources.yaml     # Lower limits
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   ├── namespace.yaml
│   │   └── patches/
│   │       ├── replicas.yaml      # 2 replicas in staging
│   │       └── resources.yaml     # Medium limits
│   └── prod/
│       ├── kustomization.yaml
│       ├── namespace.yaml
│       └── patches/
│           ├── replicas.yaml      # 5 replicas in prod
│           ├── resources.yaml     # Higher limits
│           └── policies.yaml      # Stricter policies
└── argocd/
    ├── projects/
    │   ├── ml-platform.yaml
    │   └── observability.yaml
    └── applications/
        ├── app-of-apps.yaml
        ├── ml-inference-dev.yaml
        ├── ml-inference-staging.yaml
        └── ml-inference-prod.yaml
```

**Testing Strategy:**
```bash
# Validate each overlay builds correctly
kustomize build infrastructure/overlays/dev
kustomize build infrastructure/overlays/staging
kustomize build infrastructure/overlays/prod

# Verify differences between environments
diff <(kustomize build infrastructure/overlays/dev) \
     <(kustomize build infrastructure/overlays/staging)

# Dry-run apply
kubectl apply --dry-run=client -k infrastructure/overlays/dev
```

**Success Criteria:**
- ✅ All environments build without errors
- ✅ Dev has 1 replica, staging has 2, prod has 5
- ✅ ArgoCD successfully syncs from Kustomize sources
- ✅ Zero YAML duplication between environments

**Rollback Plan:**
- Revert ArgoCD applications to point to `k8s/` directory
- Keep old `k8s/` directory for 2 weeks as backup

**Dependencies:** Phase 0 (ADR-001)
**Risk:** Medium (migration complexity)
**Estimated Effort:** 8-12 hours

---

#### 1.2: GitOps App-of-Apps Pattern

**Rationale:** Manage all ArgoCD applications declaratively, enabling one-command cluster bootstrap

**Tasks:**
- [ ] Create ArgoCD AppProject for ML platform
- [ ] Create ArgoCD AppProject for observability
- [ ] Define root Application (app-of-apps)
- [ ] Create Application per environment
- [ ] Test bootstrap from empty cluster

**App-of-Apps Structure:**
```yaml
# infrastructure/argocd/applications/app-of-apps.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/jonasneves/gitops-ml-infra-demo
    targetRevision: main
    path: infrastructure/argocd/applications
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**Testing:**
```bash
# Bootstrap entire cluster from single command
kubectl apply -f infrastructure/argocd/applications/app-of-apps.yaml

# Verify all child applications created
argocd app list

# Expected output:
# root              Synced  Healthy
# ml-inference-dev  Synced  Healthy
# ml-inference-prod Synced  Healthy
# observability     Synced  Healthy
```

**Success Criteria:**
- ✅ Single command deploys entire infrastructure
- ✅ All applications auto-sync enabled
- ✅ Self-healing operational across all apps

**Dependencies:** Task 1.1
**Risk:** Low
**Estimated Effort:** 4-6 hours

---

### Phase 2: Security Hardening (Week 2-3)
**Goal:** Implement zero-trust security model and policy enforcement

#### 2.1: Network Policies (Zero-Trust Baseline)

**Rationale:** Default-deny networking prevents lateral movement and limits blast radius of compromises

**Tasks:**
- [ ] Create default-deny NetworkPolicy per namespace
- [ ] Define allow-list for ml-inference ingress
- [ ] Allow monitoring stack to scrape metrics
- [ ] Allow DNS resolution (kube-dns)
- [ ] Test connectivity after policies applied
- [ ] Document network topology

**Network Policy Examples:**
```yaml
# infrastructure/base/security/network-policies/deny-all-default.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
  namespace: ml-inference
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# infrastructure/base/security/network-policies/allow-ml-inference.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ml-inference
  namespace: ml-inference
spec:
  podSelector:
    matchLabels:
      app: ml-inference
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53  # DNS
```

**Testing Strategy:**
```bash
# Apply policies
kubectl apply -k infrastructure/base/security/network-policies

# Test allowed traffic
kubectl run test-pod --rm -it --image=curlimages/curl -- \
  curl http://ml-inference.ml-inference.svc.cluster.local/health

# Test denied traffic (should fail)
kubectl run test-pod --rm -it --image=curlimages/curl -- \
  curl http://grafana.monitoring.svc.cluster.local:3000
```

**Success Criteria:**
- ✅ All namespaces have default-deny policies
- ✅ ML inference API remains accessible
- ✅ Monitoring can scrape metrics
- ✅ Unauthorized access blocked (verified via tests)

**Rollback Plan:**
```bash
kubectl delete networkpolicies --all -n ml-inference
kubectl delete networkpolicies --all -n monitoring
```

**Dependencies:** Phase 1.1 (Kustomize structure)
**Risk:** High (can break connectivity)
**Estimated Effort:** 6-8 hours

---

#### 2.2: Policy Enforcement with Kyverno

**Rationale:** Prevent misconfigurations before they reach cluster, enforce organizational standards

**Tasks:**
- [ ] Install Kyverno via Helm
- [ ] Create policy: require resource limits
- [ ] Create policy: require health probes
- [ ] Create policy: block :latest tag
- [ ] Create policy: require labels (owner, env, app)
- [ ] Create policy: require non-root containers
- [ ] Test policies in audit mode
- [ ] Enable enforcement mode
- [ ] Add policy exceptions for system namespaces

**Key Policies:**
```yaml
# infrastructure/base/security/policies/require-resource-limits.yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
  annotations:
    policies.kyverno.io/title: Require Resource Limits
    policies.kyverno.io/severity: medium
    policies.kyverno.io/description: >-
      Containers must define resource requests and limits to prevent
      resource exhaustion and enable proper scheduling.
spec:
  validationFailureAction: enforce
  background: true
  rules:
  - name: validate-resources
    match:
      any:
      - resources:
          kinds:
          - Deployment
          - StatefulSet
          - DaemonSet
    validate:
      message: "CPU and memory resources must be defined"
      pattern:
        spec:
          template:
            spec:
              containers:
              - resources:
                  requests:
                    memory: "?*"
                    cpu: "?*"
                  limits:
                    memory: "?*"
                    cpu: "?*"
```

**Testing:**
```bash
# Test with non-compliant deployment (should fail)
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
      - name: nginx
        image: nginx:latest  # Should fail: latest tag
        # Missing: resource limits, health probes
EOF
# Expected: Admission webhook denied (multiple policy violations)

# Test with compliant deployment (should succeed)
kubectl apply -k infrastructure/overlays/dev
```

**Success Criteria:**
- ✅ All policies active and enforcing
- ✅ Existing deployments remain compliant
- ✅ Non-compliant resources blocked at admission
- ✅ Policy violations visible in audit logs

**Dependencies:** None (parallel with 2.1)
**Risk:** Medium (can block legitimate deployments)
**Estimated Effort:** 8-10 hours

---

#### 2.3: External Secrets Operator

**Rationale:** Never store secrets in Git, pull from secure vault at runtime

**Tasks:**
- [ ] Install External Secrets Operator
- [ ] Configure mock secrets backend (Kubernetes secrets for demo)
- [ ] Document AWS Secrets Manager integration (for production)
- [ ] Migrate Grafana admin password to ExternalSecret
- [ ] Migrate ArgoCD admin password to ExternalSecret
- [ ] Update documentation with secret rotation procedures

**Implementation:**
```yaml
# infrastructure/base/observability/grafana/external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: grafana-admin-credentials
  namespace: monitoring
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: cluster-secret-store
    kind: ClusterSecretStore
  target:
    name: grafana-admin-secret
    creationPolicy: Owner
  data:
  - secretKey: admin-user
    remoteRef:
      key: grafana/admin-user
  - secretKey: admin-password
    remoteRef:
      key: grafana/admin-password
---
# Reference in deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  template:
    spec:
      containers:
      - name: grafana
        env:
        - name: GF_SECURITY_ADMIN_USER
          valueFrom:
            secretKeyRef:
              name: grafana-admin-secret
              key: admin-user
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-admin-secret
              key: admin-password
```

**Success Criteria:**
- ✅ Zero secrets stored in Git
- ✅ Secrets automatically synced from backend
- ✅ Secret rotation works without pod restarts
- ✅ Documentation for production vault setup

**Dependencies:** Phase 1.1
**Risk:** Medium (misconfiguration can break apps)
**Estimated Effort:** 6-8 hours

---

### Phase 3: Complete Observability Stack (Week 3-4)
**Goal:** Achieve full visibility with metrics, logs, and traces

#### 3.1: Logging with Loki

**Rationale:** Centralized logging enables fast debugging, correlates with metrics/traces

**Tasks:**
- [ ] Deploy Loki in microservices mode (distributor, ingester, querier)
- [ ] Deploy Promtail as DaemonSet for log collection
- [ ] Configure Grafana data source for Loki
- [ ] Create log dashboards (error rates, log volume)
- [ ] Add structured logging to ml-inference app
- [ ] Test log queries across pods
- [ ] Configure retention (7 days)

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│                   Loki Stack                         │
│                                                      │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐   │
│  │Distributor│────▶│ Ingester │────▶│ Querier  │   │
│  └──────────┘     └──────────┘     └──────────┘   │
│       ▲                                    │        │
│       │                                    ▼        │
│  ┌──────────┐                        ┌─────────┐  │
│  │ Promtail │                        │ Grafana │  │
│  │(DaemonSet)│                        └─────────┘  │
│  └──────────┘                                       │
│       ▲                                             │
└───────┼─────────────────────────────────────────────┘
        │
   Pod Logs (/var/log/pods/*)
```

**Grafana LogQL Queries:**
```logql
# Error rate for ml-inference
sum(rate({app="ml-inference"} |= "ERROR" [5m])) by (pod)

# Slow requests (>200ms)
{app="ml-inference"}
  | json
  | duration > 200ms
  | line_format "{{.method}} {{.path}} took {{.duration}}"

# Correlate logs with trace
{app="ml-inference"}
  | json
  | trace_id="abc123"
```

**Success Criteria:**
- ✅ All pod logs centralized in Loki
- ✅ Logs retained for 7 days
- ✅ Log search < 3 seconds
- ✅ Integration with traces via trace ID

**Dependencies:** Phase 1.1
**Risk:** Medium (storage requirements)
**Estimated Effort:** 8-10 hours

---

#### 3.2: Distributed Tracing with Tempo

**Rationale:** Trace requests end-to-end, identify latency bottlenecks in microservices

**Tasks:**
- [ ] Deploy Grafana Tempo
- [ ] Instrument ml-inference with OpenTelemetry
- [ ] Configure trace sampling (10% of requests)
- [ ] Add trace context propagation
- [ ] Create Grafana data source for Tempo
- [ ] Build trace dashboard
- [ ] Test trace correlation with logs

**OpenTelemetry Instrumentation:**
```python
# app/ml-inference/app.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Initialize tracer
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Export to Tempo
otlp_exporter = OTLPSpanExporter(endpoint="tempo.monitoring:4317")
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Custom spans
@app.post("/predict")
async def predict(request: InferenceRequest):
    with tracer.start_as_current_span("sentiment_analysis") as span:
        span.set_attribute("text_length", len(request.text))
        result = analyze_sentiment(request.text)
        span.set_attribute("sentiment", result.sentiment)
        return result
```

**Trace Visualization:**
```
Request: POST /predict
├─ [200ms] sentiment_analysis
│  ├─ [50ms]  preprocess_text
│  ├─ [100ms] model_inference
│  │  ├─ [30ms] load_model (cached)
│  │  └─ [70ms] run_inference
│  └─ [50ms]  postprocess_result
└─ [10ms] serialize_response
```

**Success Criteria:**
- ✅ 10% of requests traced
- ✅ Traces visible in Grafana within 10 seconds
- ✅ Trace ID logged for correlation
- ✅ P95 latency identified from traces

**Dependencies:** Task 3.1
**Risk:** Medium (performance overhead)
**Estimated Effort:** 10-12 hours

---

#### 3.3: Service Level Objectives (SLOs)

**Rationale:** Define reliability targets, track error budgets, make data-driven decisions

**Tasks:**
- [ ] Define SLOs for ml-inference service
- [ ] Create Prometheus recording rules for SLIs
- [ ] Build SLO dashboard in Grafana
- [ ] Configure alerting for error budget burn
- [ ] Document incident response procedures

**SLO Definitions:**
```yaml
# config/slos/ml-inference.yaml
service: ml-inference
slos:
  - name: availability
    target: 99.9%                    # "Three nines"
    window: 30d
    sli:
      type: availability
      query: |
        sum(rate(inference_requests_total{status=~"2.."}[5m]))
        /
        sum(rate(inference_requests_total[5m]))
    error_budget: 43m               # 0.1% of 30 days

  - name: latency
    target: 95%                      # 95% of requests < 200ms
    window: 30d
    sli:
      type: latency
      query: |
        histogram_quantile(0.95,
          sum(rate(inference_request_duration_seconds_bucket[5m])) by (le)
        ) < 0.2

  - name: error_rate
    target: 99.9%                    # <0.1% errors
    window: 30d
    sli:
      type: errors
      query: |
        1 - (
          sum(rate(inference_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(inference_requests_total[5m]))
        )
```

**Grafana Dashboard:**
```
┌─────────────────────────────────────────────────────┐
│         ML Inference SLO Dashboard                  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Availability SLO (99.9%)                           │
│  ████████████████████████░  99.95% ✅               │
│  Error Budget Remaining: 42m / 43m (97%)            │
│                                                      │
│  Latency SLO (P95 < 200ms)                          │
│  ████████████████████░░░░  96.2% ✅                 │
│  Current P95: 185ms                                  │
│  Error Budget Remaining: 1.2% / 5%                   │
│                                                      │
│  Error Rate SLO (<0.1%)                             │
│  ██████████████████████░  99.92% ✅                 │
│  Current Error Rate: 0.08%                           │
│  Error Budget Remaining: 15m / 43m (35%)            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Alerting Rules:**
```yaml
# infrastructure/base/observability/victoriametrics/alerts/slo-alerts.yaml
groups:
- name: slo_alerts
  interval: 1m
  rules:
  - alert: ErrorBudgetBurnRateCritical
    expr: |
      (
        1 - (
          sum(rate(inference_requests_total{status=~"2.."}[5m]))
          /
          sum(rate(inference_requests_total[5m]))
        )
      ) > 0.001 * 14.4  # Burning budget 14.4x faster than target
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Error budget burning too fast"
      description: "At current rate, entire error budget will be consumed in < 2 days"
```

**Success Criteria:**
- ✅ SLOs defined for all critical services
- ✅ Error budget visible in dashboard
- ✅ Alerts fire before budget exhaustion
- ✅ Runbook linked from alerts

**Dependencies:** Task 3.1, 3.2
**Risk:** Low
**Estimated Effort:** 6-8 hours

---

### Phase 4: ML Platform Features (Week 4-5)
**Goal:** Enable rapid model iteration and experimentation

#### 4.1: Model Versioning & Registry

**Rationale:** Track model lineage, enable rollbacks, A/B test models

**Tasks:**
- [ ] Deploy MLflow for model registry
- [ ] Version ml-inference models (v1, v2)
- [ ] Add model metadata (accuracy, training date)
- [ ] Implement model version endpoint (`/model/info`)
- [ ] Tag deployments with model version
- [ ] Create model performance dashboard

**Model Registry Structure:**
```yaml
# infrastructure/base/ml-platform/mlflow/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow
  namespace: ml-platform
spec:
  template:
    spec:
      containers:
      - name: mlflow
        image: ghcr.io/mlflow/mlflow:v2.9.2
        env:
        - name: BACKEND_STORE_URI
          value: postgresql://mlflow:5432/mlflow
        - name: ARTIFACT_ROOT
          value: s3://mlflow-artifacts/
        ports:
        - containerPort: 5000
```

**Model Metadata:**
```python
# Register model in MLflow
import mlflow

with mlflow.start_run():
    mlflow.log_param("model_type", "sentiment_analysis")
    mlflow.log_param("algorithm", "rule_based")
    mlflow.log_metric("accuracy", 0.85)
    mlflow.log_metric("f1_score", 0.82)

    # Log model
    mlflow.pyfunc.log_model(
        artifact_path="model",
        python_model=SentimentModel(),
        registered_model_name="sentiment-analyzer",
    )

    # Tag version
    client = mlflow.tracking.MlflowClient()
    client.set_model_version_tag(
        name="sentiment-analyzer",
        version="1",
        key="stage",
        value="production"
    )
```

**Model Info Endpoint:**
```python
@app.get("/model/info")
async def model_info():
    return {
        "model_name": "sentiment-analyzer",
        "version": "v1.2.0",
        "deployed_at": "2025-11-14T10:30:00Z",
        "metrics": {
            "accuracy": 0.85,
            "f1_score": 0.82
        },
        "training_date": "2025-11-10",
        "mlflow_run_id": "abc123"
    }
```

**Success Criteria:**
- ✅ All models versioned in MLflow
- ✅ Model metadata accessible via API
- ✅ Deployment tags indicate model version
- ✅ Rollback to previous model < 5 min

**Dependencies:** Phase 1.1
**Risk:** Low
**Estimated Effort:** 8-10 hours

---

#### 4.2: Progressive Delivery with Argo Rollouts

**Rationale:** Gradual model rollouts reduce blast radius, enable safe experimentation

**Tasks:**
- [ ] Install Argo Rollouts controller
- [ ] Convert Deployment to Rollout
- [ ] Define canary strategy (10% → 50% → 100%)
- [ ] Configure analysis template (error rate threshold)
- [ ] Test automated rollback on error spike
- [ ] Create rollout dashboard

**Canary Rollout:**
```yaml
# infrastructure/base/ml-inference/rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: ml-inference
  namespace: ml-inference
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 10        # 10% traffic to new version
      - pause: {duration: 5m}
      - setWeight: 30
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 5m}
      - setWeight: 80
      - pause: {duration: 5m}

      # Automated analysis
      analysis:
        templates:
        - templateName: error-rate-check
        args:
        - name: service-name
          value: ml-inference

      # Automatic rollback if analysis fails
      abortScaleDownDelaySeconds: 30

  template:
    metadata:
      labels:
        app: ml-inference
        version: v2  # New model version
    spec:
      containers:
      - name: ml-inference
        image: ghcr.io/jonasneves/ml-inference:v2.0.0
        # ... rest of spec
---
# infrastructure/base/ml-inference/analysis-template.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: error-rate-check
spec:
  metrics:
  - name: error-rate
    interval: 1m
    successCondition: result < 0.05  # <5% errors
    failureLimit: 3
    provider:
      prometheus:
        address: http://victoriametrics.monitoring:8428
        query: |
          sum(rate(inference_requests_total{
            app="ml-inference",
            status=~"5.."
          }[5m]))
          /
          sum(rate(inference_requests_total{
            app="ml-inference"
          }[5m]))
```

**Deployment Flow:**
```
Version v1 (stable)
├─ [5 replicas, 100% traffic]
│
└─ Deploy v2
   ├─ Step 1: 10% traffic to v2
   │  ├─ Wait 5 min
   │  ├─ Analyze error rate
   │  └─ ✅ Proceed if < 5% errors
   │
   ├─ Step 2: 30% traffic to v2
   │  ├─ Wait 5 min
   │  └─ ✅ Analyze
   │
   ├─ Step 3: 50% traffic to v2
   │  ├─ Wait 5 min
   │  └─ ❌ Error rate spike!
   │
   └─ 🔄 Automatic Rollback
      └─ Back to 100% v1
```

**Success Criteria:**
- ✅ Canary deployments work automatically
- ✅ Rollback on error rate > 5%
- ✅ Zero downtime during rollouts
- ✅ Rollout visibility in dashboard

**Dependencies:** Phase 3.3 (SLOs for analysis)
**Risk:** Medium (misconfigured rollback could cause outage)
**Estimated Effort:** 10-12 hours

---

#### 4.3: A/B Testing Infrastructure

**Rationale:** Compare model performance with real production traffic

**Tasks:**
- [ ] Deploy two model versions simultaneously
- [ ] Configure traffic splitting (50/50 or 90/10)
- [ ] Add model version to response headers
- [ ] Track metrics per model version
- [ ] Build comparison dashboard
- [ ] Document experiment runbook

**Traffic Splitting:**
```yaml
# Using Argo Rollouts for A/B testing
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: ml-inference
spec:
  strategy:
    canary:
      # Stable A/B test (not progressing to 100%)
      steps:
      - setWeight: 50
      - pause: {}  # Pause indefinitely for A/B test

      # Route by header for deterministic testing
      trafficRouting:
        nginx:
          stableIngress: ml-inference
          annotationPrefix: nginx.ingress.kubernetes.io
          additionalIngressAnnotations:
            canary-by-header: X-Model-Version
            canary-by-header-value: v2
```

**Metrics Per Model:**
```yaml
# Prometheus queries
# Model v1 latency
histogram_quantile(0.95,
  sum(rate(inference_request_duration_seconds_bucket{
    version="v1"
  }[5m])) by (le)
)

# Model v2 latency
histogram_quantile(0.95,
  sum(rate(inference_request_duration_seconds_bucket{
    version="v2"
  }[5m])) by (le)
)

# Comparison
# If v2_latency < v1_latency AND v2_error_rate < v1_error_rate
# → Promote v2 to 100%
```

**Success Criteria:**
- ✅ Run A/B test for 24 hours
- ✅ Metrics separated by model version
- ✅ Statistical significance calculator
- ✅ One-click promotion to winner

**Dependencies:** Task 4.2
**Risk:** Low
**Estimated Effort:** 6-8 hours

---

### Phase 5: Operational Excellence (Week 5-6)
**Goal:** Reduce operational burden and improve incident response

#### 5.1: Runbooks & Documentation

**Tasks:**
- [ ] Create incident response runbook
- [ ] Create scaling runbook
- [ ] Create disaster recovery procedure
- [ ] Create new developer onboarding guide
- [ ] Create architecture diagrams (C4 model)
- [ ] Document monitoring dashboards
- [ ] Create troubleshooting guide

**Runbook Structure:**
```
docs/
├── runbooks/
│   ├── incident-response.md
│   │   ├── Severity Classification
│   │   ├── Escalation Paths
│   │   ├── Communication Templates
│   │   └── Post-Incident Review Process
│   │
│   ├── scaling-guide.md
│   │   ├── When to Scale
│   │   ├── Horizontal Scaling Procedure
│   │   ├── Vertical Scaling Procedure
│   │   └── Rollback Steps
│   │
│   ├── disaster-recovery.md
│   │   ├── Backup Procedures
│   │   ├── Restore Procedures
│   │   ├── RTO/RPO Targets
│   │   └── Testing Schedule
│   │
│   └── troubleshooting/
│       ├── high-latency.md
│       ├── high-error-rate.md
│       ├── pod-crashloop.md
│       └── argocd-sync-failure.md
│
├── developer-guides/
│   ├── onboarding.md             # 10-min setup guide
│   ├── local-development.md
│   ├── adding-new-service.md
│   └── contributing.md
│
└── architecture/
    ├── c4-context-diagram.png
    ├── c4-container-diagram.png
    ├── c4-component-diagram.png
    └── data-flow-diagram.png
```

**Incident Response Example:**
```markdown
# Runbook: High Error Rate

**Severity:** P1 (Critical)
**Owner:** ML Platform Team
**Last Updated:** 2025-11-14

## Symptoms
- Error rate > 5% for 5 minutes
- Alert: `ErrorBudgetBurnRateCritical` firing

## Investigation Steps

1. **Check current error rate**
   ```bash
   # Query VictoriaMetrics
   curl -s 'http://victoriametrics.monitoring:8428/api/v1/query' \
     --data-urlencode 'query=sum(rate(inference_requests_total{status=~"5.."}[5m]))' \
     | jq -r '.data.result[0].value[1]'
   ```

2. **Identify error types**
   ```bash
   # Check logs in Loki
   logcli query '{app="ml-inference"} |= "ERROR"' --limit=50
   ```

3. **Check recent deployments**
   ```bash
   kubectl rollout history deployment/ml-inference -n ml-inference
   ```

## Mitigation

### If recent deployment:
```bash
# Rollback to previous version
kubectl rollout undo deployment/ml-inference -n ml-inference
kubectl rollout status deployment/ml-inference -n ml-inference
```

### If infrastructure issue:
```bash
# Scale up replicas
kubectl scale deployment/ml-inference --replicas=10 -n ml-inference
```

### If third-party dependency:
- Check upstream service status
- Enable circuit breaker
- Serve cached responses

## Recovery Verification
- [ ] Error rate < 1%
- [ ] P95 latency < 200ms
- [ ] All pods healthy

## Post-Incident
- [ ] Create incident report
- [ ] Update runbook with learnings
- [ ] Schedule post-mortem meeting
```

**Success Criteria:**
- ✅ Runbook for every common incident
- ✅ All runbooks tested at least once
- ✅ Linked from alerting rules
- ✅ New developer productive in < 10 min

**Dependencies:** All previous phases
**Risk:** Low
**Estimated Effort:** 12-16 hours

---

#### 5.2: Automated Remediation

**Tasks:**
- [ ] Create PodDisruptionBudget for availability during drains
- [ ] Configure HPA with custom metrics (queue length)
- [ ] Create VerticalPodAutoscaler for right-sizing
- [ ] Implement health check auto-restart
- [ ] Add circuit breaker for upstream dependencies
- [ ] Test failure scenarios

**PodDisruptionBudget:**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: ml-inference-pdb
  namespace: ml-inference
spec:
  minAvailable: 2  # Always keep at least 2 pods running
  selector:
    matchLabels:
      app: ml-inference
```

**VerticalPodAutoscaler:**
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: ml-inference-vpa
  namespace: ml-inference
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-inference
  updatePolicy:
    updateMode: Auto  # Automatically apply recommendations
  resourcePolicy:
    containerPolicies:
    - containerName: ml-inference
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2000m
        memory: 1Gi
```

**Success Criteria:**
- ✅ No downtime during node drains
- ✅ Resources automatically optimized
- ✅ Pod restarts on failed health checks < 30s
- ✅ 90% of common issues self-heal

**Dependencies:** Phase 3.3
**Risk:** Medium (aggressive auto-scaling can cause instability)
**Estimated Effort:** 8-10 hours

---

### Phase 6: Advanced Features (Week 6-8, Optional)
**Goal:** Cutting-edge capabilities for large-scale production

#### 6.1: Service Mesh (Istio)

**Rationale:** Advanced traffic management, automatic mTLS, deep observability

**Decision Point:** Evaluate if complexity is justified
- **Deploy if:** Multiple services, need mTLS, advanced routing
- **Skip if:** Single service, network policies sufficient

**Tasks (if deploying):**
- [ ] Install Istio control plane
- [ ] Enable sidecar injection for ml-inference
- [ ] Configure mTLS (STRICT mode)
- [ ] Migrate NetworkPolicies to AuthorizationPolicies
- [ ] Configure retry policies
- [ ] Configure circuit breakers
- [ ] Test fault injection

**Dependencies:** Phase 2.1 (Network Policies)
**Risk:** High (adds significant complexity)
**Estimated Effort:** 20-24 hours

---

#### 6.2: Chaos Engineering

**Tasks:**
- [ ] Install Chaos Mesh
- [ ] Define chaos experiments
  - Pod kill (random pod termination)
  - Network delay (200ms latency)
  - Network partition (isolate pod)
  - CPU stress (consume 80% CPU)
- [ ] Run experiments in staging
- [ ] Verify system recovers automatically
- [ ] Document findings

**Example Chaos Experiment:**
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-failure-test
  namespace: ml-inference
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
    - ml-inference
    labelSelectors:
      app: ml-inference
  scheduler:
    cron: "0 */6 * * *"  # Every 6 hours
```

**Dependencies:** Phase 5.2 (Automated remediation)
**Risk:** Medium (can cause actual incidents if misconfigured)
**Estimated Effort:** 12-16 hours

---

## 🎯 Success Metrics Dashboard

```
┌─────────────────────────────────────────────────────┐
│       Cluster Modernization Progress                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ✅ Phase 0: Foundation              [100%] ████████│
│  ✅ Phase 1: Structure                [100%] ████████│
│  🔄 Phase 2: Security                  [60%] █████░░░│
│  ⏳ Phase 3: Observability             [30%] ███░░░░░│
│  ⏳ Phase 4: ML Platform                [0%] ░░░░░░░░│
│  ⏳ Phase 5: Operations                 [0%] ░░░░░░░░│
│  ⏳ Phase 6: Advanced (Optional)        [0%] ░░░░░░░░│
│                                                      │
│  Overall Progress: 41% ████████████░░░░░░░░░░░░      │
│                                                      │
├─────────────────────────────────────────────────────┤
│  Key Metrics                                         │
├─────────────────────────────────────────────────────┤
│  • Deployment Time:           15m → Target: <10m    │
│  • Uptime SLO:              99.5% → Target: 99.9%   │
│  • MTTD (Mean Time Detect):  12m → Target: <5m      │
│  • MTTR (Mean Time Recover): 25m → Target: <15m     │
│  • Policy Compliance:         60% → Target: 100%    │
│  • Security Score:          B (75) → Target: A (95) │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## ⚠️ Risk Register

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|-----------|--------|------------|-------|
| **Network policy breaks connectivity** | High | High | Test in dev first, maintain rollback scripts | Platform Team |
| **Kustomize migration causes downtime** | Medium | High | Blue/green migration, extensive testing | Platform Team |
| **Policy enforcement blocks legitimate deploys** | Medium | Medium | Audit mode first, exception process | Security Team |
| **Observability stack increases costs** | Low | Medium | Set retention limits, sample traces | Platform Team |
| **Service mesh adds too much complexity** | High | Medium | Evaluate thoroughly, optional deployment | Architecture Team |
| **Team lacks Kubernetes expertise** | Medium | High | Training sessions, pair programming | Engineering Manager |

---

## 🧪 Testing Strategy

### Per-Phase Testing

**Phase 1: Structure**
```bash
# Validate Kustomize builds
kustomize build infrastructure/overlays/dev > /dev/null
kustomize build infrastructure/overlays/staging > /dev/null
kustomize build infrastructure/overlays/prod > /dev/null

# Test app-of-apps
kubectl apply --dry-run=server -f infrastructure/argocd/applications/app-of-apps.yaml
```

**Phase 2: Security**
```bash
# Test network policies
./scripts/test-network-policies.sh

# Test Kyverno policies
kubectl apply --dry-run=server -f tests/fixtures/non-compliant-deployment.yaml
# Expected: admission webhook denied
```

**Phase 3: Observability**
```bash
# Verify logs in Loki
logcli query '{app="ml-inference"}' --limit=10

# Verify traces in Tempo
curl http://tempo.monitoring:3100/api/traces/<trace-id>

# Validate SLO calculations
curl -s http://victoriametrics:8428/api/v1/query \
  --data-urlencode 'query=...' | jq
```

**Phase 4: ML Platform**
```bash
# Test canary rollout
kubectl argo rollouts promote ml-inference -n ml-inference
kubectl argo rollouts abort ml-inference -n ml-inference

# Verify model versioning
curl http://ml-inference/model/info | jq
```

### End-to-End Tests
```bash
# Full cluster bootstrap test
./scripts/test-cluster-bootstrap.sh

# Disaster recovery test
./scripts/test-disaster-recovery.sh

# Chaos engineering validation
./scripts/run-chaos-experiments.sh
```

---

## 🔄 Rollback Procedures

### Phase-Specific Rollbacks

**Phase 1: Kustomize Migration**
```bash
# Revert ArgoCD applications
kubectl apply -f argocd/applications-backup/

# Revert to old k8s/ directory
git revert <kustomize-migration-commit>
git push origin main
```

**Phase 2: Security**
```bash
# Remove all network policies
kubectl delete networkpolicies --all -n ml-inference
kubectl delete networkpolicies --all -n monitoring

# Disable Kyverno enforcement
kubectl patch clusterpolicy <policy-name> \
  --type=merge -p '{"spec":{"validationFailureAction":"audit"}}'
```

**Phase 3: Observability**
```bash
# Scale down Loki
kubectl scale deployment -n monitoring --replicas=0 --all

# Remove Tempo
kubectl delete namespace tempo

# Revert instrumentation
git revert <otel-instrumentation-commit>
```

**Phase 4: ML Platform**
```bash
# Rollback to Deployment (from Rollout)
kubectl delete rollout ml-inference -n ml-inference
kubectl apply -f k8s/inference-service/deployment-backup.yaml
```

---

## 📊 Success Criteria & Acceptance Tests

### Phase Completion Checklist

Each phase is considered complete when:

- [ ] All tasks marked as done
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Team review completed
- [ ] Rollback procedure tested
- [ ] Monitoring in place
- [ ] Success metrics met

### Final Acceptance Criteria

Before considering the modernization complete:

#### Functional Requirements
- [ ] 3 environments operational (dev/staging/prod)
- [ ] All services deployed via GitOps
- [ ] Zero secrets in Git
- [ ] All policies enforcing
- [ ] Full observability (metrics + logs + traces)
- [ ] Model versioning functional
- [ ] Canary deployments working

#### Non-Functional Requirements
- [ ] 99.9% uptime SLO met for 30 days
- [ ] P95 latency < 200ms
- [ ] Error rate < 0.1%
- [ ] Deployment time < 15 minutes
- [ ] MTTD < 5 minutes
- [ ] MTTR < 15 minutes

#### Operational Requirements
- [ ] All runbooks tested
- [ ] Team trained on new tools
- [ ] On-call rotation established
- [ ] Incident response tested
- [ ] Disaster recovery tested

#### Security Requirements
- [ ] Network policies enforced
- [ ] Pod security policies enforced
- [ ] No latest tags in production
- [ ] All containers non-root
- [ ] Security audit passed

---

## 🎓 Learning Resources

### For the Team

**Kustomize**
- https://kustomize.io/
- https://kubectl.docs.kubernetes.io/guides/introduction/kustomize/

**Kyverno**
- https://kyverno.io/docs/
- https://kyverno.io/policies/

**Grafana Loki**
- https://grafana.com/docs/loki/latest/
- LogQL query language

**OpenTelemetry**
- https://opentelemetry.io/docs/
- Python instrumentation guide

**Argo Rollouts**
- https://argoproj.github.io/argo-rollouts/
- Progressive delivery patterns

**SRE Practices**
- Google SRE Book (https://sre.google/books/)
- Site Reliability Workbook

---

## 📝 Appendix

### A. Technology Comparison

| Category | Current | Evaluated | Chosen | Rationale (ADR) |
|----------|---------|-----------|--------|-----------------|
| Config Mgmt | Plain YAML | Helm, Kustomize, Jsonnet | **Kustomize** | ADR-001 |
| Secrets | In-cluster | Sealed Secrets, ESO, Vault | **ESO** | ADR-004 |
| Logging | None | Loki, ELK, Splunk | **Loki** | Cost, integration |
| Tracing | None | Jaeger, Tempo, Zipkin | **Tempo** | Grafana ecosystem |
| Policy | Manual | OPA, Kyverno | **Kyverno** | Kubernetes-native |
| Service Mesh | None | Istio, Linkerd, Cilium | **TBD** | ADR-005 |

### B. Cost Estimate

**Current Monthly Cost:** $0 (GitHub Actions free tier)

**Post-Modernization (on managed Kubernetes):**
- Compute (3 environments): ~$300/mo
- Storage (logs/metrics): ~$50/mo
- Networking: ~$20/mo
- **Total: ~$370/mo**

**Mitigations:**
- Continue using Minikube for demo
- Use spot instances for dev/staging
- Adjust retention periods

### C. Timeline Gantt Chart

```
Week 1  |████████| Phase 0 + Phase 1
Week 2  |████████| Phase 1 + Phase 2
Week 3  |████████| Phase 2 + Phase 3
Week 4  |████████| Phase 3 + Phase 4
Week 5  |████████| Phase 4 + Phase 5
Week 6  |████████| Phase 5
Week 7-8|████░░░░| Phase 6 (Optional)
```

### D. Team Roles

| Role | Responsibilities | Time Commitment |
|------|-----------------|-----------------|
| **Platform Engineer** | Infrastructure implementation | 100% for 6 weeks |
| **Security Engineer** | Policy definition, audit | 25% for 6 weeks |
| **ML Engineer** | Model versioning, testing | 25% for weeks 4-5 |
| **SRE** | SLO definition, runbooks | 25% for weeks 5-6 |
| **Tech Lead** | Architecture decisions, reviews | 10% for 6 weeks |

---

## ✅ Next Steps

1. **Review this plan** with team and stakeholders
2. **Create ADRs** for key decisions (Phase 0)
3. **Set up project tracking** (GitHub Projects, Jira)
4. **Schedule kickoff** meeting
5. **Begin Phase 1** (Kustomize migration)

---

## 📚 Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-14 | Claude | Initial comprehensive plan |

---

**Questions? Feedback?**
- Open an issue: https://github.com/jonasneves/gitops-ml-infra-demo/issues
- Team chat: #ml-platform-modernization
- Tech Lead: @tech-lead

---

*This plan is a living document. As we learn during implementation, we'll update it to reflect reality.*
