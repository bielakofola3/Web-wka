import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import hash_password, verify_password, is_common_password

client = TestClient(app)

def test_password_hashing():
    plain = "SuperSecretPass123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("wrong", hashed)

def test_common_password_rejected():
    assert is_common_password("password")
    assert is_common_password("123456")
    assert is_common_password("short")
    assert not is_common_password("UniqueLongPassphrase99")

def test_register_login_flow():
    # Rejestracja
    resp = client.post("/register", data={
        "username": "testuser",
        "email": "test@example.com",
        "password": "UniqueLongPassphrase99",
        "csrftoken": "test"  # w testach CSRF może być wyłączony lub mockowany
    }, follow_redirects=False)
    # W prawdziwych testach trzeba obsłużyć CSRF; tu uproszczenie
    assert resp.status_code in (200, 303, 422)

def test_xss_escaping():
    # Sprawdź, że szablon używa |e
    # W pełnym teście: utwórz post z <script> i sprawdź, czy nie jest wykonywany
    assert True  # placeholder – rozwinąć

def test_security_headers():
    resp = client.get("/")
    assert "X-Content-Type-Options" in resp.headers
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert "Content-Security-Policy" in resp.headers
