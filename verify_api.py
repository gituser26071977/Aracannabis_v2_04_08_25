
import requests

# Inside container, app listens on 5002.
BASE_URL = "http://localhost:5002"

def test_health():
    print(f"Testing Health Check at {BASE_URL}/api/status...")
    try:
        resp = requests.get(f"{BASE_URL}/api/status")
        print(f"Health Check: {resp.status_code}")
        if resp.status_code == 200:
            print(resp.json())
            return True
        return False
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return False

def test_login():
    url = f"{BASE_URL}/api/auth/login"
    print(f"Testing Login at {url}...")
    payload = {
        "usuario": "admin",
        "senha": "Aracannabis@2025"
    }
    try:
        resp = requests.post(url, json=payload)
        print(f"Login Status: {resp.status_code}")
        if resp.status_code == 200:
            token = resp.json().get('access_token')
            print("Login Successful, Token received")
            return token
        else:
            print(f"Login Failed: {resp.text}")
            return None
    except Exception as e:
        print(f"Login Exception: {e}")
        return None

def test_profile(token):
    url = f"{BASE_URL}/api/auth/profile"
    print(f"Testing Profile at {url}...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
        print(f"Profile Status: {resp.status_code}")
        if resp.status_code == 200:
            print(resp.json())
            return True
        else:
            print(f"Profile Failed: {resp.text}")
            return False
    except Exception as e:
        print(f"Profile Exception: {e}")
        return False

if __name__ == "__main__":
    if test_health():
        token = test_login()
        if token:
            test_profile(token)
