---
title: CodeReviewEnv
emoji: 🧠
colorFrom: green
colorTo: blue
sdk: docker
app_file: evaluate.py
pinned: false
---
# CodeReviewEnv: AI Code Debugging Environment

An OpenEnv compliant environment where AI agents learn to debug and improve Python code through real-world code review tasks. This hackathon project demonstrates a production-ready reinforcement learning environment with full API support, deterministic evaluation, and Docker deployment.

## 🎯 Objective

Enable AI agents to:
- Identify and fix bugs in Python code
- Optimize code for performance and readability
- Learn from test case feedback
- Improve iteratively through multiple attempts

## 📋 Overview

**CodeReviewEnv** simulates a real-world code review and debugging scenario where:
- An agent receives buggy Python code and a problem description
- The agent proposes a fix
- The environment grades the fix using test cases and code quality metrics
- The agent receives a reward (0.0 to 1.0) indicating solution quality
- The agent can iterate up to 5 times per task

## 🔌 OpenEnv API

The environment implements the complete OpenEnv specification:

### `reset(difficulty="easy") → Observation`

**Purpose**: Initialize/reset the environment for a new task

**Parameters**:
- `difficulty` (str): Task difficulty - "easy", "medium", or "hard"

**Returns** (`Observation`):
```python
{
    "problem_description": str,    # What needs to be fixed
    "buggy_code": str,            # Initial buggy code
    "test_cases": list,           # Test cases (inputs, expected outputs)
    "attempt_count": int,         # Current attempt number
    "best_score": float,          # Best score so far (0.0-1.0)
    "previous_feedback": str      # Feedback from last attempt (optional)
}
```

**Example**:
```python
from env.code_review_env import create_env

env = create_env()
obs = env.reset(difficulty="easy")
print(obs.problem_description)
print(obs.buggy_code)
```

### `step(fixed_code) → (observation, reward, done, info)`

**Purpose**: Submit fixed code and receive evaluation feedback

**Parameters**:
- `fixed_code` (str): The agent's proposed fixed code

**Returns**:
- `observation` (`Observation`): Updated observation with feedback
- `reward` (float): Score 0.0-1.0 indicating solution quality
- `done` (bool): Whether episode is complete (all attempts used or perfect score)
- `info` (`Info`): Detailed feedback

**Info structure**:
```python
{
    "test_passed": int,           # Number of passed tests
    "test_total": int,            # Total test cases
    "test_score": float,          # Fraction of tests passed
    "syntax_valid": bool,         # Whether code is syntactically valid
    "code_quality": float,        # 0.0-1.0 quality score
    "error_messages": list,       # Any errors encountered
    "test_details": list          # Per-test results
}
```

**Example**:
```python
fixed_code = """def sum_range(start, end):
    total = 0
    for i in range(start, end + 1):
        total += i
    return total
"""

obs, reward, done, info = env.step(fixed_code)
print(f"Reward: {reward:.4f}")
print(f"Tests passed: {info.test_passed}/{info.test_total}")
```

### `state() → Dict`

**Purpose**: Get current environment state without affecting it

**Returns**:
```python
{
    "attempt_count": int,         # Current attempt number
    "best_score": float,          # Best score achieved
    "done": bool,                 # Episode complete?
    "difficulty": str,            # Current difficulty level
    "rewards": list,              # Reward history
    "average_reward": float       # Mean reward across attempts
}
```

**Example**:
```python
state = env.state()
print(f"Average reward: {state['average_reward']:.4f}")
```

## 📚 Tasks

### Task 1: Easy - Off-by-One Bug (25 points)

**Problem**: The `sum_range(start, end)` function should return the sum of integers from `start` to `end` inclusive, but it's missing the last element.

**Buggy Code**:
```python
def sum_range(start, end):
    total = 0
    for i in range(start, end):  # BUG: should be range(start, end + 1)
        total += i
    return total
```

**Test Cases**:
- `sum_range(1, 5)` → 15
- `sum_range(0, 10)` → 55
- `sum_range(5, 5)` → 5

