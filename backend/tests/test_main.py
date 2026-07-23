import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_signup_missing_fields():
    response = client.post("/auth/signup", json={})
    assert response.status_code == 422

def test_login_wrong_credentials():
    response = client.post("/auth/login", json={
        "email": "fake@fake.com",
        "password": "wrongpassword"
    })
    assert response.status_code in [401, 400]

def test_debate_requires_auth():
    response = client.get("/reports/history")
    assert response.status_code in [401, 403]

def test_reports_requires_auth():
    response = client.get("/reports/history")
    assert response.status_code in [401, 403]

def test_admin_requires_auth():
    response = client.get("/admin/users")
    assert response.status_code in [401, 403]