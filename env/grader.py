"""Grader for evaluating code submissions and computing rewards."""

import ast
import re
import sys
from io import StringIO
from typing import Dict, Any, Tuple, List, Optional
from dataclasses import dataclass
import traceback


@dataclass
class GradeResult:
    """Result of grading a code submission."""
    passed_tests: int
    total_tests: int
    test_case_score: float  # 0.0-1.0
    syntax_score: float  # 0.0 or 1.0
    quality_score: float  # 0.0-1.0
    final_score: float  # 0.0-1.0
    errors: List[str]
    details: Dict[str, Any]


class Grader:
    """Evaluates code submissions for correctness and quality."""

    def __init__(self):
        """Initialize the grader."""
        pass

    def check_syntax(self, code: str) -> Tuple[bool, str]:
        """Check if code is syntactically valid."""
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error: {e.msg} at line {e.lineno}"
        except Exception as e:
            return False, f"Parse error: {str(e)}"

    def extract_function(self, code: str, function_name: str) -> Optional[str]:
        """Extract function from code block."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    return code
            return None
        except:
            return None

    def run_test_case(self, code: str, function_name: str, inputs: List[Any], expected: Any) -> Tuple[bool, str]:
        """Run a single test case and return pass/fail."""
        try:
            # Create a safe namespace
            namespace = {}
            exec(code, namespace)

            if function_name not in namespace:
                return False, f"Function '{function_name}' not found in code"

            func = namespace[function_name]

            # Run with timeout protection (simulate with try-except for now)
            if isinstance(inputs, list):
                result = func(*inputs)
            else:
                result = func(inputs)

            if result == expected:
                return True, ""
            else:
                return False, f"Expected {expected}, got {result}"

        except RecursionError:
            return False, "RecursionError: Stack overflow (inefficient algorithm)"
        except TimeoutError:
            return False, "TimeoutError: Execution took too long"
        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 100:
                error_msg = error_msg[:100] + "..."
            return False, f"Runtime error: {error_msg}"

    def assess_code_quality(self, code: str) -> float:
        """Assess code quality heuristically (0.0-1.0)."""
        score = 1.0
        penalties = []

        # Detect overly complex patterns
        if "while True" in code and code.count("break") == 0:
            score -= 0.1
            penalties.append("Infinite loop detected")

        # Check for recursion (not always bad, but warn if excessive)
        if code.count("return ") > 3 and code.count("def ") == 1:
            if code.count("(n - 1)") > 0 or code.count("(n-1)") > 0:
                # Recursive call - check if memoization is used
                if "memo" not in code and "cache" not in code:
                    # Basic recursion without memoization might be suboptimal
                    # But we don't penalize too much as some solutions might use it
                    pass

        # Check for reasonable variable names
        bad_names = re.findall(r'\b[a-z]{1}\b(?!=")', code)  # Single letter vars (excluding assignments)
        if len(bad_names) > 5:
            score -= 0.05
            penalties.append("Too many single-letter variables")

        # Check if code is too long (potential inefficiency)
        lines = code.strip().split('\n')
        if len(lines) > 50:
            score -= 0.05
            penalties.append("Code is quite long")

        return max(0.0, min(1.0, score))

    def grade(self, code: str, function_name: str, test_cases: List[Dict], timeout_sec: float = 5.0) -> GradeResult:
        """Grade a code submission against test cases."""
        errors = []
        details = {
            "test_results": [],
            "quality_notes": []
        }

        # Step 1: Check syntax
        is_valid, syntax_error = self.check_syntax(code)
        if not is_valid:
            errors.append(syntax_error)
            return GradeResult(
                passed_tests=0,
                total_tests=len(test_cases),
                test_case_score=0.0,
                syntax_score=0.0,
                quality_score=0.0,
                final_score=0.0,
                errors=errors,
                details=details
            )
        syntax_score = 1.0

        # Step 2: Run test cases
        passed = 0
        timeouts = 0
        runtime_errors = 0

        for i, test_case in enumerate(test_cases):
            inputs = test_case.get("inputs", [])
            expected = test_case.get("expected_output")
            description = test_case.get("description", f"Test {i+1}")

            passed_test, error_msg = self.run_test_case(code, function_name, inputs, expected)

            if passed_test:
                passed += 1
                details["test_results"].append({
                    "test": description,
                    "passed": True
                })
            else:
                if "Stack overflow" in error_msg or "took too long" in error_msg:
                    timeouts += 1
                elif "Runtime error" in error_msg or "not found" in error_msg:
                    runtime_errors += 1

                details["test_results"].append({
                    "test": description,
                    "passed": False,
                    "error": error_msg
                })

        # Step 3: Calculate test case score (partial credit)
        test_case_score = passed / len(test_cases) if test_cases else 0.0

        # Step 4: Assess code quality
        quality_score = self.assess_code_quality(code)
        if runtime_errors > 0:
            quality_score = max(0.0, quality_score - 0.3)

        # Step 5: Calculate final score
        # CRITICAL: If all tests pass, score is 1.0 (perfect solution)
        if passed == len(test_cases) and syntax_score == 1.0:
            final_score = 1.0
        else:
            # Components: 60% test cases, 20% syntax, 20% quality
            final_score = (
                test_case_score * 0.6 +
                syntax_score * 0.2 +
                quality_score * 0.2
            )

            # Apply penalties for significant issues
            if timeouts > 0:
                final_score -= 0.1 * min(1, timeouts / len(test_cases))

            # Clamp to [0.0, 1.0]
            final_score = max(0.0, min(1.0, final_score))

        return GradeResult(
            passed_tests=passed,
            total_tests=len(test_cases),
            test_case_score=test_case_score,
            syntax_score=syntax_score,
            quality_score=quality_score,
            final_score=final_score,
            errors=errors,
            details=details
        )
