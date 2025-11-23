# Modular Infrastructure Architecture

Treating GitHub Actions runners as distributed compute units for scalable infrastructure.

## Concept

| Traditional | Modular Approach |
|-------------|------------------|
| Kubernetes pods | GitHub Actions jobs/runners |
| Manifests | Workflow files |
| Service mesh | Cloudflare Tunnel |
| Orchestrator | GitHub Actions |

Each workflow file defines an independent component that can be:
- Scaled horizontally (multiple runners)
- Deployed independently
- Failed in isolation
- Updated without affecting others

## Current Implementation

Two-component split in `live-server.yml`:

```
┌─────────────────┐     ┌─────────────────┐
│   Host Runner   │     │Monitoring Runner│
├─────────────────┤     ├─────────────────┤
│ Minikube        │     │ VictoriaMetrics │
│ ArgoCD          │     │ Grafana         │
│ ML API          │     │                 │
│ Dashboard       │     │                 │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───── Cloudflare ──────┘
```

## Future: Full Modular Split

```
.github/workflows/
├── live-cluster.yml      # Minikube + ArgoCD
├── live-dashboard.yml    # Dashboard server
└── live-monitoring.yml   # VictoriaMetrics + Grafana
```

Benefits:
- Independent scaling per component
- Selective restarts
- Clear ownership
- Better resource isolation

## Challenges to Solve

### 1. Service Discovery

**Problem:** Runners are isolated. Components need to find each other.

**Current workaround:** Pass URLs via workflow inputs (`ml_api_url`).

**Potential solutions:**
- Shared configuration file in repo
- GitHub Actions cache as registry
- External service registry (Redis, Consul)
- Cloudflare Workers KV for coordination

### 2. Single Tunnel Routing

**Problem:** Multiple runners can't share one tunnel token effectively (Cloudflare load-balances between them).

**Current workaround:** Separate tunnel per runner.

**Potential solutions:**
- Named tunnels with config files (each runner specifies its routes)
- Cloudflare Access service tokens for routing
- Single tunnel runner that proxies to others
- Use tunnel connector ID to distinguish runners

### 3. Inter-Runner Communication

**Problem:** Runners have no direct network path to each other.

**Current workaround:** Communicate via public URLs through Cloudflare.

**Potential solutions:**
- Tailscale/WireGuard mesh between runners
- GitHub Actions artifacts for async data sharing
- External message queue (Redis pub/sub)
- Webhook-based coordination

### 4. Dependency Coordination

**Problem:** Some components must start before others (cluster before dashboard).

**Potential solutions:**
- `workflow_run` triggers for sequencing
- Health check polling before dependent starts
- Coordinator job that orchestrates startup
- GitHub Actions outputs passed between jobs

### 5. State Management

**Problem:** No shared filesystem between runners.

**Potential solutions:**
- GitHub Actions cache for shared state
- External object storage (S3, R2)
- Database for coordination state
- Git repo as state store

### 6. Unified Logging

**Problem:** Logs scattered across multiple workflow runs.

**Potential solutions:**
- Central log aggregation (Loki, CloudWatch)
- GitHub Actions log forwarding
- Shared Grafana with multiple datasources

## Component Constraints

Not all components can be separated:

| Component | Separable? | Reason |
|-----------|------------|--------|
| Minikube | No | Core cluster, others depend on it |
| ArgoCD | No | Must run inside cluster |
| ML API | No | Deployed into cluster by ArgoCD |
| Dashboard | No | Needs kubectl access to cluster |
| VictoriaMetrics | Yes | Standalone, scrapes via HTTP |
| Grafana | Yes | Standalone, queries via HTTP |

## Scaling Patterns

### Horizontal Scaling (Multiple Instances)

```yaml
strategy:
  matrix:
    instance: [1, 2, 3]
```

Good for: Stateless API servers, load testing

### Vertical Scaling (Bigger Runner)

```yaml
runs-on: ubuntu-latest-16-cores
```

Good for: Build jobs, resource-intensive workloads

### Geographic Distribution

```yaml
strategy:
  matrix:
    region: [us-east, eu-west, ap-south]
```

Good for: Multi-region demos, latency testing

## Implementation Priorities

1. **Solve single tunnel routing** - Most impactful, enables true modularity
2. **Service discovery mechanism** - Required for components to communicate
3. **Dependency coordination** - Ensures reliable startup order
4. **Split into component workflows** - Final implementation

## Cost Considerations

- Each parallel job consumes runner minutes independently
- 2 runners for 5.5 hours = 11 runner-hours per session
- Consider consolidating for cost vs splitting for modularity
- GitHub Free: 2,000 minutes/month
- GitHub Pro: 3,000 minutes/month

## References

- [GitHub Actions: Using jobs in a workflow](https://docs.github.com/en/actions/using-jobs)
- [Cloudflare Tunnel: Run as a service](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/run-tunnel/as-a-service/)
- [GitHub Actions: Caching dependencies](https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows)
