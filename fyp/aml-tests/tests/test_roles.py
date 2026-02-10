import requests
from auth_api import login
from config import BASE_URL

def test_admin_can_deposit():
    admin = login("admin@example.com", "admin123")
    user = login("a7@example.com", "test123")

    res = requests.post(
        f"{BASE_URL}/admin/deposit",
        json={
            "wallet_id": user["wallet"],
            "amount": 2000
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        }
    )

    assert res.status_code == 200


def test_user_cannot_deposit():
    user = login("a7@example.com", "test123")

    res = requests.post(
        f"{BASE_URL}/admin/deposit",
        json={
            "wallet_id": user["wallet"],
            "amount": 2000
        },
        headers={
            "Authorization": f"Bearer {user['token']}"
        }
    )

    assert res.status_code == 403
