#!/usr/bin/env python3
"""
Test script for the webhook functionality
Run this to test the webhook locally and verify it's working correctly
"""

import json
import requests
import time
import sys
from pathlib import Path

# Test data for different scenarios
TEST_PAYLOADS = {
    "pr_opened": {
        "action": "opened",
        "pull_request": {
            "issue_url": "https://api.github.com/repos/test/repo/issues/1",
            "statuses_url": "https://api.github.com/repos/test/repo/statuses/abc123"
        }
    },
    "pr_labeled": {
        "action": "labeled",
        "pull_request": {
            "issue_url": "https://api.github.com/repos/test/repo/issues/2",
            "statuses_url": "https://api.github.com/repos/test/repo/statuses/def456"
        }
    },
    "pr_synchronized": {
        "action": "synchronize",
        "pull_request": {
            "issue_url": "https://api.github.com/repos/test/repo/issues/3",
            "statuses_url": "https://api.github.com/repos/test/repo/statuses/ghi789"
        }
    },
    "pr_closed": {
        "action": "closed",
        "pull_request": {
            "issue_url": "https://api.github.com/repos/test/repo/issues/4",
            "statuses_url": "https://api.github.com/repos/test/repo/statuses/jkl012"
        }
    }
}


def test_endpoint(base_url, endpoint, method="GET", data=None):
    """Test an endpoint and return the results"""
    url = f"{base_url}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Testing {method} {url}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        
        if method.upper() == "POST":
            response = requests.post(
                url, 
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
        else:
            response = requests.get(url, timeout=30)
        
        duration = (time.time() - start_time) * 1000
        
        print(f"Response Code: {response.status_code}")
        print(f"Response Time: {duration:.2f}ms")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            print(f"Response Body: {json.dumps(response_json, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response Body: {response.text}")
        
        return {
            'success': True,
            'status_code': response.status_code,
            'duration_ms': duration,
            'response': response.text
        }
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out (30s)")
        return {'success': False, 'error': 'timeout'}
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the server running?")
        return {'success': False, 'error': 'connection_error'}
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {'success': False, 'error': str(e)}


def main():
    """Main test function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:5000"
    
    print(f"Testing webhook at: {base_url}")
    print(f"Current directory: {Path.cwd()}")
    
    # Test health check
    health_result = test_endpoint(base_url, "/health")
    
    # Test config endpoint
    config_result = test_endpoint(base_url, "/config")
    
    # Test webhook endpoints with different scenarios
    webhook_results = {}
    for scenario, payload in TEST_PAYLOADS.items():
        print(f"\n🧪 Testing scenario: {scenario}")
        result = test_endpoint(base_url, "/", "POST", payload)
        webhook_results[scenario] = result
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    print(f"Health Check: {'✅' if health_result.get('success') else '❌'}")
    print(f"Config Check: {'✅' if config_result.get('success') else '❌'}")
    
    for scenario, result in webhook_results.items():
        status = '✅' if result.get('success') else '❌'
        duration = result.get('duration_ms', 0)
        print(f"Webhook {scenario}: {status} ({duration:.0f}ms)")
    
    # Check for performance issues
    slow_requests = [
        (name, result) for name, result in webhook_results.items() 
        if result.get('duration_ms', 0) > 5000
    ]
    
    if slow_requests:
        print(f"\n⚠️  Slow requests (>5s):")
        for name, result in slow_requests:
            print(f"  - {name}: {result.get('duration_ms', 0):.0f}ms")
    
    # Check for errors
    errors = [
        (name, result) for name, result in webhook_results.items() 
        if not result.get('success')
    ]
    
    if errors:
        print(f"\n❌ Failed requests:")
        for name, result in errors:
            print(f"  - {name}: {result.get('error', 'unknown error')}")
    
    print(f"\n📝 Check the logs for detailed information about each request")


if __name__ == "__main__":
    main() 