from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from agents.planner import run_planner
from agents.researcher import run_researcher
from agents.coder import run_coder
from agents.reviewer import run_reviewer
from agents.reporter import run_reporter
from memory.shared_memory import memory
from tools.notifier import notify_run_finished
from tools.pdf_generator import generate_pdf

app = FastAPI(title="Multi-Agent AI System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    task: str
    feedback: str = ""
    image_name: str = ""


class RunRequest(BaseModel):
    task: str
    plan: str
    image_name: str = ""
    image_data: str = ""


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok", "message": "Multi-Agent API is running. Use /health or /api/plan."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/plan")
def create_plan(request: PlanRequest) -> dict[str, str]:
    try:
        past_context = memory.recall_past_runs(request.task)
        plan_text = run_planner(request.task, request.feedback, past_context, request.image_name)
        return {"plan": plan_text, "stage": "planned"}
    except Exception as e:
        # Return an error payload the frontend can display
        return {"error": str(e), "stage": "error"}


@app.post("/api/run")
def run_workflow(request: RunRequest) -> dict[str, str]:
    try:
        research_notes = run_researcher(request.task, request.plan)
        code = run_coder(request.task, request.plan, research_notes)
        review_feedback = run_reviewer(request.task, code)
        final_report = run_reporter(
            request.task,
            request.plan,
            research_notes,
            code,
            review_feedback,
        )

        memory.save_run(request.task, final_report)
        notify_run_finished(request.task, final_report)

        return {
            "research_notes": research_notes,
            "code": code,
            "review_feedback": review_feedback,
            "final_report": final_report,
            "stage": "done",
        }
    except Exception as e:
        return {"error": str(e), "stage": "error"}


@app.post("/api/report_pdf")
def report_pdf(request: dict[str, str]) -> Response:
    try:
        report_text = request.get("report", "")
        pdf_bytes = generate_pdf(report_text)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=final_report.pdf"})
    except Exception as e:
        return Response(content=str(e), status_code=500)
