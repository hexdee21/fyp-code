import requests

BASE_URL = "http://localhost:5173"

def test_admin_login_success():
    payload = {
        "email": "admin@example.com",
        "password": "admin123"
    }

    res = requests.post(f"{BASE_URL}/login", json=payload)

    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["role"] == "admin"
    assert "token" in res.json()