**Difficulty**: Straightforward off-by-one error

### Task 2: Medium - String Reversal (35 points)

**Problem**: The `reverse_words(text)` function should reverse the order of words while keeping each word intact (e.g., "hello world" → "world hello"). The current implementation mishandles whitespace.

**Buggy Code**:
```python
def reverse_words(text):
    words = text.split()
    reversed_words = []
    for i in range(len(words) - 1, -1, -1):
        reversed_words.append(words[i] + " ")  # BUG: extra space
    return "".join(reversed_words)
```

**Test Cases**:
- `reverse_words("hello world")` → "world hello"
- `reverse_words("one two three four")` → "four three two one"
- `reverse_words("single")` → "single"

**Difficulty**: Logic error with string manipulation and whitespace

### Task 3: Hard - Fibonacci Optimization (40 points)

**Problem**: Optimize the recursive `fibonacci(n)` function, which is exponentially slow. Must use memoization or iteration, and handle edge cases (negative numbers, n=0, n=1).

**Buggy Code**:
```python
def fibonacci(n):
    if n < 0:
        return 0
    if n == 0:
        return 0
    if n == 1:
        return 1
    return fibonacci(n - 1) + fibonacci(n - 2)  # BUG: No memoization!
```

**Test Cases**:
- `fibonacci(0)` → 0
- `fibonacci(10)` → 55
- `fibonacci(20)` → 6765
- `fibonacci(-1)` → 0

**Difficulty**: Algorithm optimization with proper edge case handling

## 🎯 Reward Function

The reward ranges from 0.0 to 1.0 and is calculated as:

### Perfect Solution Rule
```
IF all test cases pass AND syntax is valid:
  Final Score = 1.0
ELSE:
  Final Score = (T * 0.6) + (S * 0.2) + (Q * 0.2)
```

### Score Components

1. **Test Case Success (60%)**
   - Partial credit for each passing test
   - 0.0 if code doesn't compile or has runtime errors

2. **Syntax Validity (20%)**
   - 1.0 for syntactically valid code
   - 0.0 for syntax errors

3. **Code Quality (20%)**
   - Heuristic assessment of code efficiency and readability
   - Checks for reasonable variable names, code length, obvious inefficiencies

### Penalties
- Runtime errors: -0.2
- Stack overflow/timeout: -0.1 per occurrence
- Highly inefficient code: -0.3

### Final Processing
- Score is clamped to [0.0, 1.0]
- Perfect correctness always yields 1.0 reward

## 🤖 Baseline Agent

A deterministic agent using the Groq API (auto-selects available model):

**Features**:
- Uses Groq's free tier API
- **Temperature=0** for deterministic results
- **Top_p=1.0** for consistent sampling
- Reads from GROQ_API_KEY environment variable
- Iterative improvement: uses test feedback for multiple attempts
- Returns only fixed code (no explanations)
- Auto-detects working model from available Groq models

**Determinism Guarantee**:
- All inference parameters are fixed (temperature=0, top_p=1.0)
- No random seeds or stochastic elements
- Identical input → identical output (within Groq API constraints)

**Setup**:
```bash
export GROQ_API_KEY="your-api-key-here"
```

**Usage**:
```python
from agent.baseline_agent import create_agent

agent = create_agent()  # Auto-selects available model

obs = env.reset("easy")
fixed_code = agent.fix_code(
    obs.problem_description,
    obs.buggy_code,
    obs.previous_feedback
)

obs, reward, done, info = env.step(fixed_code)
```

## 📦 Installation

### Local Setup

**Requirements**:
- Python 3.10+
- pip

**Steps**:

1. Clone the repository:
```bash
cd code-review-openenv
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set API key (for baseline agent):
```bash
# Linux/macOS
export GROQ_API_KEY="your-groq-api-key"

