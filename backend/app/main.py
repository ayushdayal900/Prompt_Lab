from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

from app.api.routes import router as api_router
from app.api.routes import solve_quiz, QuizRequest

app = FastAPI(title="AI Pipe Prompt Tester & Quiz Solver")

# CORS configuration
origins = [
    "http://localhost:5173",  # React frontend
    "http://localhost:3000",
    "https://prompt-lab-rouge.vercel.app",
    "https://prompt-lab-steel.vercel.app",
    "https://prompt-lab-backend.onrender.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Pipe Prompt Tester & Quiz Solver API is running"}

@app.get("/healthz")
def health_check():
    return {"status": "ok", "uptime_seconds": 3600}

app.include_router(api_router, prefix="/api")

@app.post("/solve")
async def solve_quiz_root(request: QuizRequest, background_tasks: BackgroundTasks):
    """
    Compatibility endpoint for /solve (same as /api/solve)
    """
    return await solve_quiz(request, background_tasks)
