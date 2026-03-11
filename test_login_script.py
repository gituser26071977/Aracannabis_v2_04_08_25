#!/usr/bin/env python3
"""
Test script for verifying patient login
"""
import requests
import sys

def test_login():
    url = "http://localhost:5002/api/patient-auth/login"
    data = {
        "email": "paciente.teste@example.com",
        "senha": "senhateste123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        if response.status_code == 200:
            print("✅ LOGIN SUCCESS")
            return 0
        else:
            print("❌ LOGIN FAILED")
            return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(test_login())
