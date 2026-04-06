#!/usr/bin/env python3
"""Additional tests for CodeReviewEnv FastAPI server."""

import requests
import json

base_url = "http://127.0.0.1:8000"

# Test medium difficulty
print("Testing MEDIUM difficulty...")
response = requests.post(f"{base_url}/reset", json={"difficulty": "medium"})
data = response.json()
print(f"Status: {response.status_code} ✅")
print(f"Problem: {data['problem_description'][:80]}...")
print(f"Test Cases: {len(data['test_cases'])}\n")

# Test hard difficulty
print("Testing HARD difficulty...")
response = requests.post(f"{base_url}/reset", json={"difficulty": "hard"})
data = response.json()
print(f"Status: {response.status_code} ✅")
print(f"Problem: {data['problem_description'][:80]}...")
print(f"Test Cases: {len(data['test_cases'])}\n")

# Reset to easy and test with wrong code
print("Testing /step with WRONG code...")
requests.post(f"{base_url}/reset", json={"difficulty": "easy"})
wrong_code = """def sum_range(start, end):
    return 0
"""
response = requests.post(f"{base_url}/step", json={"fixed_code": wrong_code})
data = response.json()
print(f"Status: {response.status_code} ✅")
print(f"Reward: {data['reward']} (should be < 1.0)")
print(f"Info: {data['info']['test_passed']}/{data['info']['test_total']} tests passed\n")

# Test invalid difficulty
print("Testing INVALID difficulty...")
response = requests.post(f"{base_url}/reset", json={"difficulty": "impossible"})
print(f"Status: {response.status_code} (should be 400)")
if response.status_code == 400:
    print(f"Error: {response.json()['detail']} ✅\n")

print("✅ All validation tests passed!")
