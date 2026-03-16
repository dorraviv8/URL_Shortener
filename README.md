# URL Shortener Platform

A production-ready URL shortening service built with FastAPI, PostgreSQL, and deployed on Kubernetes with a full CI/CD pipeline via Jenkins.

## Features

- Shorten long URLs into 5-character codes via a web UI
- HTTP 307 redirects from short codes to original URLs
- Liveness and readiness health check endpoints
- Prometheus metrics (request counts, durations, URL shortening counters)
- Auto-scaling, pod disruption budgets, and graceful shutdown

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI 0.115.0 |
| Server | Uvicorn 0.30.6 |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy 2.0.30 |
| Templating | Jinja2 3.1.4 |
| Monitoring | Prometheus Client 0.20.0 |
| Container Build | Kaniko |
| CI/CD | Jenkins (Kubernetes agents) |
| Orchestration | Kubernetes |

## Project Structure

```
.
├── app/
│   ├── main.py          # FastAPI routes, middleware, Prometheus metrics
│   ├── database.py      # SQLAlchemy engine with connection pooling
│   ├── models.py        # URL model (id, code, original_url)
│   └── templates/
│       └── index.html   # Web UI
├── tests/
│   ├── conftest.py      # SQLite test database fixture
│   └── test_health.py   # 7 tests covering all core endpoints
├── k8s/
│   ├── app-deployment.yaml
│   ├── app-service.yaml
│   ├── app-hpa.yaml
│   ├── app-ingress.yaml
│   ├── app-pdb.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── postgres-deployment.yaml
│   ├── postgres-service.yaml
│   ├── postgres-pvc.yaml
│   ├── url-shortener-servicemonitor.yaml
│   └── admin/
│       └── jenkins-rbac.yaml   # Apply once by cluster admin
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── requirements.txt
└── requirements-dev.txt
```

## Local Development

### With Docker Compose (recommended)

```bash
docker-compose up --build
```

App available at http://localhost:8000

### Manual Setup

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

export POSTGRES_USER=user
export POSTGRES_PASSWORD=password
export POSTGRES_DB=urlshortener
export DB_HOST=localhost
export DB_PORT=5432

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

Tests use SQLite and cover: liveness, readiness, home page, URL shortening, redirect, 404, and metrics endpoints.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Web UI home page |
| POST | `/shorten-ui` | Shorten a URL (form submission) |
| GET | `/{code}` | Redirect to original URL |
| GET | `/live` | Liveness probe |
| GET | `/ready` | Readiness probe |
| GET | `/metrics` | Prometheus metrics |

## CI/CD Pipeline

The Jenkinsfile defines a 4-stage pipeline using Kubernetes pod agents:

1. **Checkout** — pulls code from GitHub
2. **Quality Checks** — runs `flake8` and `pytest`
3. **Build & Push Image** — builds with Kaniko, pushes to Docker Hub as `dorraviv/url-shortener-platform:{BUILD_NUMBER}` and `:latest`
4. **Deploy to Kubernetes** — applies all manifests in `k8s/`, updates the deployment image, waits for rollout

### Jenkins Prerequisites

- Kubernetes secret `kaniko-docker-config` with Docker Hub credentials
- Jenkins service account RBAC applied once by a cluster admin:

```bash
kubectl apply -f k8s/admin/jenkins-rbac.yaml
```

## Kubernetes Deployment

All manifests target the `default` namespace (except the ServiceMonitor which goes to `monitoring`).

```bash
# Apply RBAC first (once, as cluster admin)
kubectl apply -f k8s/admin/jenkins-rbac.yaml

# Deploy everything
kubectl apply -f k8s/
```

### Resource Overview

| Resource | Details |
|---|---|
| Deployment | 1 replica, 100m–500m CPU, 128Mi–256Mi memory |
| HPA | 2–7 replicas, scales at 50% CPU |
| PDB | minAvailable: 1 |
| Ingress | NGINX, routes `/` to app |
| PostgreSQL | Single pod with 1Gi PVC |
| ServiceMonitor | Scrapes `/metrics` every 10s via Prometheus Operator |

## Monitoring

The app exposes Prometheus metrics at `/metrics`:

- `url_shortener_urls_created_total` — total URLs shortened
- `url_shortener_redirects_total` — total redirects served
- `http_requests_total` — request count by method/path/status
- `http_request_duration_seconds` — request latency histogram

The `url-shortener-servicemonitor.yaml` configures Prometheus Operator to scrape these automatically.
