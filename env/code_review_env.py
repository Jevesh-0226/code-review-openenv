"""CodeReviewEnv: An OpenEnv environment for AI code review and debugging."""

from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict, field
import json

from .tasks import Task, get_task, TestCase
from .grader import Grader, GradeResult


@dataclass
class Observation:
    """Observation structure for the environment."""
    problem_description: str
    buggy_code: str
    test_cases: list  # List of test cases (dicts)
    attempt_count: int
    best_score: float
    previous_feedback: Optional[str] = None


@dataclass
class Info:
    """Info structure containing detailed feedback."""
    test_passed: int
    test_total: int
    test_score: float
    syntax_valid: bool
    code_quality: float
    error_messages: list = field(default_factory=list)
    test_details: list = field(default_factory=list)


class CodeReviewEnv:
    """OpenEnv environment for AI code debugging and review."""

    def __init__(self, seed: int = 42):
        """Initialize the environment."""
        self.seed = seed
        self.grader = Grader()
        
        # State variables
        self.current_task: Optional[Task] = None
        self.current_difficulty: Optional[str] = None
        self.attempt_count: int = 0
        self.best_score: float = 0.0
        self.best_code: Optional[str] = None
        self.episode_done: bool = False
        self.previous_feedback: Optional[str] = None
        
        # Episode tracking
        self.episode_rewards: list = []
        
    def reset(self, difficulty: str = "easy") -> Observation:
        """
        Reset the environment and return initial observation.
        
        Args:
            difficulty: Task difficulty level ("easy", "medium", "hard")
            
        Returns:
            Observation with problem description, buggy code, and test cases
        """
        self.current_difficulty = difficulty
        self.current_task = get_task(difficulty)
        self.attempt_count = 0
        self.best_score = 0.0
        self.best_code = None
        self.episode_done = False
        self.previous_feedback = None
        self.episode_rewards = []
        
        # Prepare test cases for observation
        test_cases_dicts = []
        for tc in self.current_task.test_cases:
            test_cases_dicts.append({
                "inputs": tc.inputs,
                "expected_output": tc.expected_output,
                "description": tc.description
            })
        
        return Observation(
            problem_description=self.current_task.description,
            buggy_code=self.current_task.buggy_code,
            test_cases=test_cases_dicts,
            attempt_count=0,
            best_score=0.0
        )

    def step(self, fixed_code: str) -> Tuple[Observation, float, bool, Info]:
        """
        Evaluate the agent's fix and return feedback.
        
        Args:
            fixed_code: The agent's proposed fixed code
            
        Returns:
            Tuple of (observation, reward, done, info)
        """
        if self.current_task is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        
        self.attempt_count += 1
        
        # Extract test cases
        test_cases_for_grading = []
        for tc in self.current_task.test_cases:
            test_cases_for_grading.append({
                "inputs": tc.inputs,
                "expected_output": tc.expected_output,
                "description": tc.description
            })
        
        # Grade the submission
        function_name = self._extract_function_name(self.current_task.buggy_code)
        grade_result: GradeResult = self.grader.grade(
            fixed_code, 
            function_name, 
            test_cases_for_grading
        )
        
        reward = grade_result.final_score
        
        # Update best score
        if grade_result.final_score > self.best_score:
            self.best_score = grade_result.final_score
            self.best_code = fixed_code
        
        self.episode_rewards.append(reward)
        
        # Determine if episode is done (success or max attempts)
        max_attempts = 5
        is_done = (reward >= 1.0) or (self.attempt_count >= max_attempts)
        self.episode_done = is_done
        
        # Prepare feedback
        feedback_lines = []
        if grade_result.errors:
            feedback_lines.extend(grade_result.errors)
        
        if grade_result.details.get("test_results"):
            for result in grade_result.details["test_results"]:
                if result.get("passed"):
                    feedback_lines.append(f"✓ {result['test']}")
                else:
                    feedback_lines.append(f"✗ {result['test']}: {result.get('error', 'Failed')}")
        
        self.previous_feedback = "\n".join(feedback_lines)
        
        # Prepare info
        info = Info(
            test_passed=grade_result.passed_tests,
            test_total=grade_result.total_tests,
            test_score=grade_result.test_case_score,
            syntax_valid=(grade_result.syntax_score == 1.0),
            code_quality=grade_result.quality_score,
            error_messages=grade_result.errors,
            test_details=grade_result.details.get("test_results", [])
        )
        
        # Prepare next observation
        observation = Observation(
            problem_description=self.current_task.description,
            buggy_code=self.current_task.buggy_code,
            test_cases=[
                {
                    "inputs": tc.inputs,
                    "expected_output": tc.expected_output,
                    "description": tc.description
                }
                for tc in self.current_task.test_cases
            ],
            attempt_count=self.attempt_count,
            best_score=self.best_score,
            previous_feedback=self.previous_feedback
        )
        
        return observation, reward, is_done, info

    def state(self) -> Dict[str, Any]:
        """
        Return the current state of the environment.
        
        Returns:
            Dict with attempt count, best score, and done status
        """
        return {
            "attempt_count": self.attempt_count,
            "best_score": self.best_score,
            "done": self.episode_done,
            "difficulty": self.current_difficulty,
            "rewards": self.episode_rewards,
            "average_reward": sum(self.episode_rewards) / len(self.episode_rewards) if self.episode_rewards else 0.0
        }

    def _extract_function_name(self, code: str) -> str:
        """Extract the function name from buggy code."""
        import ast
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return node.name
        except:
            pass
        return "solution"  # Default fallback

    def render(self, mode: str = "human"):
        """Render the environment state."""
        if mode == "human":
            if self.current_task:
                print(f"\n{'='*60}")
                print(f"Task: {self.current_task.name}")
                print(f"Difficulty: {self.current_difficulty}")
                print(f"Attempts: {self.attempt_count}")
                print(f"Best Score: {self.best_score:.2f}")
                print(f"{'='*60}\n")

    def get_task_info(self) -> Dict[str, Any]:
        """Get detailed task information."""
        if self.current_task is None:
            return {}
        
        return {
            "name": self.current_task.name,
            "difficulty": self.current_task.difficulty,
            "description": self.current_task.description,
            "points": self.current_task.points,
            "test_count": len(self.current_task.test_cases)
        }


def create_env(seed: int = 42) -> CodeReviewEnv:
    """Factory function to create the environment."""
    return CodeReviewEnv(seed=seed)
