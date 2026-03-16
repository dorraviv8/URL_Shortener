import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import URL

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    yield
    if SessionLocal:
        db = SessionLocal()
        try:
            db.query(URL).delete()
            db.commit()
        finally:
            db.close()


def test_live():
    response = client.get("/live")
    assert response.status_code == 200


def test_ready():
    response = client.get("/ready")
    assert response.status_code == 200


def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_shorten_url_returns_short_url():
    response = client.post("/shorten-ui", data={"url": "https://example.com"})
    assert response.status_code == 200
    assert "https://example.com" in response.text or "http://" in response.text


def test_redirect_to_original_url():
    db = SessionLocal()
    try:
        db.add(URL(code="testcode", original_url="https://example.com/target"))
        db.commit()
    finally:
        db.close()

    response = client.get("/testcode", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/target"


def test_redirect_not_found():
    response = client.get("/nonexistent-xyz", follow_redirects=False)
    assert response.status_code == 404


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
