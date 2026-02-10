import requests
from config import BASE_URL

def login(email, password):
    res = requests.post(
        f"{BASE_URL}/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert res.status_code == 200

    data = res.json()
    return {
        "token": data["token"],
        "wallet": data["wallet"],
        "role": data["role"]
    }
