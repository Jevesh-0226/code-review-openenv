"""Task definitions for CodeReviewEnv with real-world debugging scenarios."""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class TestCase:
    """Represents a single test case."""
    inputs: List[Any]
    expected_output: Any
    description: str = ""


@dataclass
class Task:
    """Represents a code debugging task."""
    name: str
    difficulty: str  # "easy", "medium", "hard"
    description: str
    buggy_code: str
    test_cases: List[TestCase]
    points: int


# ============================================================================
# TASK 1: Easy - Off-by-One Bug in Range
# ============================================================================

TASK_EASY = Task(
    name="off_by_one",
    difficulty="easy",
    description=(
        "Fix the off-by-one error in the sum_range function. "
        "The function should return the sum of integers from start to end (inclusive). "
        "Currently, it's missing the last element."
    ),
    buggy_code="""def sum_range(start, end):
    \"\"\"Return the sum of integers from start to end (inclusive).\"\"\"
    total = 0
    for i in range(start, end):  # BUG: should be range(start, end + 1)
        total += i
    return total
""",
    test_cases=[
        TestCase(inputs=[1, 5], expected_output=15, description="Sum 1 to 5 should be 15"),
        TestCase(inputs=[0, 10], expected_output=55, description="Sum 0 to 10 should be 55"),
        TestCase(inputs=[5, 5], expected_output=5, description="Single element should return that element"),
        TestCase(inputs=[1, 1], expected_output=1, description="Another single element"),
    ],
    points=25
)


# ============================================================================
# TASK 2: Medium - String Reversal Logic Error
# ============================================================================

TASK_MEDIUM = Task(
    name="string_reversal",
    difficulty="medium",
    description=(
        "Fix the reverse_words function. It should reverse the order of words in a string "
        "while keeping each word intact. For example: 'hello world' -> 'world hello'. "
        "The current implementation has a logic error with whitespace handling."
    ),
    buggy_code="""def reverse_words(text):
    \"\"\"Reverse the order of words in a string.\"\"\"
    words = text.split()
    reversed_words = []
    for i in range(len(words) - 1, -1, -1):
        reversed_words.append(words[i] + " ")  # BUG: adds extra space, doesn't clean last space
    return "".join(reversed_words)
""",
    test_cases=[
        TestCase(inputs=["hello world"], expected_output="world hello", description="Basic two-word reversal"),
        TestCase(inputs=["one two three four"], expected_output="four three two one", description="Multiple words"),
        TestCase(inputs=["single"], expected_output="single", description="Single word should remain unchanged"),
        TestCase(inputs=["a b c"], expected_output="c b a", description="Short words"),
        TestCase(inputs=["python  is  great"], expected_output="great is python", description="Multiple spaces"),
    ],
    points=35
)


# ============================================================================
# TASK 3: Hard - Fibonacci Optimization + Edge Cases
# ============================================================================

TASK_HARD = Task(
    name="fibonacci_optimization",
    difficulty="hard",
    description=(
        "Optimize the fibonacci function and handle edge cases correctly. "
        "The current recursive implementation is exponentially slow and missing base case handling. "
        "Your solution should be efficient (O(n) or better) and handle negative numbers, zero, and large values. "
        "For negative n, return 0. For n=0, return 0. For n=1, return 1."
    ),
    buggy_code="""def fibonacci(n):
    \"\"\"Return the nth Fibonacci number with memoization.
    
    Edge cases:
    - Negative n: return 0
    - n == 0: return 0
    - n == 1: return 1
    \"\"\"
    if n < 0:
        return 0
    if n == 0:
        return 0
    if n == 1:
        return 1
    # BUG: Simple recursion without memoization - extremely slow!
    return fibonacci(n - 1) + fibonacci(n - 2)
""",
    test_cases=[
        TestCase(inputs=[0], expected_output=0, description="Fibonacci(0) = 0"),
        TestCase(inputs=[1], expected_output=1, description="Fibonacci(1) = 1"),
        TestCase(inputs=[2], expected_output=1, description="Fibonacci(2) = 1"),
        TestCase(inputs=[5], expected_output=5, description="Fibonacci(5) = 5"),
        TestCase(inputs=[10], expected_output=55, description="Fibonacci(10) = 55"),
        TestCase(inputs=[-1], expected_output=0, description="Negative number should return 0"),
        TestCase(inputs=[20], expected_output=6765, description="Fibonacci(20) = 6765"),
    ],
    points=40
)


# Task registry
TASKS = {
    "easy": TASK_EASY,
    "medium": TASK_MEDIUM,
    "hard": TASK_HARD,
}


def get_task(difficulty: str) -> Task:
    """Get a task by difficulty level."""
    if difficulty not in TASKS:
        raise ValueError(f"Invalid difficulty: {difficulty}. Must be one of {list(TASKS.keys())}")
    return TASKS[difficulty]


def get_all_tasks() -> List[Task]:
    """Get all tasks in order."""
    return [TASK_EASY, TASK_MEDIUM, TASK_HARD]
