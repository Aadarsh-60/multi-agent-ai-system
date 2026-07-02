# Multi-Agent AI System

A modern multi-agent application that turns a user request into a structured plan, gets human approval, and then runs specialized agents for research, coding, review, and reporting. The app is designed for a polished web experience with streaming outputs, dark UI styling, human-in-the-loop control, and PDF export.

## Tech Stack

- Python
- FastAPI
- LangGraph
- LangChain
- Google Gemini / LLM integration
- Tavily Search
- React
- Vite
- FPDF2

## Key Features

- Human approval before execution
- Planner → Research → Coding → Review → Report agent flow
- Dark, modern frontend UI
- Structured and streaming output rendering
- Optional image attachment for task context
- Final report download as text or PDF

## Project Structure

```text
multi-agent-ai-system/
├── agents/              # Planner, researcher, coder, reviewer, reporter
├── tools/               # LLM, search, notifier, PDF generation helpers
├── memory/              # Shared memory layer
├── workflows/           # Graph orchestration and human-loop logic
├── api.py               # FastAPI backend
├── frontend/            # React + Vite frontend
├── main.py              # Terminal entry point
├── requirements.txt
└── .env
```

## Setup Locally

1. Create and activate a Python environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:

```bash
cd frontend
npm install
```

4. Add your API keys to a `.env` file:

```env
GEMINI_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

## Run Locally

Start the backend:

```bash
source .venv/bin/activate
uvicorn api:app --host 127.0.0.1 --port 8000
```

Start the frontend:

```bash
cd frontend
npm run dev
```

Open: http://127.0.0.1:5173

## Deployment

To deploy this project:

1. Host the FastAPI backend on a cloud service such as Render, Railway, Fly.io, or Azure.
2. Build and deploy the React frontend on Vercel, Netlify, or any static hosting provider.
3. Update the frontend API base URL to point to the deployed backend.
4. Set environment variables such as `GEMINI_API_KEY` and `TAVILY_API_KEY` in the deployment platform.
5. Ensure CORS is enabled for your frontend domain.

## Example Flow

1. User enters a task.
2. Planner generates a step-by-step plan.
3. Human approves or revises the plan.
4. Research, coding, review, and reporting agents produce structured output.
5. Final report can be downloaded as text or PDF.
