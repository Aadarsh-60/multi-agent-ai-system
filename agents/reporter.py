"""
agents/reporter.py

Report Agent
Responsibilities: combine everything the other agents produced
into one final, readable report/response for the user.
"""

from tools.llm import get_llm

REPORT_PROMPT = """You are the Report Agent in a multi-agent system.
Combine all the work below into one clean final report for the user.

Original Task:
{task}

Plan:
{plan}

Research Notes:
{research_notes}

Generated Code:
{code}

Reviewer Feedback:
{review_feedback}

Write the final report with these sections:
- Summary
- What was researched
- Final code (include it as-is)
- Review notes
- Next steps / suggestions
"""


def run_reporter(task, plan, research_notes, code, review_feedback) -> str:
    """Combines all agent outputs into one final report."""
    llm = get_llm(temperature=0.3)
    prompt = REPORT_PROMPT.format(
        task=task,
        plan=plan,
        research_notes=research_notes,
        code=code,
        review_feedback=review_feedback,
    )
    response = llm.invoke(prompt)
    return response.content
