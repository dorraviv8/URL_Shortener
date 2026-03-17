from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse, Response
from fastapi.templating import Jinja2Templates
import time
import secrets
from pathlib import Path
from urllib.parse import urlparse
from sqlalchemy import text
from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
)

from app.database import engine, SessionLocal
from app.models import Base, URL


# -------------------------
# App init
# -------------------------
app = FastAPI(title="URL Shortener", version="0.2.0")

# Create tables only if DB engine exists
if engine:
    Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# -------------------------
# Prometheus custom metrics
# -------------------------
URL_SHORTENED_TOTAL = Counter(
    "url_shortened_total",
    "Total number of URLs shortened"
)

URL_REDIRECT_TOTAL = Counter(
    "url_redirect_total",
    "Total number of redirects served"
)

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"]
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"]
)


# -------------------------
# HTTP Metrics Middleware
# -------------------------
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    http_requests_total.labels(
        method=request.method,
        path=request.url.path,
        status=response.status_code
    ).inc()

    http_request_duration_seconds.labels(
        method=request.method,
        path=request.url.path
    ).observe(duration)

    return response


# -------------------------
# 1️⃣ Home Page (UI)
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


def _validate_url(url: str) -> str | None:
    """Return an error message if the URL is invalid, else None."""
    try:
        parsed = urlparse(url)
    except Exception:
        return "Invalid URL format."
    if parsed.scheme not in ("http", "https"):
        return "Only http:// and https:// URLs are accepted."
    if not parsed.netloc:
        return "URL must include a valid hostname."
    return None


# -------------------------
# 2️⃣ Shorten via UI Form
# -------------------------
@app.post("/shorten-ui", response_class=HTMLResponse)
def shorten_ui(request: Request, url: str = Form(...)):

    error = _validate_url(url)
    if error:
        return templates.TemplateResponse(
            request,
            "index.html",
            {"error": error},
            status_code=400,
        )

    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")

    db = SessionLocal()

    try:
        code = secrets.token_urlsafe(5)

        while db.query(URL).filter(URL.code == code).first():
            code = secrets.token_urlsafe(5)

        db.add(URL(code=code, original_url=url))
        db.commit()

        URL_SHORTENED_TOTAL.inc()

        base_url = str(request.base_url).rstrip("/")
        short_url = f"{base_url}/{code}"

        return templates.TemplateResponse(
            request,
            "index.html",
            {"short_url": short_url}
        )

    finally:
        db.close()


# -------------------------
# 3️⃣ Health Checks
# -------------------------
@app.get("/ready")
def readiness():

    # אם אין DB (כמו ב-CI)
    if SessionLocal is None:
        return {"status": "ok"}

    db = SessionLocal()

    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}

    except Exception:
        raise HTTPException(status_code=500, detail="Database not available")

    finally:
        db.close()


@app.get("/live")
def liveness():
    return {"status": "alive"}


# -------------------------
# 4️⃣ Metrics Endpoint
# -------------------------
@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# -------------------------
# 5️⃣ Redirect Route (must be last)
# -------------------------
@app.get("/{code}")
def redirect(code: str):

    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database not configured")

    db = SessionLocal()

    try:
        url_entry = db.query(URL).filter(URL.code == code).first()

        if not url_entry:
            raise HTTPException(status_code=404, detail="Code not found")

        URL_REDIRECT_TOTAL.inc()

        return RedirectResponse(
            url=url_entry.original_url,
            status_code=307
        )

    finally:
        db.close()
