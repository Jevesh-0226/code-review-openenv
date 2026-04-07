"""Client script for calling CodeReviewEnv API endpoints."""

import requests

BASE_URL = "http://localhost:7860"


def run():
    """Run inference by calling the deployed API endpoints."""
    try:
        # Step 1: Reset environment
        print("Step 1: Resetting environment...")
        res = requests.post(f"{BASE_URL}/reset", json={"difficulty": "easy"})
        data = res.json()
        
        if "error" in data:
            print(f"Reset error: {data['error']}")
            return
        
        observation = data.get("observation", data)
        print(f"Problem: {observation['problem_description'][:100]}...")
        
        # Step 2: Extract buggy code
        buggy_code = observation["buggy_code"]
        print(f"\nBuggy code:\n{buggy_code}")
        
        # Step 3: Apply fix
        fixed_code = """def sum_range(start, end):
    total = 0
    for i in range(start, end + 1):
        total += i
    return total
"""
        print(f"\nFixed code:\n{fixed_code}")
        
        # Step 4: Send fix to API
        print("\nStep 2: Submitting fix...")
        res = requests.post(f"{BASE_URL}/step", json={"fixed_code": fixed_code})
        result = res.json()
        
        if "error" in result:
            print(f"Step error: {result['error']}")
            return
        
        # Step 5: Display results
        print("\n" + "="*60)
        print("FINAL RESULT")
        print("="*60)
        print(f"Reward: {result.get('reward', 'N/A')}")
        print(f"Done: {result.get('done', 'N/A')}")
        
        info = result.get("info", {})
        print(f"\nTest Results:")
        print(f"  Tests Passed: {info.get('test_passed', 'N/A')} / {info.get('test_total', 'N/A')}")
        print(f"  Test Score: {info.get('test_score', 'N/A')}")
        print(f"  Syntax Valid: {info.get('syntax_valid', 'N/A')}")
        print(f"  Code Quality: {info.get('code_quality', 'N/A')}")
        
        if info.get("error_messages"):
            print(f"\nError Messages:")
            for msg in info["error_messages"]:
                print(f"  - {msg}")

    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to API at {BASE_URL}")
        print("Make sure the server is running with: python -m server.app:main")
    except Exception as e:
        print(f"ERROR: {str(e)}")


if __name__ == "__main__":
    run()