# Windows PowerShell
$env:GROQ_API_KEY="your-groq-api-key"
```

4. Run the demo:
```bash
python run.py
```

5. Run full evaluation:
```bash
python evaluate.py
```

## 🐳 Docker Support

### Build and Run

**Build image**:
```bash
docker build -t code-review-env .
```

**Run with evaluation (no agent)**:
```bash
docker run code-review-env
```

**Run with Groq API key (with agent)**:
```bash
docker run -e GROQ_API_KEY="your-api-key" code-review-env
```

**Run with interactive shell**:
```bash
docker run -it code-review-env bash
```

### Docker Compose

For orchestrated deployment, you can extend this with docker-compose.yml.

## 🧪 Running the Project

### Option 1: Quick Demo (Local)

Shows all tasks with example fixes:
```bash
python run.py
```

**Output**:
- Task description
- Buggy code
- Test cases
- Example fixed code
- Evaluation results

### Option 2: Full Evaluation (Local)

Runs all tasks with the baseline agent:
```bash
python evaluate.py
```

**Requirements**:
- GROQ_API_KEY environment variable set

**Output**:
- Summary statistics
- Per-task results
- evaluation_results.json

### Option 3: Custom Agent

```python
from env.code_review_env import create_env

env = create_env()

# Task 1: Easy
obs = env.reset("easy")
# ... agent generates fixed_code ...
obs, reward, done, info = env.step(fixed_code)
print(f"Reward: {reward}")

# Task 2: Medium
obs = env.reset("medium")
# ...

# Task 3: Hard
obs = env.reset("hard")
# ...
```

## � Reproducibility

The evaluation pipeline is fully reproducible:

**Deterministic Inference**:
- LLM temperature: 0 (no randomness)
- Top-p: 1.0 (no truncation)
- Identical input → identical output

**Fixed Test Cases**:
- All test cases are hardcoded
- No randomized test data
- Consistent across runs

**Deterministic Grading**:
- Reward calculation uses only test results, syntax, and code quality
- No stochastic components
- Perfect rules: All tests pass → Score = 1.0

**Reproducibility Guarantee**:
- Run the same evaluation multiple times
- Expect identical or near-identical results
- Minor variations only from API infrastructure

## 📊 Baseline Results

**Expected Performance** (current available Groq model):

```
Easy Task:      0.95-1.00  (Perfect: all tests pass)
Medium Task:    0.85-1.00  (Usually perfect or near-perfect)
Hard Task:      0.85-1.00  (Usually perfect with optimization)

Average Score:  0.90-1.00  (90-100% overall)
```

**Performance Notes**:
- With deterministic inference (temperature=0), results are highly consistent
- Perfect correctness yields score = 1.0 (all tests passing)
- Groq model auto-detection ensures compatibility with API changes

**Example Recent Run**:
```
Easy:    1.0000 ✓
Medium:  1.0000 ✓  
Hard:    1.0000 ✓
Average: 1.0000
```

## 🏗️ Project Structure

```
code-review-openenv/
├── env/
│   ├── code_review_env.py    # Main environment (OpenEnv API)
│   ├── tasks.py              # Task definitions (easy/medium/hard)
│   └── grader.py             # Grader & reward calculation
├── agent/
│   └── baseline_agent.py     # Groq-based baseline agent
├── evaluate.py               # Full evaluation script
├── run.py                    # Quick demo script
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker configuration
├── openenv.yaml              # OpenEnv specification
└── README.md                 # This file
```

## 🔧 Design Decisions

### 1. Real-World Tasks

Chose actual bug patterns found in production code:
- Off-by-one errors (common in loops)
- String manipulation logic errors (regex, formatting)
- Algorithm optimization issues (recursion, performance)

### 2. Partial Rewards

Scores are partial (0.0-1.0) rather than binary:
- Agents learn from partial progress
- Encourages iterative improvement
- Allows fine-grained evaluation

### 3. Groq API Choice

Used Groq instead of OpenAI:
- Free tier with generous limits
- Faster inference
- Deterministic with temperature=0
- Hackathon-friendly

### 4. Deterministic Grading

All evaluation is deterministic:
- Test cases are fixed
- Grading logic is reproducible
- No randomness in reward calculation
- Enables fair comparisons

### 5. Multi-Attempt Learning

Agents get 5 attempts per task:
- Encourages iterative improvement
- Simulates real debugging workflow
- Allows learning from feedback

## ⚙️ Advanced Usage

### Custom Task Addition

```python
from env.tasks import Task, TestCase

