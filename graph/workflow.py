"""
graph/workflow.py

Defines and compiles the LangGraph StateGraph connecting all multi-agent nodes
strictly adhering to the AgentMind production workflow:

  1. START
  2. Planner Agent
  3. Human Approval? (Approve -> Step 4 / Revise -> Step 2 / Reject -> Cancelled)
  4. Research Needed? (Yes -> Researcher / No -> Coder)
  4A. Researcher Agent
  5. Coder Agent
  6. Execution & Validation (Sandbox)
  7. Reviewer Agent
  8. Review Decision (approved -> Reporter / need_changes -> Coder / more_research_needed -> Researcher)
  9. Reporter Agent
  10. END
"""

from typing import Optional, List, Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import AgentState
from graph.nodes import (
    planner_node,
    researcher_node,
    coder_node,
    execution_sandbox_node,
    reviewer_node,
    reporter_node
)


def cancelled_node(state: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """Handles explicit human cancellation."""
    return {
        "status": "cancelled",
        "final_report": "Workflow was cancelled by the user upon plan review."
    }


def route_after_planner(state: Dict[str, Any]) -> str:
    """Step 3 & 4: Evaluates Human Approval and Research Requirement:
      - 'rejected' -> 'cancelled'
      - 'revise' -> 'planner' (loops back with feedback)
      - 'approved' (or default) -> 'researcher' if research_needed else 'coder'
    """
    approval = state.get("human_approval", "approved")
    if approval == "rejected":
        return "cancelled"
    elif approval == "revise":
        return "planner"

    # Step 4: Research Check
    if state.get("research_needed", True):
        return "researcher"
    return "coder"


def route_review_decision(state: Dict[str, Any]) -> str:
    """Step 8: Review Decision - 3-way conditional branch with iteration guards:
      - approved -> reporter
      - need_changes -> coder (Loop)
      - more_research_needed -> researcher (Loop)
    """
    decision = state.get("review_decision", "approved")
    iteration = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", 2)

    if iteration >= max_iter:
        return "reporter"

    if decision == "need_changes":
        return "coder"
    elif decision == "more_research_needed":
        return "researcher"
    return "reporter"


def create_multi_agent_graph(
    checkpointer: Optional[Any] = None,
    store: Optional[Any] = None,
    interrupt_before: Optional[List[str]] = None
):
    """Compiles the full AgentMind multi-agent workflow with Stage 1 checkpointer & Stage 2 store."""
    from memory.workflow_checkpoint import workflow_memory
    from memory.user_store import user_memory_store

    workflow = StateGraph(AgentState)

    # 1. Register Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("validator", execution_sandbox_node)
    workflow.add_node("reviewer", reviewer_node)
    workflow.add_node("reporter", reporter_node)
    workflow.add_node("cancelled", cancelled_node)

    # 2. Add Edges & Conditional Branches
    workflow.add_edge(START, "planner")

    # Step 3 & 4: Human Approval Check and Research Check after planner
    workflow.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "cancelled": "cancelled",
            "planner": "planner",
            "researcher": "researcher",
            "coder": "coder"
        }
    )

    # Researcher -> Coder
    workflow.add_edge("researcher", "coder")

    # Coder -> Sandbox Validator
    workflow.add_edge("coder", "validator")

    # Validator -> Reviewer
    workflow.add_edge("validator", "reviewer")

    # Step 8: 3-Way Review Decision
    workflow.add_conditional_edges(
        "reviewer",
        route_review_decision,
        {
            "reporter": "reporter",
            "coder": "coder",
            "researcher": "researcher"
        }
    )

    # Reporter & Cancelled -> END
    workflow.add_edge("reporter", END)
    workflow.add_edge("cancelled", END)

    # Stage 1: Persistent Workflow Memory (Checkpointer)
    if checkpointer is None:
        checkpointer = workflow_memory.checkpointer

    # Stage 2: Long-Term User Memory (Store)
    if store is None:
        store = user_memory_store.store

    compiled_graph = workflow.compile(
        checkpointer=checkpointer,
        store=store,
        interrupt_before=interrupt_before
    )

    return compiled_graph


# Default compiled graph instance
graph = create_multi_agent_graph()
