#!/usr/bin/env python3
"""
Test script to check API functionality
"""

import requests
import json

def test_api_endpoints():
    base_url = "http://localhost:5001"
    
    print("Testing API endpoints...")
    
    # Test 1: System status
    print("\n1. Testing /api/status...")
    try:
        response = requests.get(f"{base_url}/api/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Graph list
    print("\n2. Testing /api/graph/list...")
    try:
        response = requests.get(f"{base_url}/api/graph/list")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Graph get
    print("\n3. Testing /api/graph/get...")
    try:
        response = requests.get(f"{base_url}/api/graph/get?name=graph_1FfmbHfnpaZj.json")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Graph data retrieved successfully")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: Frontend serving
    print("\n4. Testing /frontend/index.html...")
    try:
        response = requests.get(f"{base_url}/frontend/index.html")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("Frontend served successfully")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()
