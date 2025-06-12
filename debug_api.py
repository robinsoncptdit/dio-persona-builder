#!/usr/bin/env python3
"""Debug O*NET API response structure."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from diocesan_persona_builder.core.config import ONetCredentials, APIConfig

# Create client
credentials = ONetCredentials(username="ptdiocese", password="6344jwh")
config = APIConfig()

from diocesan_persona_builder.core.onet_api import ONetAPIClient

client = ONetAPIClient(credentials, config)

print("Testing API response structure...")
print("="*50)

try:
    # Test skills endpoint
    endpoint = "online/occupations/43-6014.00/details/skills"
    data = client._make_request(endpoint)
    
    print(f"Skills endpoint response keys: {list(data.keys())}")
    if 'element' in data and len(data['element']) > 0:
        print(f"First skill element keys: {list(data['element'][0].keys())}")
        print(f"First skill element: {data['element'][0]}")
    
    print("\n" + "="*50)
    
    # Test tasks endpoint
    endpoint = "online/occupations/43-6014.00/details/tasks"
    data = client._make_request(endpoint)
    
    print(f"Tasks endpoint response keys: {list(data.keys())}")
    if 'task' in data and len(data['task']) > 0:
        print(f"First task element keys: {list(data['task'][0].keys())}")
        print(f"First task element: {data['task'][0]}")
        
except Exception as e:
    print(f"Error: {e}")