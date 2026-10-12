"""
graph/state.py

Defines the centralized AgentState schema for the AgentMind LangGraph workflow.
Matches the 10-step production workflow architecture:
  1. START (User Request)
  2. Planner Agent
  3. Human Approval (Approve / Revise / Reject)
  4. Research Needed? (Yes -> Researcher / No -> Coder)
  4A. Researcher Agent
  5. Coder Agent
  6. Execution & Validation (Sandbox)
  7. Reviewer Agent
  8. Review Decision (approved / need_changes / more_research_needed)
  9. Reporter Agent
  10. END Final Output
"""

from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """The shared state passed between all nodes in the multi-agent graph."""
    task: str
    plan: str
    feedback: str
    past_context: str
    image_name: str
    
    # Step 3: Human Approval
    human_approval: str  # 'approved', 'revise', 'rejected'
    
    # Step 4: Research Check
    research_needed: bool
    research_notes: str
    research_feedback: str  # Set when reviewer loops back for more research
    
    # Step 5: Coder Agent
    code: str
    
    # Step 6: Execution & Validation (Sandbox)
    execution_output: str
    execution_success: bool
    execution_stderr: str
    
    # Step 7 & 8: Reviewer & Decision
    review_feedback: str
    review_decision: str  # 'approved', 'need_changes', 'more_research_needed'
    
    # Loop controls
    iteration_count: int
    max_iterations: int
    
    # Step 9 & 10: Reporter & Output
    final_report: str
    status: str
