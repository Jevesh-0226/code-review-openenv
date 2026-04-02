"""Evaluation script for CodeReviewEnv - tests all difficulty levels."""

import json
import sys
import time
from typing import Dict, List, Any
from http.server import SimpleHTTPRequestHandler, HTTPServer

from env.code_review_env import create_env
from env.tasks import get_all_tasks
from agent.baseline_agent import create_agent


class Evaluator:
    """Evaluates agent performance across all tasks."""

    def __init__(self, use_agent: bool = True):
        """
        Initialize evaluator.
        
        Args:
            use_agent: Whether to use baseline agent (requires GROQ_API_KEY)
        """
        self.use_agent = use_agent
        if use_agent:
            try:
                self.agent = create_agent()
            except ValueError as e:
                print(f"Warning: {e}")
                self.use_agent = False
                self.agent = None
        else:
            self.agent = None
        
        self.results = {
            "summary": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "total_score": 0.0,
                "average_score": 0.0,
            },
            "tasks": []
        }

    def evaluate_task(self, difficulty: str, task_id: int = 1) -> Dict[str, Any]:
        """
        Evaluate a single task.
        
        Args:
            difficulty: Task difficulty level
            task_id: Task identifier for reporting
            
        Returns:
            Dict with evaluation results
        """
        print(f"\n{'='*70}")
        print(f"Task {task_id}: {difficulty.upper()}")
        print(f"{'='*70}")
        
        # Reset environment
        env = create_env()
        observation = env.reset(difficulty=difficulty)
        
        task_info = env.get_task_info()
        print(f"Problem: {task_info.get('name', 'N/A')}")
        print(f"Points: {task_info.get('points', 0)}")
        print(f"\nDescription:")
        print(observation.problem_description)
        print(f"\nBuggy Code:")
        print(observation.buggy_code)
        
        result = {
            "task_id": task_id,
            "difficulty": difficulty,
            "name": task_info.get('name'),
            "points": task_info.get('points'),
            "status": "failed",
            "attempts": 0,
            "final_score": 0.0,
            "attempts_log": []
        }
        
        if not self.use_agent or not self.agent:
            print("\n[No agent available - skipping execution]")
            return result
        
        try:
            # Use agent to fix code
            print("\n[Agent attempting fix...]")
            start_time = time.time()
            
            fixed_code = self.agent.fix_code(
                observation.problem_description,
                observation.buggy_code,
                None
            )
            
            elapsed_time = time.time() - start_time
            print(f"[Agent response time: {elapsed_time:.2f}s]")
            
            # Step through environment
            state = env.state()
            obs, reward, done, info = env.step(fixed_code)
            
            result["attempts"] = 1
            result["final_score"] = reward
            result["status"] = "success" if reward >= 0.8 else "partial"
            result["attempts_log"].append({
                "attempt": 1,
                "reward": reward,
                "tests_passed": info.test_passed,
                "tests_total": info.test_total,
                "syntax_valid": info.syntax_valid,
                "code_quality": info.code_quality,
            })
            
            print(f"\nResults:")
            print(f"  Tests passed: {info.test_passed}/{info.test_total}")
            print(f"  Test score: {info.test_score:.2%}")
            print(f"  Syntax valid: {info.syntax_valid}")
            print(f"  Code quality: {info.code_quality:.2f}")
            print(f"  *** FINAL REWARD: {reward:.4f} ***")
            
            if info.test_details:
                print(f"\nTest Details:")
                for detail in info.test_details:
                    status = "[PASS]" if detail.get("passed") else "[FAIL]"
                    print(f"  {status} {detail.get('test')}")
                    if not detail.get("passed"):
                        print(f"    Error: {detail.get('error')}")
            
            # If not perfect, try iterative improvement
            if reward < 1.0 and self.agent:
                print("\n[Attempting iterative improvement...]")
                attempts_left = 4
                while attempts_left > 0 and obs and not done:
                    # Get feedback and try again
                    feedback = "\n".join([
                        f"{'✓' if d.get('passed') else '✗'} {d['test']}: {d.get('error', '')}"
                        for d in info.test_details
                    ])
                    
                    fixed_code = self.agent.fix_code(
                        observation.problem_description,
                        fixed_code,  # Use previous attempt as base
                        feedback
                    )
                    
                    obs, reward, done, info = env.step(fixed_code)
                    result["attempts"] += 1
                    result["final_score"] = reward
                    result["status"] = "success" if reward >= 0.8 else "partial"
                    result["attempts_log"].append({
                        "attempt": result["attempts"],
                        "reward": reward,
                        "tests_passed": info.test_passed,
                        "tests_total": info.test_total,
                        "syntax_valid": info.syntax_valid,
                        "code_quality": info.code_quality,
                    })
                    
                    print(f"  Attempt {result['attempts']}: score={reward:.4f}, tests={info.test_passed}/{info.test_total}")
                    
                    if done or reward >= 1.0:
                        break
                    
                    attempts_left -= 1
        
        except Exception as e:
            print(f"\nError during evaluation: {str(e)}")
            import traceback
            traceback.print_exc()
            result["status"] = "error"
            result["error"] = str(e)
        
        return result

    def run_all_tasks(self) -> Dict[str, Any]:
        """Run evaluation on all tasks."""
        print("Starting CodeReviewEnv Evaluation")
        print("=" * 70)
        
        tasks = get_all_tasks()
        task_id = 1
        
        for task in tasks:
            result = self.evaluate_task(task.difficulty, task_id)
            self.results["tasks"].append(result)
            task_id += 1
        
        # Calculate summary
        self._calculate_summary()
        
        return self.results

    def _calculate_summary(self):
        """Calculate summary statistics."""
        if not self.results["tasks"]:
            return
        
        total_tasks = len(self.results["tasks"])
        completed = sum(1 for t in self.results["tasks"] if t["status"] in ["success", "partial"])
        total_score = sum(t["final_score"] for t in self.results["tasks"])
        
        self.results["summary"]["total_tasks"] = total_tasks
        self.results["summary"]["completed_tasks"] = completed
        self.results["summary"]["total_score"] = total_score
        self.results["summary"]["average_score"] = total_score / total_tasks if total_tasks > 0 else 0.0

    def print_summary(self):
        """Print summary report."""
        print("\n" + "=" * 70)
        print("FINAL EVALUATION SUMMARY")
        print("=" * 70)
        
        summary = self.results["summary"]
        print(f"\nTotal Tasks: {summary['total_tasks']}")
        print(f"Completed: {summary['completed_tasks']}/{summary['total_tasks']}")
        print(f"Total Score: {summary['total_score']:.4f}")
        print(f"Average Score: {summary['average_score']:.4f}")
        
        print(f"\nPer-Task Breakdown:")
        for task in self.results["tasks"]:
            status_icon = "OK" if task["final_score"] >= 0.95 else "WK" if task["final_score"] >= 0.7 else "NO"
            print(f"  {status_icon} {task['difficulty'].upper():6s} | Score: {task['final_score']:.4f} | {task['name']:20s} | Attempts: {task['attempts']}")

    def save_results(self, filename: str = "evaluation_results.json"):
        """Save results to JSON file."""
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\nResults saved to {filename}")


def main():
    """Main evaluation script."""
    import os
    
    # Check for GROQ API key
    use_agent = "GROQ_API_KEY" in os.environ
    
    if not use_agent:
        print("Warning: GROQ_API_KEY not set. Running in evaluation mode without agent.")
        print("Set GROQ_API_KEY environment variable to enable agent-based fixing.")
    
    # Run evaluation
    evaluator = Evaluator(use_agent=use_agent)
    results = evaluator.run_all_tasks()
    
    # Print and save results
    evaluator.print_summary()
    evaluator.save_results()
    
    return results


def run_server():
    """Start a minimal HTTP server for Hugging Face Spaces."""
    port = 7860
    print(f"\nStarting server at http://0.0.0.0:{port}")
    
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    results = main()
    
    print("\n" + "=" * 70)
    print("Evaluation completed successfully!")
    print("Launching minimal server for Hugging Face Spaces...")
    print("=" * 70)
    
    run_server()
