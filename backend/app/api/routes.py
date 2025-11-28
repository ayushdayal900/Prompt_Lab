from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Optional, Dict, Any
import os
from app.services.prompt_tester import PromptTester
from app.services.solver import QuizSolver

router = APIRouter()

# --- Pydantic Models ---

class PromptTestRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    model: str = "gpt-4o-mini" # Default model
    secret: Optional[str] = None # Optional custom secret
    api_token: Optional[str] = None # Optional API token

class PromptTestResponse(BaseModel):
    system_prompt: str
    user_prompt: str
    secret: str
    llm_output: str
    leak_detected: bool
    score_system: int
    score_user: int

class QuizRequest(BaseModel):
    email: EmailStr
    secret: str
    url: HttpUrl
    api_token: Optional[str] = None

class QuizResponse(BaseModel):
    message: str
    status: str

# --- Endpoints ---

@router.get("/healthz")
def health_check():
    return {"status": "ok", "source": "routes.py"}

@router.post("/test-prompt", response_model=PromptTestResponse)
async def test_prompt(request: PromptTestRequest):
    """
    Tests a system prompt against a user prompt to see if the secret leaks.
    """
    tester = PromptTester()
    result = await tester.run_test(
        system_prompt=request.system_prompt,
        user_prompt=request.user_prompt,
        model=request.model,
        secret=request.secret,
        api_token=request.api_token or os.getenv("API_KEY")
    )
    return result

@router.post("/solve")
async def solve_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    """
    Receives a quiz task and starts the solver in the background.
    """
    # Verify secret (simple check for now, can be expanded)
    if not request.secret:
         raise HTTPException(status_code=403, detail="Invalid secret")

    solver = QuizSolver()
    
    # Run the solver in the background to avoid blocking
    background_tasks.add_task(
        solver.solve_and_submit,
        email=request.email,
        secret=request.secret,
        start_url=str(request.url),
        api_token=request.api_token or os.getenv("API_KEY")
    )

    return {"message": "Solver started", "status": "processing"}
