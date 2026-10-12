"""
graph/nodes.py

Node implementations matching the 10-step AgentMind workflow:
  - planner_node (creates plan and assesses research need)
  - researcher_node (gathers findings and source links)
  - coder_node (generates executable Python code)
  - execution_sandbox_node (Step 6: executes and validates in sandbox)
  - reviewer_node (evaluates code + execution results with 3-way decision)
  - reporter_node (compiles final report, saves memory, sends alerts)
"""

from typing import Dict, Any, Optional
from langchain_core.runnables import RunnableConfig

from agents.planner import run_planner, check_research_needed
from agents.researcher import run_researcher
from agents.coder import run_coder
from agents.reviewer import run_reviewer, parse_review_decision
from agents.reporter import run_reporter
from tools.sandbox import run_code_in_sandbox
from memory.shared_memory import memory
from tools.monitor import monitor


def _collect_stream(generator, callback=None) -> str:
    """Helper to consume a generator stream and invoke callback per token if present."""
    chunks = []
    for chunk in generator:
        if callback:
            callback(chunk)
        chunks.append(chunk)
    return "".join(chunks)


def planner_node(state: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Step 2: Planner Agent - Breaks task into steps and determines if research is needed."""
    monitor.start_span("planner")
    callback = (config or {}).get("callbacks_dict", {}).get("planner")
    task = state.get("task", "")
    feedback = state.get("feedback", "")
    past_context = state.get("past_context", "")
    image_name = state.get("image_name", "")

    try:
        stream = run_planner(
            task=task,
            feedback=feedback,
            past_context=past_context,
            image_name=image_name,
            config=config
        )
        plan_text = _collect_stream(stream, callback=callback)
        research_needed = check_research_needed(plan_text, task)
        monitor.end_span("planner", input_text=f"{task} {feedback}", output_text=plan_text)

        return {
            "plan": plan_text,
            "research_needed": research_needed,
            "status": "plan_generated"
        }
    except Exception as e:
        monitor.end_span("planner", input_text=task, error=str(e))
        raise


def researcher_node(state: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Step 4A: Researcher Agent - Collects relevant info and source citations."""
    monitor.start_span("researcher")
    callback = (config or {}).get("callbacks_dict", {}).get("researcher")
    task = state.get("task", "")
    plan = state.get("plan", "")
    research_feedback = state.get("research_feedback", "")

    try:
        stream = run_researcher(
            task=task,
            plan=plan,
            research_feedback=research_feedback,
            config=config
        )
        notes_text = _collect_stream(stream, callback=callback)
        monitor.end_span("researcher", input_text=f"{task} {plan}", output_text=notes_text)

        return {
            "research_notes": notes_text,
            "status": "research_completed"
        }
    except Exception as e:
        monitor.end_span("researcher", input_text=task, error=str(e))
        raise


def coder_node(state: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Step 5: Coder Agent - Writes code using plan, research findings, and execution errors."""
    monitor.start_span("coder")
    callback = (config or {}).get("callbacks_dict", {}).get("coder")
    task = state.get("task", "")
    plan = state.get("plan", "")
    research_notes = (state.get("research_notes", "") or "")[:6000]

    # Combine review feedback and sandbox errors for self-correction loops
    iteration = state.get("iteration_count", 0)
    review_feedback = state.get("review_feedback", "")
    execution_output = state.get("execution_output", "")

    execution_feedback = ""
    if iteration > 0 and (review_feedback or execution_output):
        execution_feedback = (
            f"Review Critique:\n{review_feedback[:2500]}\n\n"
            f"Sandbox Output/Errors:\n{execution_output[:2500]}"
        )

    try:
        stream = run_coder(
            task=task,
            plan=plan,
            research_notes=research_notes,
            execution_feedback=execution_feedback,
            config=config
        )
        code_text = _collect_stream(stream, callback=callback)
        monitor.end_span("coder", input_text=f"{task} {plan} {execution_feedback}", output_text=code_text)

        return {
            "code": code_text,
            "status": "code_generated"
        }
    except Exception as e:
        monitor.end_span("coder", input_text=task, error=str(e))
        raise


def execution_sandbox_node(state: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Step 6: Execution & Validation (Sandbox) - Safely runs code and captures stdout/stderr."""
    monitor.start_span("sandbox")
    code = state.get("code", "")
    sandbox_res = run_code_in_sandbox(code, timeout_seconds=15)

    stdout_txt = sandbox_res.get("stdout", "")
    stderr_txt = sandbox_res.get("stderr", "")
    summary_txt = sandbox_res.get("summary", "")

    formatted_output = (
        f"Result: {summary_txt}\n"
        f"Exit Code: {sandbox_res.get('exit_code', -1)}\n"
        f"--- STDOUT ---\n{stdout_txt if stdout_txt else '(empty)'}\n"
        f"--- STDERR ---\n{stderr_txt if stderr_txt else '(empty)'}"
    )

    err_flag = None if sandbox_res.get("success") else summary_txt
    monitor.end_span("sandbox", input_text=code, output_text=formatted_output, error=err_flag)

    return {
        "execution_output": formatted_output,
        "execution_success": sandbox_res.get("success", False),
        "execution_stderr": stderr_txt,
        "status": "validated"
    }


def reviewer_node(state: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Step 7: Reviewer Agent - Validates correctness, quality, and sandbox result."""
    monitor.start_span("reviewer")
    callback = (config or {}).get("callbacks_dict", {}).get("reviewer")
    task = state.get("task", "")
    plan = state.get("plan", "")
    code = (state.get("code", "") or "")[:6000]
    execution_output = state.get("execution_output", "")

    try:
        stream = run_reviewer(
            task=task,
            code=code,
            execution_results=execution_output,
            plan=plan,
            config=config
        )
        review_text = _collect_stream(stream, callback=callback)

        decision = parse_review_decision(review_text)
        curr_iteration = state.get("iteration_count", 0)

        # If more research needed, extract research note
        research_feedback = ""
        if decision == "more_research_needed":
            research_feedback = f"Reviewer requested more info:\n{review_text[:1500]}"

        monitor.end_span("reviewer", input_text=f"{code} {execution_output}", output_text=review_text)

        return {
            "review_feedback": review_text,
            "review_decision": decision,
            "research_feedback": research_feedback,
            "iteration_count": curr_iteration + 1,
            "status": "review_completed"
        }
    except Exception as e:
        monitor.end_span("reviewer", input_text=task, error=str(e))
        raise


def reporter_node(state: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Step 9: Reporter Agent - Creates final answer with explanations, code, and findings."""
    monitor.start_span("reporter")
    callback = (config or {}).get("callbacks_dict", {}).get("reporter")
    task = state.get("task", "")
    plan = state.get("plan", "")
    research_notes = (state.get("research_notes", "") or "")[:6000]
    code = (state.get("code", "") or "")[:6000]
    review_feedback = (state.get("review_feedback", "") or "")[:3000]
    execution_output = state.get("execution_output", "")

    try:
        stream = run_reporter(
            task=task,
            plan=plan,
            research_notes=research_notes,
            code=code,
            review_feedback=review_feedback,
            execution_output=execution_output,
            config=config
        )
        final_report_text = _collect_stream(stream, callback=callback)

        try:
            memory.save_run(task, final_report_text)
        except Exception as e:
            print(f"[Warning] Failed to save run to memory: {e}")

        monitor.end_span("reporter", input_text=f"{task} {code} {execution_output}", output_text=final_report_text)

        return {
            "final_report": final_report_text,
            "status": "completed"
        }
    except Exception as e:
        monitor.end_span("reporter", input_text=task, error=str(e))
        raise
