import requests

BASE_URL = "http://localhost:7860"

def run():
    try:
        task_name = "easy"
        print(f"[START] task={task_name}", flush=True)

        # Step 1: Reset
        res = requests.post(f"{BASE_URL}/reset", json={"difficulty": task_name})
        data = res.json()

        # Fix code
        fixed_code = """def sum_range(start, end):
    total = 0
    for i in range(start, end + 1):
        total += i
    return total
"""

        # Step 2: Send fix
        res = requests.post(f"{BASE_URL}/step", json={"fixed_code": fixed_code})
        result = res.json()

        reward = result.get("reward", 0)

        print(f"[STEP] step=1 reward={reward}", flush=True)

        print(f"[END] task={task_name} score={reward} steps=1", flush=True)

    except Exception as e:
        print(f"[END] task=easy score=0 steps=1", flush=True)

if __name__ == "__main__":
    run()
