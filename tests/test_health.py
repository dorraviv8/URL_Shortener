from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_live():
    response = client.get("/live")
    assert response.status_code == 200

def test_ready():
    response = client.get("/ready")
    assert response.status_code == 200
