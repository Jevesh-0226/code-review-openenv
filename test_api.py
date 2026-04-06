#!/usr/bin/env python3
"""Test script for CodeReviewEnv FastAPI server."""

import requests
import json

base_url = "http://127.0.0.1:8000"

def test_reset():
    """Test POST /reset endpoint."""
    print("=" * 80)
    print("TEST 1: POST /reset (easy)")
    print("=" * 80)
    response = requests.post(f"{base_url}/reset", json={"difficulty": "easy"})
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Keys: {list(data.keys())}")
    print(f"Problem: {data['problem_description'][:100]}...")
    print(f"Attempt Count: {data['attempt_count']}")
    print(f"Best Score: {data['best_score']}")
    print(f"Test Cases: {len(data['test_cases'])} cases")
    print(f"First test case type: {type(data['test_cases'][0])}")
    print(f"First test case: {data['test_cases'][0]}")
    print("✅ /reset endpoint working!\n")
    return response.status_code == 200

def test_state():
    """Test GET /state endpoint."""
    print("=" * 80)
    print("TEST 2: GET /state")
    print("=" * 80)
    response = requests.get(f"{base_url}/state")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    print("✅ /state endpoint working!\n")
    return response.status_code == 200

def test_step():
    """Test POST /step endpoint."""
    print("=" * 80)
    print("TEST 3: POST /step (with correct fix)")
    print("=" * 80)
    fixed_code = """def sum_range(start, end):
    \"\"\"Return the sum of integers from start to end (inclusive).\"\"\"
    total = 0
    for i in range(start, end + 1):
        total += i
    return total
"""
    response = requests.post(f"{base_url}/step", json={"fixed_code": fixed_code})
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Keys: {list(data.keys())}")
    print(f"Reward: {data['reward']}")
    print(f"Done: {data['done']}")
    print(f"Info Keys: {list(data['info'].keys())}")
    print(f"Info test passed: {data['info']['test_passed']}/{data['info']['test_total']}")
    print(f"Info test_score: {data['info']['test_score']}")
    print(f"Info syntax_valid: {data['info']['syntax_valid']}")
    print("✅ /step endpoint working!\n")
    return response.status_code == 200

def test_health():
    """Test GET /health endpoint."""
    print("=" * 80)
    print("TEST 0: GET /health")
    print("=" * 80)
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    print("✅ /health endpoint working!\n")
    return response.status_code == 200

if __name__ == "__main__":
    print("Starting API tests...\n")
    try:
        results = [
            ("Health Check", test_health()),
            ("Reset", test_reset()),
            ("State", test_state()),
            ("Step", test_step()),
        ]
        
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name}: {status}")
        
        if all(r[1] for r in results):
            print("\n🎉 All tests passed! API is ready for deployment.")
        else:
            print("\n⚠️  Some tests failed. Check the output above.")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
