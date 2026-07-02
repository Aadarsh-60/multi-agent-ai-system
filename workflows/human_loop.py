"""
workflows/human_loop.py

This is the "Human-in-the-loop" piece of the project.

The idea: before the system does something critical (like
generating and "running" code), we stop and ask a real human
to approve the plan. If the human says no, we ask the Planner
to revise the plan instead of just barging ahead.

This function is written so it can be reused by:
  - a simple terminal app (input())
  - a Streamlit app (we just swap this function out, see app.py)
"""


def ask_human_approval(plan: str) -> bool:
    """
    Shows the plan to a human and asks for approval.
    Returns True if approved, False if rejected.
    """
    print("\n========== HUMAN APPROVAL NEEDED ==========")
    print("The Planner Agent created this plan:\n")
    print(plan)
    print("=============================================")

    answer = input("Approve this plan and continue? (y/n): ").strip().lower()
    return answer == "y"


def ask_human_feedback() -> str:
    """
    If the human rejects the plan, we ask them what they
    want changed, and send that back to the Planner Agent.
    """
    feedback = input("What should be changed? ")
    return feedback
