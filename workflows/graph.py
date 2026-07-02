"""
workflows/graph.py

This is the "orchestrator" — it wires all 5 agents together into
one workflow using LangGraph, with a human-approval checkpoint
sitting right after the Planner Agent.

Flow:

  User Request
       v
  Planner Agent
       v
  Human Approval  --(rejected)--> back to Planner (with feedback)
       v (approved)
  Research Agent  (uses Tavily)
       v
  Coding Agent
       v
  Reviewer Agent
       v
  Report Agent
       v
  Final Response
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END

from agents.planner import run_planner
from agents.researcher import run_researcher
from agents.coder import run_coder
from agents.reviewer import run_reviewer
from agents.reporter import run_reporter
from workflows.human_loop import ask_human_approval, ask_human_feedback
from memory.shared_memory import memory
from tools.notifier import notify_run_finished


# ---- 1. Define the shared state that flows between every node ----
class AgentState(TypedDict):
    task: str
    plan: str
    feedback: str
    approved: bool
    research_notes: str
    code: str
    review_feedback: str
    final_report: str


# ---- 2. Define one function ("node") per step in the flow ----

def planner_node(state: AgentState) -> AgentState:
    past_context = memory.recall_past_runs(state["task"])
    plan = run_planner(state["task"], state.get("feedback", ""), past_context)
    state["plan"] = plan
    return state


def human_approval_node(state: AgentState) -> AgentState:
    approved = ask_human_approval(state["plan"])
    state["approved"] = approved
    if not approved:
        state["feedback"] = ask_human_feedback()
    return state


def research_node(state: AgentState) -> AgentState:
    notes = run_researcher(state["task"], state["plan"])
    state["research_notes"] = notes
    return state


def coding_node(state: AgentState) -> AgentState:
    code = run_coder(state["task"], state["plan"], state["research_notes"])
    state["code"] = code
    return state


def reviewer_node(state: AgentState) -> AgentState:
    feedback = run_reviewer(state["task"], state["code"])
    state["review_feedback"] = feedback
    return state


def reporter_node(state: AgentState) -> AgentState:
    report = run_reporter(
        state["task"],
        state["plan"],
        state["research_notes"],
        state["code"],
        state["review_feedback"],
    )
    state["final_report"] = report
    # Save to long term memory
    memory.save_run(state["task"], report)
    # Notify
    notify_run_finished(state["task"], report)
    return state


# ---- 3. Routing function: decide where to go after human approval ----
def route_after_approval(state: AgentState) -> str:
    if state["approved"]:
        return "research"
    else:
        return "planner"  # loop back so Planner can revise


# ---- 4. Build the graph ----
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("research", research_node)
    graph.add_node("coding", coding_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node("reporter", reporter_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "human_approval")

    # this is the human-in-the-loop branch point
    graph.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {"research": "research", "planner": "planner"},
    )

    graph.add_edge("research", "coding")
    graph.add_edge("coding", "reviewer")
    graph.add_edge("reviewer", "reporter")
    graph.add_edge("reporter", END)

    return graph.compile()


# ---- 5. Convenience function used by app.py / main.py ----
def run_multi_agent_system(task: str) -> AgentState:
    app = build_graph()
    initial_state: AgentState = {
        "task": task,
        "plan": "",
        "feedback": "",
        "approved": False,
        "research_notes": "",
        "code": "",
        "review_feedback": "",
        "final_report": "",
    }
    final_state = app.invoke(initial_state, config={"recursion_limit": 25})
    return final_state
