from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
import os
import time
from dotenv import load_dotenv
from app.models import QuizRequest, QuizResponse
from app.solver import Solver

load_dotenv()

import logging
import sys

# Configure logging to show up in the terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

from fastapi.middleware.cors import CORSMiddleware
from app.models import QuizRequest, QuizResponse, PromptTestRequest, PromptTestResponse
from app.llm import ask_llm

app = FastAPI(title="LLM Analysis Quiz Solver")

# Add CORS Middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev/demo purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    secret = os.getenv("MY_SECRET")
    if not secret:
        print("WARNING: MY_SECRET environment variable is not set!")

@app.post("/api/test-prompt", response_model=PromptTestResponse)
async def test_prompt_endpoint(request: PromptTestRequest):
    # Call LLM with user provided parameters
    try:
        response_text = await ask_llm(
            prompt=request.user_prompt,
            system_prompt=request.system_prompt,
            api_key=request.api_token,
            model=request.model
        )
        
        # Check if secret was leaked (Case insensitive check)
        leak_detected = request.secret.lower() in response_text.lower()
        
        return PromptTestResponse(
            leak_detected=leak_detected,
            llm_output=response_text
        )
    except Exception as e:
        print(f"Error in test-prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/project2", response_model=QuizResponse)
async def solve_quiz_endpoint(
    request: QuizRequest, 
    background_tasks: BackgroundTasks
):
    # Secret Verification (Constant-time comparison ideally, but simple string compare for now per requirements)
    server_secret = os.getenv("MY_SECRET")
    if not server_secret or request.secret != server_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    # Deadline calculation (Now + 3 minutes)
    deadline = time.time() + 180

    # Initialize Solver
    solver = Solver(
        email=request.email,
        secret=request.secret,
        api_token=os.getenv("OPENAI_API_KEY") 
    )

    # Run in background
    background_tasks.add_task(
        solver.solve,
        start_url=str(request.url),
        deadline=deadline
    )

    return {"status": "received", "message": "Solver started in background."}

# Health check
@app.get("/healthz")
def health():
    return {"status": "ok"}
