"""FastAPI server for CodeReviewEnv OpenEnv compliance."""

from fastapi import FastAPI
from typing import Dict, Any
from env.code_review_env import CodeReviewEnv

# Create FastAPI app instance
app = FastAPI(
    title="CodeReviewEnv API",
    description="OpenEnv API for AI code review and debugging",
    version="1.0.0"
)

# Global environment instance
env = CodeReviewEnv(seed=42)


def observation_to_dict(obs) -> Dict[str, Any]:
    """Convert Observation dataclass to JSON-serializable dictionary."""
    return {
        "problem_description": str(obs.problem_description),
        "buggy_code": str(obs.buggy_code),
        "test_cases": obs.test_cases,
        "attempt_count": int(obs.attempt_count),
        "best_score": float(obs.best_score),
        "previous_feedback": obs.previous_feedback
    }


def info_to_dict(info) -> Dict[str, Any]:
    """Convert Info dataclass to JSON-serializable dictionary."""
    return {
        "test_passed": int(info.test_passed),
        "test_total": int(info.test_total),
        "test_score": float(info.test_score),
        "syntax_valid": bool(info.syntax_valid),
        "code_quality": float(info.code_quality),
        "error_messages": list(info.error_messages),
        "test_details": list(info.test_details)
    }


@app.get("/")
def root():
    """Root endpoint - returns API status."""
    return {"message": "CodeReviewEnv API is running", "status": "active"}


@app.get("/health")
def health_check():
    """Health check endpoint to verify server is running."""
    return {"status": "healthy", "message": "API is operational"}


@app.post("/reset")
def reset_endpoint(data: dict = None):
    """
    Reset the environment and get initial observation.
    
    POST body: {"difficulty": "easy" | "medium" | "hard"}
    Returns: Initial observation
    """
    try:
        if data is None:
            data = {}
        
        difficulty = data.get("difficulty", "easy")
        
        # Validate difficulty
        if difficulty not in ["easy", "medium", "hard"]:
            return {"error": f"Invalid difficulty '{difficulty}'. Must be 'easy', 'medium', or 'hard'"}
        
        # Reset environment
        observation = env.reset(difficulty=difficulty)
        
        # Return as plain dict
        return {
            "problem_description": str(observation.problem_description),
            "buggy_code": str(observation.buggy_code),
            "test_cases": observation.test_cases,
            "attempt_count": int(observation.attempt_count),
            "best_score": float(observation.best_score),
            "previous_feedback": observation.previous_feedback
        }
    
    except Exception as e:
        return {"error": str(e)}


@app.post("/step")
def step_endpoint(data: dict = None):
    """
    Step the environment with the agent's fixed code.
    
    POST body: {"fixed_code": "..."}
    Returns: observation, reward, done, info
    """
    try:
        if data is None:
            data = {}
        
        fixed_code = data.get("fixed_code", "")
        
        # Check if environment is initialized
        if env.current_task is None:
            return {"error": "Environment not initialized. Call /reset first."}
        
        # Step the environment
        observation, reward, done, info = env.step(fixed_code)
        
        # Convert all to plain dicts
        observation_dict = observation_to_dict(observation)
        info_dict = info_to_dict(info)
        
        return {
            "observation": observation_dict,
            "reward": float(reward),
            "done": bool(done),
            "info": info_dict
        }
    
    except Exception as e:
        return {"error": str(e)}


@app.get("/state")
def state_endpoint():
    """
    Get the current state of the environment.
    
    Returns: Current state with attempt count, best score, rewards
    """
    try:
        state = env.state()
        
        return {
            "attempt_count": int(state["attempt_count"]),
            "best_score": float(state["best_score"]),
            "done": bool(state["done"]),
            "difficulty": state["difficulty"],
            "rewards": [float(r) for r in state["rewards"]],
            "average_reward": float(state["average_reward"])
        }
    
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
