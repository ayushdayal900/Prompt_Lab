# LLM Analysis Quiz Solver

This project is an automated quiz solver that uses an LLM (Large Language Model) to analyze web pages, answer questions, and perform data science tasks autonomously.

## Features
- **FastAPI Backend**: Exposes a secure `/project2` endpoint.
- **Autonomous Agent**: Propelled by `gpt-4o-mini` (or other LLMs via OpenRouter).
- **Headless Browser**: Uses Playwright to navigate and interact with quizzes.
- **Tool Use**: Capable of executing Python code, downloading files, and performing OCR.
- **Deadline Management**: Adheres to a strict 3-minute solving window.

## Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/your-repo/project.git
    cd project
    ```

2.  **Install Dependencies**
    ```bash
    cd backend
    pip install -r requirements.txt
    playwright install chromium
    ```

3.  **Environment Variables**
    Create a `.env` file in the `backend` directory:
    ```env
    MY_SECRET=your_secure_secret_value
    OPENAI_API_KEY=sk-or-...
    LLM_PROVIDER=openai
    ```

## Usage

1.  **Start the Server**
    ```bash
    cd backend
    uvicorn app.main:app --reload
    ```
    *Server runs at `http://localhost:8000`*

2.  **Trigger the Solver**
    Send a POST request to `/project2`:
    ```bash
    curl -X POST "http://localhost:8000/project2" \
         -H "Content-Type: application/json" \
         -d '{
               "email": "student@example.com",
               "secret": "your_secure_secret_value",
               "url": "https://quiz-site.com/start"
             }'
    ```

## Architecture
- **`app/main.py`**: Entry point, endpoint definition.
- **`app/solver.py`**: Core logic loop, manages the deadline and agent cycle.
- **`app/llm.py`**: Interface for LLM communication.
- **`app/prowser.py`**: Wrapper for Playwright interactions.
- **`app/utils.py`**: Helper tools for file downloading and code execution.
