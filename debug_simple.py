#!/usr/bin/env python3
"""Simple debug to see API response structure."""

import json
import sys
import os

# Add src to path
sys.path.insert(0, 'src')

# Import and setup
from diocesan_persona_builder.core.config import ONetCredentials, APIConfig
from diocesan_persona_builder.core.onet_api import ONetAPIClient

# Create client
credentials = ONetCredentials(username="ptdiocese", password="6344jwh")
config = APIConfig()
client = ONetAPIClient(credentials, config)

# Test different endpoints and print structure
endpoints = [
    ("skills", "online/occupations/43-6014.00/details/skills"),
    ("tasks", "online/occupations/43-6014.00/details/tasks"),
    ("knowledge", "online/occupations/43-6014.00/details/knowledge"),
    ("abilities", "online/occupations/43-6014.00/details/abilities"),
    ("interests", "online/occupations/43-6014.00/details/interests"),
    ("technology_skills", "online/occupations/43-6014.00/details/technology_skills"),
    ("education", "online/occupations/43-6014.00/details/education"),
    ("work_styles", "online/occupations/43-6014.00/details/work_styles"),
]

for name, endpoint in endpoints:
    print(f"\n=== {name.upper()} ENDPOINT ===")
    try:
        data = client._make_request(endpoint)
        print(f"Response keys: {list(data.keys())}")
        
        # Find the main data array
        if name == "tasks" and "task" in data:
            items = data["task"]
        elif "element" in data:
            items = data["element"]
        else:
            items = []
            
        if items and len(items) > 0:
            print(f"First item keys: {list(items[0].keys())}")
            print(f"First item sample: {json.dumps(items[0], indent=2)}")
        else:
            print("No items found")
            
    except Exception as e:
        print(f"Error: {e}")