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

app = FastAPI(title="LLM Analysis Quiz Solver")

@app.on_event("startup")
async def startup_event():
    secret = os.getenv("MY_SECRET")
    if not secret:
        print("WARNING: MY_SECRET environment variable is not set!")

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
