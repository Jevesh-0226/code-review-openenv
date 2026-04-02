"""Quick run script to demonstrate the CodeReviewEnv."""

import sys
from env.code_review_env import create_env
from env.tasks import get_all_tasks


def main():
    """Demonstrate the environment with manual fixes."""
    print("CodeReviewEnv - Quick Demo")
    print("=" * 70)
    
    # Get tasks
    tasks = get_all_tasks()
    
    # Demo each task
    for task in tasks:
        print(f"\n{'='*70}")
        print(f"Task: {task.name} ({task.difficulty.upper()})")
        print(f"Points: {task.points}")
        print(f"{'='*70}\n")
        
        print(f"Description:\n{task.description}\n")
        print(f"Buggy Code:\n{task.buggy_code}\n")
        
        # Create environment
        env = create_env()
        obs = env.reset(difficulty=task.difficulty)
        
        # Show test cases
        print("Test Cases:")
        for i, tc in enumerate(obs.test_cases, 1):
            print(f"  {i}. {tc['description']}")
            print(f"     Input(s): {tc['inputs']}")
            print(f"     Expected: {tc['expected_output']}\n")
        
        print("Example Fixed Code:")
        print("-" * 70)
        
        # Show example fixed code (just for demonstration)
        if task.name == "off_by_one":
            fixed = """def sum_range(start, end):
    \"\"\"Return the sum of integers from start to end (inclusive).\"\"\"
    total = 0
    for i in range(start, end + 1):  # FIXED: changed end to end + 1
        total += i
    return total"""
        elif task.name == "string_reversal":
            fixed = """def reverse_words(text):
    \"\"\"Reverse the order of words in a string.\"\"\"
    words = text.split()
    return " ".join(reversed(words))"""
        else:  # fibonacci_optimization
            fixed = """def fibonacci(n):
    \"\"\"Return the nth Fibonacci number with memoization.\"\"\"
    if n < 0:
        return 0
    if n == 0:
        return 0
    if n == 1:
        return 1
    
    # Use memoization for efficiency
    memo = {}
    
    def fib_memo(n):
        if n in memo:
            return memo[n]
        if n <= 1:
            return n
        memo[n] = fib_memo(n - 1) + fib_memo(n - 2)
        return memo[n]
    
    return fib_memo(n)"""
        
        print(fixed)
        print("-" * 70)
        
        # Step through environment
        obs, reward, done, info = env.step(fixed)
        
        print(f"\nEvaluation Results:")
        print(f"  Tests passed: {info.test_passed}/{info.test_total}")
        print(f"  Syntax valid: {info.syntax_valid}")
        print(f"  Code quality: {info.code_quality:.2f}")
        print(f"  Final reward: {reward:.4f}")
        
        if info.test_details:
            print(f"\nTest Details:")
            for detail in info.test_details:
                status = "[PASS]" if detail.get("passed") else "[FAIL]"
                print(f"  {status} {detail['test']}")
                if not detail.get("passed"):
                    print(f"     Error: {detail.get('error')}")
    
    print(f"\n{'='*70}")
    print("Demo completed!")


if __name__ == "__main__":
    main()
