#!/usr/bin/env python3
"""
Debug version of Option B endpoint verification with enhanced logging.
"""

import os
import requests
import json

def debug_api_access():
    """Debug API access and token configuration."""
    print("🔍 Debugging Option B Endpoint Access")
    print("=" * 50)
    
    devin_token = os.getenv('DEVIN_API_TOKEN')
    
    print(f"Token present: {bool(devin_token)}")
    if devin_token:
        print(f"Token length: {len(devin_token)}")
        print(f"Token prefix: {devin_token[:10]}...")
    else:
        print("❌ No DEVIN_API_TOKEN found in environment")
        return
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {devin_token}'
    }
    
    print(f"\nTesting basic connectivity to api.devin.ai...")
    
    try:
        response = requests.get('https://api.devin.ai', timeout=10)
        print(f"Base URL response: {response.status_code}")
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        return
    
    print(f"\nTesting session creation endpoint...")
    url = "https://api.devin.ai/v1/sessions"
    payload = {
        "prompt": "Simple test prompt",
        "unlisted": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text[:500]}...")
        
        if response.status_code == 401:
            print("❌ Authentication failed - token may be invalid or expired")
        elif response.status_code == 403:
            print("❌ Authorization failed - token may lack required permissions")
        elif response.status_code == 404:
            print("❌ Endpoint not found - URL may be incorrect")
        
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == '__main__':
    debug_api_access()
