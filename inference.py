"""FastAPI server for CodeReviewEnv inference and interaction."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from env.code_review_env import CodeReviewEnv

# ============================================================================
# Pydantic Models for request/response validation
# ============================================================================

class ResetRequest(BaseModel):
    """Request model for /reset endpoint."""
    difficulty: str = "easy"


class StepRequest(BaseModel):
    """Request model for /step endpoint."""
    fixed_code: str


class ResetResponse(BaseModel):
    """Response model for /reset endpoint."""
    problem_description: str
    buggy_code: str
    test_cases: List[Dict[str, Any]]
    attempt_count: int
    best_score: float
    previous_feedback: Optional[str] = None


class StepResponse(BaseModel):
    """Response model for /step endpoint."""
    observation: Dict[str, Any]
    reward: float
    done: bool
    info: Dict[str, Any]


class StateResponse(BaseModel):
    """Response model for /state endpoint."""
    attempt_count: int
    best_score: float
    done: bool
    difficulty: Optional[str]
    rewards: List[float]
    average_reward: float


# ============================================================================
# FastAPI Application
# ============================================================================

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
        "problem_description": obs.problem_description,
        "buggy_code": obs.buggy_code,
        "test_cases": obs.test_cases,
        "attempt_count": obs.attempt_count,
        "best_score": obs.best_score,
        "previous_feedback": obs.previous_feedback
    }


def info_to_dict(info) -> Dict[str, Any]:
    """Convert Info dataclass to JSON-serializable dictionary."""
    return {
        "test_passed": info.test_passed,
        "test_total": info.test_total,
        "test_score": float(info.test_score),
        "syntax_valid": info.syntax_valid,
        "code_quality": float(info.code_quality),
        "error_messages": info.error_messages,
        "test_details": info.test_details
    }


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/reset", response_model=ResetResponse)
async def reset_endpoint(request: ResetRequest):
    """
    Reset the environment and get initial observation.
    
    Args:
        request: ResetRequest with difficulty level
        
    Returns:
        Initial observation with problem description, buggy code, test cases
    """
    # Validate difficulty
    if request.difficulty not in ["easy", "medium", "hard"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid difficulty. Must be 'easy', 'medium', or 'hard', got '{request.difficulty}'"
        )
    
    try:
        # Reset environment
        observation = env.reset(difficulty=request.difficulty)
        
        # Convert to JSON-serializable dict
        return ResetResponse(
            problem_description=observation.problem_description,
            buggy_code=observation.buggy_code,
            test_cases=observation.test_cases,
            attempt_count=observation.attempt_count,
            best_score=observation.best_score,
            previous_feedback=observation.previous_feedback
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in /reset: {str(e)}"
        )


@app.post("/step", response_model=StepResponse)
async def step_endpoint(request: StepRequest):
    """
    Step the environment with the agent's fixed code.
    
    Args:
        request: StepRequest with fixed code
        
    Returns:
        Tuple of (observation, reward, done, info) as JSON
    """
    try:
        # Check if environment is initialized
        if env.current_task is None:
            raise HTTPException(
                status_code=400,
                detail="Environment not initialized. Call /reset first."
            )
        
        # Step the environment
        observation, reward, done, info = env.step(request.fixed_code)
        
        # Convert all to JSON-serializable dicts
        observation_dict = observation_to_dict(observation)
        info_dict = info_to_dict(info)
        
        return StepResponse(
            observation=observation_dict,
            reward=float(reward),
            done=done,
            info=info_dict
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in /step: {str(e)}"
        )


@app.get("/state", response_model=StateResponse)
async def state_endpoint():
    """
    Get the current state of the environment.
    
    Returns:
        Current state with attempt count, best score, done status, and rewards
    """
    try:
        state = env.state()
        
        return StateResponse(
            attempt_count=state["attempt_count"],
            best_score=float(state["best_score"]),
            done=state["done"],
            difficulty=state["difficulty"],
            rewards=[float(r) for r in state["rewards"]],
            average_reward=float(state["average_reward"])
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in /state: {str(e)}"
        )


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint to verify server is running."""
    return {
        "status": "healthy",
        "message": "CodeReviewEnv API is running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
