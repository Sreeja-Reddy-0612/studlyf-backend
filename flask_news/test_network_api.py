#!/usr/bin/env python3
"""
Test script for Network API endpoints
Run this to test the Flask backend functionality
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_health_check():
    """Test if the API is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print("✅ Health Check:", response.json())
        return True
    except Exception as e:
        print("❌ Health Check Failed:", str(e))
        return False

def test_get_all_users():
    """Test getting all users (public endpoint)"""
    try:
        response = requests.get(f"{BASE_URL}/api/users")
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Get All Users: Found {len(users)} users")
            return True
        else:
            print("❌ Get All Users Failed:", response.status_code, response.text)
            return False
    except Exception as e:
        print("❌ Get All Users Failed:", str(e))
        return False

def test_protected_endpoint():
    """Test a protected endpoint without authentication"""
    try:
        response = requests.get(f"{BASE_URL}/api/profile/test-uid")
        if response.status_code == 401:
            print("✅ Protected Endpoint: Correctly requires authentication")
            return True
        else:
            print("❌ Protected Endpoint: Should return 401 without auth")
            return False
    except Exception as e:
        print("❌ Protected Endpoint Test Failed:", str(e))
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Network API Endpoints...")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_get_all_users,
        test_protected_endpoint
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print("-" * 30)
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Flask backend is working correctly.")
    else:
        print("⚠️ Some tests failed. Check your Flask app configuration.")

if __name__ == "__main__":
    main()