new_task = Task(
    name="custom_bug",
    difficulty="medium",
    description="Fix this specific bug...",
    buggy_code="...",
    test_cases=[
        TestCase(inputs=[1, 2], expected_output=3),
        # ... more test cases
    ],
    points=30
)
```

### Custom Grader

Extend `grader.py` to add custom quality metrics:

```python
from env.grader import Grader

class CustomGrader(Grader):
    def assess_code_quality(self, code: str) -> float:
        # Custom quality logic
        pass
```

### Custom Agent

```python
class CustomAgent:
    def fix_code(self, problem, buggy_code, feedback):
        # Custom fixing logic
        pass
```

## 🐛 Troubleshooting

### GROQ_API_KEY not set

**Error**: `ValueError: GROQ_API_KEY environment variable not set`

**Solution**: Set the API key before running:
```bash
export GROQ_API_KEY="your-key"
python evaluate.py
```

### Import errors

**Error**: `ModuleNotFoundError: No module named 'groq'`

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Timeout errors

**Error**: Fibonacci test times out

**Reason**: Recursive implementation without memoization

**Solution**: The grader expects optimized (O(n)) implementation

### Docker build issues

**Error**: `base image not found`

**Solution**: Ensure internet connection, Docker daemon running:
```bash
docker pull python:3.10-slim
docker build -t code-review-env .
```

## 📈 Metrics & Evaluation

### Key Metrics

1. **Final Score**: 0.0-1.0 overall performance
2. **Test Pass Rate**: Fraction of test cases passed
3. **Syntax Validity**: Whether code compiles/parses
4. **Code Quality**: Heuristic quality assessment
5. **Attempt Count**: Number of iterations needed
6. **Average Reward**: Mean reward across all attempts

### Reproducibility

All evaluation is deterministic:
- Fixed random seeds
- Temperature=0 for LLM
- Deterministic test cases
- Reproducible grading

## 📝 OpenEnv Specification Compliance

This project fully implements OpenEnv requirements:

- ✅ **API Compliance**: reset(), step(), state()
- ✅ **Typed Structures**: Observation, Info, Task
- ✅ **Reward Function**: 0.0-1.0 range, partial scores
- ✅ **Real-World Task**: Code debugging (not a game)
- ✅ **Deterministic Grading**: No randomness after seed
- ✅ **Multi-Task**: Easy, medium, hard difficulty
- ✅ **OpenEnv Configuration**: openenv.yaml included
- ✅ **Baseline Agent**: Groq llama3-70b-8192 deterministic
- ✅ **Evaluation Script**: Complete evaluation.py
- ✅ **Docker Support**: Full Dockerfile included
- ✅ **Documentation**: Comprehensive README

## 🚀 Submission Checklist

Before submitting to hackathon:

- [x] All files present (env/, agent/, configs, scripts)
- [x] OpenEnv API fully implemented
- [x] 3 tasks (easy, medium, hard) with test cases
- [x] Grader with partial rewards
- [x] Baseline agent (Groq API)
- [x] Evaluation script runs successfully
- [x] Docker builds and runs
- [x] openenv.yaml present and valid
- [x] README complete and detailed
- [x] No hardcoded secrets
- [x] Deterministic behavior
- [x] Proper error handling

## 📄 License

This project is open source for hackathon evaluation.

## 🤝 Technical Support

For issues:
1. Check troubleshooting section
2. Review error messages in evaluation_results.json
3. Run with verbose output: `python -u evaluate.py`
4. Check Docker logs: `docker logs <container-id>`

---

**Created for OpenEnv Hackathon**  
Production-ready, fully tested, competition-grade implementation.
