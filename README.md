# URL Shortener Platform

A production-ready URL shortening service built with FastAPI and PostgreSQL, deployed on Kubernetes with a full CI/CD pipeline using Jenkins and ArgoCD GitOps.

## Features

- Shorten long URLs into 5-character codes via a web UI
- HTTP 307 redirects from short codes to original URLs
- URL validation (http/https only)
- Liveness and readiness health check endpoints
- Prometheus metrics with custom counters and histograms
- Grafana dashboard for real-time observability
- Auto-scaling (HPA), pod disruption budgets, and graceful shutdown

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI 0.115.0 |
| Server | Uvicorn 0.30.6 |
| Database | PostgreSQL 15 + SQLAlchemy 2.0.30 |
| Templating | Jinja2 3.1.4 |
| Monitoring | Prometheus Client 0.20.0 + Grafana |
| Container Build | Docker + Kaniko (in-cluster) |
| CI | Jenkins (Kubernetes pod agents) |
| CD | ArgoCD (GitOps) |
| Orchestration | Kubernetes |

## Project Structure

```
.
├── app/
│   ├── main.py           # FastAPI routes, middleware, Prometheus metrics
│   ├── database.py       # SQLAlchemy engine with connection pooling
│   ├── models.py         # URL model (id, code, original_url)
│   └── templates/
│       └── index.html    # Web UI (dark glassmorphism design)
├── tests/
│   ├── conftest.py       # SQLite test database fixture
│   └── test_health.py    # 7 tests covering all core endpoints
├── k8s/
│   ├── app-deployment.yaml               # App deployment (image tag managed by CI)
│   ├── app-service.yaml                  # ClusterIP service on port 8000
│   ├── app-hpa.yaml                      # HPA: 2–7 replicas, 50% CPU target
│   ├── app-ingress.yaml                  # NGINX ingress
│   ├── app-pdb.yaml                      # PodDisruptionBudget: minAvailable 1
│   ├── configmap.yaml                    # APP_ENV=production
│   ├── postgres-deployment.yaml          # PostgreSQL with Recreate strategy
│   ├── postgres-service.yaml             # Postgres ClusterIP service
│   ├── postgres-pvc.yaml                 # 1Gi PVC for postgres data
│   ├── url-shortener-servicemonitor.yaml # Prometheus scrape config
│   ├── argocd-app.yaml                   # ArgoCD Application definition
│   ├── grafana-dashboard.json            # Grafana dashboard as code
│   └── admin/
│       └── jenkins-rbac.yaml             # ClusterRole for Jenkins SA (apply once)
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── requirements.txt
└── requirements-dev.txt
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Web UI home page |
| POST | `/shorten-ui` | Shorten a URL (form submission) |
| GET | `/{code}` | Redirect to original URL (HTTP 307) |
| GET | `/live` | Liveness probe → `{"status": "alive"}` |
| GET | `/ready` | Readiness probe (checks DB connection) |
| GET | `/metrics` | Prometheus metrics |

## Local Development

### With Docker Compose (recommended)

```bash
docker-compose up --build
```

App available at `http://localhost:8000`

### Manual Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

export DATABASE_URL=postgresql://user:password@localhost:5432/urlshortener

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Individual env vars are also supported: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DB_HOST` (default: `postgres`), `DB_PORT` (default: `5432`).

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests use SQLite (`DATABASE_URL=sqlite:///./test.db` set in `conftest.py`) — no Postgres needed. Covers: liveness, readiness, home page, URL shortening, redirect (307), 404, and metrics endpoints.

## CI/CD Pipeline

The project uses a split CI/CD model — Jenkins handles CI, ArgoCD handles CD.

### CI — Jenkins (4 stages)

1. **Checkout** — pulls code from GitHub; skips the build if the commit message contains `[skip ci]`
2. **Quality Checks** — runs `flake8 app` and `pytest -v` in a `python:3.11` container
3. **Build & Push Image** — builds with Kaniko (no Docker daemon needed), pushes `:{BUILD_NUMBER}` and `:latest` to Docker Hub
4. **Update Manifest** — updates `k8s/app-deployment.yaml` with the new image tag, commits `[skip ci]` back to git, and pushes to GitHub

Jenkins uses Kubernetes pod agents — each build spins up a pod with `python:3.11` and `gcr.io/kaniko-project/executor` containers sharing a workspace volume.

### CD — ArgoCD

ArgoCD watches the `k8s/` path on the `main` branch. When Jenkins commits the updated image tag, ArgoCD detects the change and performs a rolling update automatically.

- **Auto-sync:** enabled with `prune: true` and `selfHeal: true`
- **Rollback:** revert the manifest commit in git — ArgoCD syncs the revert automatically

### Jenkins Prerequisites

- Kubernetes secret `kaniko-docker-config` with Docker Hub credentials
- Jenkins credential `github-creds` (username + GitHub personal access token with `repo` scope)
- Jenkins RBAC applied once by a cluster admin:

```bash
kubectl apply -f k8s/admin/jenkins-rbac.yaml
```

### ArgoCD Prerequisites

- ArgoCD installed in the `argocd` namespace
- Git credentials secret for manifest write-back:

```bash
kubectl create secret generic git-creds \
  --from-literal=username=<github-username> \
  --from-literal=password=<github-token> \
  -n argocd
```

- ArgoCD Application applied:

```bash
kubectl apply -f k8s/argocd-app.yaml
```

## Kubernetes Deployment

All manifests target the `default` namespace except the ServiceMonitor (`monitoring` namespace).

```bash
# Apply RBAC first (once, as cluster admin)
kubectl apply -f k8s/admin/jenkins-rbac.yaml

# Create the database secret (not tracked in git)
kubectl apply -f k8s/secret.yaml
kubectl annotate secret db-secret argocd.argoproj.io/sync-options=Prune=false -n default

# Deploy everything
kubectl apply -f k8s/
```

### Kubernetes Resources

| Resource | Details |
|---|---|
| Deployment | Image tag updated by Jenkins on every build, `imagePullPolicy: Always` |
| HPA | 2–7 replicas, scales at 50% CPU, aggressive scale-up, conservative scale-down (300s) |
| PDB | `minAvailable: 1` — ensures zero-downtime during rolling updates |
| Ingress | NGINX — replace `url-shortener.example.com` with your actual domain |
| PostgreSQL | Single pod, `Recreate` strategy (required for ReadWriteOnce PVC), 1Gi storage |
| ServiceMonitor | Scrapes `/metrics` every 10s via Prometheus Operator |

## Monitoring

The app exposes Prometheus metrics at `/metrics`:

| Metric | Type | Description |
|---|---|---|
| `url_shortened_total` | Counter | Total URLs shortened |
| `url_redirect_total` | Counter | Total redirects served |
| `http_requests_total` | Counter | Requests by method / path / status |
| `http_request_duration_seconds` | Histogram | Request latency |

A Grafana dashboard is included at `k8s/grafana-dashboard.json` covering URL activity, P95 latency, success rate, error rate, and pod count.

To import: Grafana → Dashboards → Import → upload `grafana-dashboard.json`.

## Secrets Management

`k8s/secret.yaml` is gitignored — credentials are never committed to the repository. The `db-secret` in the cluster is annotated with `argocd.argoproj.io/sync-options=Prune=false` so ArgoCD never deletes it during sync.

If the secret is ever lost, reapply manually:

```bash
kubectl apply -f k8s/secret.yaml
kubectl annotate secret db-secret argocd.argoproj.io/sync-options=Prune=false -n default
```
