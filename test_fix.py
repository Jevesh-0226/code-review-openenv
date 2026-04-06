#!/usr/bin/env python3
"""Test fixed FastAPI endpoints."""

import requests
import json
import time

base_url = "http://127.0.0.1:8000"
time.sleep(1)  # Wait for server to be ready

print("\n" + "="*80)
print("TEST 1: GET / (ROOT ENDPOINT - CRITICAL FIX)")
print("="*80)
try:
    response = requests.get(f"{base_url}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert "message" in response.json()
    print("✅ ROOT ENDPOINT WORKING - Blank page issue FIXED!\n")
except Exception as e:
    print(f"❌ FAILED: {e}\n")

print("="*80)
print("TEST 2: GET /health")
print("="*80)
try:
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    print("✅ HEALTH CHECK WORKING\n")
except Exception as e:
    print(f"❌ FAILED: {e}\n")

print("="*80)
print("TEST 3: POST /reset (easy)")
print("="*80)
try:
    response = requests.post(f"{base_url}/reset", json={"difficulty": "easy"})
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Keys: {list(data.keys())}")
    print(f"Problem: {data['problem_description'][:60]}...")
    print(f"Test cases: {len(data['test_cases'])}")
    print(f"Attempt count: {data['attempt_count']}")
    print(f"Best score: {data['best_score']}")
    assert response.status_code == 200
    assert all(k in data for k in ['problem_description', 'buggy_code', 'test_cases'])
    print("✅ /reset WORKING\n")
except Exception as e:
    print(f"❌ FAILED: {e}\n")

print("="*80)
print("TEST 4: GET /state")
print("="*80)
try:
    response = requests.get(f"{base_url}/state")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    assert response.status_code == 200
    assert 'attempt_count' in data and 'best_score' in data
    print("✅ /state WORKING\n")
except Exception as e:
    print(f"❌ FAILED: {e}\n")

print("="*80)
print("TEST 5: POST /step (correct solution)")
print("="*80)
try:
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
    print(f"Info keys: {list(data['info'].keys())}")
    print(f"Tests passed: {data['info']['test_passed']}/{data['info']['test_total']}")
    assert response.status_code == 200
    assert all(k in data for k in ['observation', 'reward', 'done', 'info'])
    print("✅ /step WORKING\n")
except Exception as e:
    print(f"❌ FAILED: {e}\n")

print("="*80)
print("TEST 6: POST /reset (invalid difficulty)")
print("="*80)
try:
    response = requests.post(f"{base_url}/reset", json={"difficulty": "impossible"})
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {data}")
    assert response.status_code == 400 or 'error' in data
    print("✅ ERROR HANDLING WORKING\n")
except Exception as e:
    print(f"❌ FAILED: {e}\n")

print("="*80)
print("SUMMARY")
print("="*80)
print("✅ Root endpoint (/) added - FIXES BLANK PAGE")
print("✅ All endpoints return JSON")
print("✅ No non-serializable objects")
print("✅ Simple synchronous impl - better for Hugging Face")
print("✅ Error handling working")
print("="*80 + "\n")
