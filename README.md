---
title: LLM Analysis Quiz Solver
emoji: 🏃
colorFrom: red
colorTo: blue
sdk: docker
pinned: false
app_port: 8000
---

# LLM Analysis - Autonomous Quiz Solver Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121.3+-green.svg)](https://fastapi.tiangolo.com/)

An intelligent, autonomous agent built with **Playwright** and **OpenAI/OpenRouter** that solves data-related quizzes involving web scraping, data processing, analysis, and visualization tasks. The system uses **GPT-4o Mini** (or similar models) to orchestrate tool usage and make decisions.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Tools & Capabilities](#tools--capabilities)
- [Docker Deployment](#docker-deployment)
- [How It Works](#how-it-works)
- [License](#license)

## 🔍 Overview

This project was developed for the TDS (Tools in Data Science) course project, where the objective is to build an application that can autonomously solve multi-step quiz tasks involving:

- **Data sourcing**: Scraping websites, calling APIs, downloading files
- **Data preparation**: Cleaning text, PDFs, and various data formats
- **Data analysis**: Filtering, aggregating, statistical analysis, ML models
- **Data visualization**: Generating charts, narratives, and presentations

The system receives quiz URLs via a REST API, navigates through multiple quiz pages, solves each task using LLM-powered reasoning and specialized tools, and submits answers back to the evaluation server.

## 🏗️ Architecture

The project uses a **FastAPI + React** architecture with the following components:

```
┌─────────────┐
│   FastAPI   │  ← Receives POST requests with quiz URLs
│   Server    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Solver    │  ← Playwright + AsyncOpenAI (LLM)
│   Service   │
└──────┬──────┘
       │
       ├────────────┬────────────┐
       ▼            ▼            ▼
   [Browser]    [LLM Analysis] [Submission]
```

### Key Components:

1. **FastAPI Server** (`backend/app/main.py`): Handles incoming POST requests, validates secrets, and triggers the agent.
2. **Quiz Solver** (`backend/app/services/solver.py`): Intelligent agent that uses Playwright to browse and LLMs to solve.
3. **Prompt Tester** (`backend/app/services/prompt_tester.py`): Tool for testing system prompt robustness.
4. **Frontend** (`frontend/`): React-based UI for manual testing and visualization.

## ✨ Features

- ✅ **Autonomous multi-step problem solving**: Chains together multiple quiz pages
- ✅ **Dynamic JavaScript rendering**: Uses Playwright for client-side rendered pages
- ✅ **LLM-Powered Analysis**: Uses GPT-4o Mini to understand page content and extract answers
- ✅ **Prompt Injection Testing**: Dedicated module for testing LLM security
- ✅ **Robust error handling**: Retries failed attempts within time limits
- ✅ **Rate limiting**: Respects API quotas

## 📁 Project Structure

```
LLM_Analysis/
├── backend/
│   ├── app/
│   │   ├── api/routes.py       # API Endpoints
│   │   ├── services/
│   │   │   ├── solver.py       # Quiz Solver Logic
│   │   │   └── prompt_tester.py # Prompt Testing Logic
│   │   └── main.py             # FastAPI Entry Point
│   └── requirements.txt        # Python Dependencies
├── frontend/                   # React Frontend
│   ├── src/
│   └── package.json
└── README.md
```

## 📦 Installation

### Prerequisites

- Python 3.12 or higher
- Node.js & npm (for frontend)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/LLM_Analysis.git
cd LLM_Analysis
```

### Step 2: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

### Step 3: Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

## ⚙️ Configuration

### Environment Variables

You can create a `.env` file in `backend/` or pass credentials directly via the API.

Required keys for operation:
- `OPENROUTER_API_KEY` (or OpenAI API Key)

## 🚀 Usage

### Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```
Server starts at `http://localhost:8000`.

### Start the Frontend

```bash
cd frontend
npm run dev
```
UI starts at `http://localhost:5173`.

### Testing the Endpoint

Send a POST request to test your setup:

```bash
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your.email@example.com",
    "secret": "your_secret_string",
    "url": "https://tds-llm-analysis.s-anand.net/demo",
    "api_token": "sk-..."
  }'
```

Expected response:

```json
{
  "message": "Solver started",
  "status": "processing"
}
```

## 🌐 API Endpoints

### `POST /solve`

Receives quiz tasks and triggers the autonomous agent.

**Request Body:**

```json
{
  "email": "your.email@example.com",
  "secret": "your_secret_string",
  "url": "https://example.com/quiz-123",
  "api_token": "sk-..."
}
```

**Responses:**

| Status Code | Description                    |
| ----------- | ------------------------------ |
| `200`     | Solver started successfully    |
| `403`     | Invalid secret                 |

### `GET /healthz`

Health check endpoint for monitoring.

**Response:**

```json
{
  "status": "ok",
  "uptime_seconds": 3600
}
```

## 🛠️ Tools & Capabilities

The agent has access to the following tools:

### 1. **Web Scraper** (Playwright)

- Uses Playwright to render JavaScript-heavy pages
- Waits for network idle before extracting content
- Returns fully rendered HTML/Text for parsing

### 2. **LLM Analysis** (AsyncOpenAI)

- Analyzes page content to find answers
- Determines the submission URL dynamically
- Handles complex reasoning tasks

### 3. **Submission Handler**

- Sends JSON payloads to submission endpoints
- Handles response parsing and chaining to the next URL

## 🐳 Docker Deployment

### Build the Image

```bash
docker build -t llm-analysis-agent .
```

### Run the Container

```bash
docker run -p 8000:8000 llm-analysis-agent
```

## 🧠 How It Works

### 1. Request Reception

- FastAPI receives a POST request with quiz URL
- Validates the secret
- Starts the `QuizSolver` in the background

### 2. Solver Loop

```
┌─────────────────────────────────────────┐
│ 1. Navigate to URL (Playwright)         │
│    - Render page                        │
│    - Extract text & links               │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│ 2. LLM Analysis                         │
│    - "What is the answer?"              │
│    - "Where do I submit it?"            │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│ 3. Submission                           │
│    - POST answer to submit URL          │
│    - Get result (Correct/Incorrect)     │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│ 4. Decision                             │
│    - If Correct & New URL: Loop to 1    │
│    - If Done/Fail: Stop                 │
└─────────────────────────────────────────┘
```

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
