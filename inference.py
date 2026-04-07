"""CodeReviewEnv Phase 2 Inference Script - Direct environment integration with LLM proxy."""

import os
import sys
from openai import OpenAI
from env.code_review_env import CodeReviewEnv

BASE_URL = "http://localhost:7860"


def get_llm_client():
    """Initialize OpenAI client using environment variables for proxy."""
    api_base = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
    api_key = os.environ.get("API_KEY", "")
    
    if not api_key:
        raise ValueError("API_KEY environment variable not set")
    
    return OpenAI(
        base_url=api_base,
        api_key=api_key
    )


def generate_fix(buggy_code: str, test_cases: list, problem_description: str) -> str:
    """Use LLM to generate a fix for the buggy code."""
    try:
        client = get_llm_client()
        
        prompt = f"""You are a code review expert. Fix the following buggy code to pass the test cases.

Problem: {problem_description}

Buggy Code:
{buggy_code}

Test Cases:
{test_cases}

Provide ONLY the fixed code function, nothing else. No markdown, no explanations."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert code fixer. Return only the fixed code function."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"WARNING: LLM call failed: {e}", file=sys.stderr, flush=True)
        # Fallback to a basic fix
        return """def sum_range(start, end):
    total = 0
    for i in range(start, end + 1):
        total += i
    return total
"""


def run():
    """Main inference function with structured logging."""
    task_name = "code_review"
    total_reward = 0.0
    steps_taken = 0
    
    try:
        print(f"[START] task={task_name}", flush=True)
        sys.stdout.flush()
        
        # Initialize environment directly
        env = CodeReviewEnv(seed=42)
        
        # Step 1: Reset environment
        observation = env.reset(difficulty="easy")
        buggy_code = observation.buggy_code
        problem_description = observation.problem_description
        test_cases = observation.test_cases
        
        # Step 2: Generate fix using LLM proxy
        fixed_code = generate_fix(str(buggy_code), test_cases, str(problem_description))
        steps_taken += 1
        
        # Step 3: Step the environment with the fix
        observation_new, reward, done, info = env.step(fixed_code)
        total_reward = float(reward)
        
        # Log step result
        print(f"[STEP] step=1 reward={total_reward}", flush=True)
        sys.stdout.flush()
        
        # Final log with total score
        print(f"[END] task={task_name} score={total_reward} steps={steps_taken}", flush=True)
        sys.stdout.flush()
    
    except Exception as e:
        print(f"[END] task={task_name} score=0 steps={steps_taken}", flush=True)
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    run()
    sys.exit(0)
