
import requests

# URL of the backend API
BASE_URL = "http://localhost:5010"

def trigger_password_reset():
    endpoint = f"{BASE_URL}/auth/request-password-setup"
    payload = {
        "email": "abholzwarth@gmail.com"
    }
    
    print(f"Sending request to {endpoint} with payload: {payload}")
    
    try:
        response = requests.post(endpoint, json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("SUCCESS: Password setup email triggered!")
        else:
            print("FAILURE: Could not trigger email.")
            
    except Exception as e:
        print(f"Error calling API: {e}")

if __name__ == "__main__":
    trigger_password_reset()
