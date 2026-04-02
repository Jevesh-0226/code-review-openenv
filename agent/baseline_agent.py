"""Baseline agent using Groq API for code debugging."""

import os
from typing import Optional
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BaselineAgent:
    """Baseline agent that uses Groq API to fix code."""

    # List of models to try in order (most capable first)
    AVAILABLE_MODELS = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma-7b-it",
    ]

    def __init__(self, model: str = None):
        """
        Initialize the baseline agent.
        
        Args:
            model: Groq model to use. If None, tries available models in order.
        """
        self.model = model
        self.api_key = os.environ.get("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set. "
                "Please set it before creating the agent."
            )
        
        # Lazy import to avoid requiring groq if not using the agent
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            
            # If no model specified, find one that works
            if self.model is None:
                self.model = self._find_working_model()
        except ImportError:
            raise ImportError(
                "groq package is required. Install it with: pip install groq"
            )

    def _find_working_model(self) -> str:
        """Find the first available model from the list."""
        try:
            available = [m.id for m in self.client.models.list().data]
            for model in self.AVAILABLE_MODELS:
                if model in available:
                    return model
            # If none of our preferred models are available, use the first available
            if available:
                return available[0]
        except Exception:
            pass
        # Fallback to first model in list
        return self.AVAILABLE_MODELS[0]

    def fix_code(self, problem_description: str, buggy_code: str, test_feedback: Optional[str] = None) -> str:
        """
        Use Groq API to generate fixed code.
        
        Args:
            problem_description: Description of what needs to be fixed
            buggy_code: The buggy code to fix
            test_feedback: Feedback from test cases (optional)
            
        Returns:
            Fixed code as a string
        """
        # Build the prompt
        prompt = self._build_prompt(problem_description, buggy_code, test_feedback)
        
        # Call Groq API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0,  # Deterministic
            max_tokens=2048,
            top_p=1.0
        )
        
        # Extract fixed code from response
        fixed_code = response.choices[0].message.content.strip()
        
        # Clean up markdown code blocks if present
        fixed_code = self._extract_code_from_response(fixed_code)
        
        return fixed_code

    def _build_prompt(self, problem_description: str, buggy_code: str, test_feedback: Optional[str] = None) -> str:
        """Build the prompt for the Groq API."""
        prompt = f"""You are an expert Python developer. Your task is to fix the buggy code.

PROBLEM:
{problem_description}

BUGGY CODE:
```python
{buggy_code}
```

"""
        
        if test_feedback:
            prompt += f"""PREVIOUS ATTEMPT FEEDBACK:
{test_feedback}

"""
        
        prompt += """INSTRUCTIONS:
1. Analyze the problem and the buggy code
2. Identify and fix the bug(s)
3. Return ONLY the complete fixed Python code without any explanation or markdown formatting
4. The function signature must remain the same
5. Do NOT include code blocks or triple backticks

Return only the Python code:"""
        
        return prompt

    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from response, removing markdown formatting if present."""
        lines = response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            code_lines.append(line)
        
        return '\n'.join(code_lines).strip()

    def fix_code_iterative(
        self, 
        problem_description: str, 
        buggy_code: str, 
        test_cases: list,
        max_iterations: int = 3
    ) -> tuple:
        """
        Iteratively fix code, using test feedback to improve.
        
        Args:
            problem_description: Description of the problem
            buggy_code: Initial buggy code
            test_cases: List of test cases
            max_iterations: Maximum iterations to try
            
        Returns:
            Tuple of (fixed_code, final_score, iteration_count)
        """
        from ..env.grader import Grader
        
        current_code = buggy_code
        grader = Grader()
        test_cases_formatted = [
            {
                "inputs": tc.inputs if isinstance(tc, dict) else tc.get("inputs", []),
                "expected_output": tc.expected_output if isinstance(tc, dict) else tc.get("expected_output"),
                "description": tc.description if isinstance(tc, dict) else tc.get("description", "")
            }
            for tc in test_cases
        ]
        
        # Extract function name
        import ast
        function_name = "solution"
        try:
            tree = ast.parse(buggy_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    function_name = node.name
                    break
        except:
            pass
        
        feedback = None
        best_score = 0.0
        best_code = buggy_code
        
        for iteration in range(max_iterations):
            # Grade current code
            result = grader.grade(current_code, function_name, test_cases_formatted)
            
            if result.final_score > best_score:
                best_score = result.final_score
                best_code = current_code
            
            # If perfect, stop
            if result.final_score >= 1.0:
                return current_code, result.final_score, iteration + 1
            
            # Build feedback from test results
            feedback_lines = []
            for test_result in result.details.get("test_results", []):
                if test_result.get("passed"):
                    feedback_lines.append(f"✓ {test_result['test']}")
                else:
                    feedback_lines.append(f"✗ {test_result['test']}: {test_result.get('error', 'Failed')}")
            
            feedback = "\n".join(feedback_lines)
            
            # Get fixed code with feedback
            current_code = self.fix_code(problem_description, current_code, feedback)
        
        return best_code, best_score, max_iterations


def create_agent(model: str = None) -> BaselineAgent:
    """Factory function to create a baseline agent.
    
    Args:
        model: Optional model name. If None, automatically selects available model.
    """
    return BaselineAgent(model=model)
