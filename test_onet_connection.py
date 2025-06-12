#!/usr/bin/env python3
"""Simple test to verify O*NET API connection."""

import requests
from requests.auth import HTTPBasicAuth
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Your credentials
username = "ptdiocese"
password = "6344jwh"

# Test URLs
base_url = "https://services.onetcenter.org/ws"
test_endpoints = [
    f"{base_url}/online/occupations/43-6014.00",  # Basic occupation info
    f"{base_url}/online/occupations",             # List occupations
]

print("Testing O*NET API connection...")
print(f"Username: {username}")
print("="*50)

session = requests.Session()
session.auth = HTTPBasicAuth(username, password)
session.verify = False  # Disable SSL verification
session.headers.update({
    "Accept": "application/json",
    "User-Agent": "diocesan-persona-builder-test/0.1.0"
})

for url in test_endpoints:
    print(f"\nTesting: {url}")
    try:
        response = session.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            if isinstance(data, dict) and 'occupation' in data:
                print(f"Occupation title: {data['occupation'][0].get('title', 'N/A')}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"Exception: {e}")

print("\n" + "="*50)
print("Test complete.")