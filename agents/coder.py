"""
agents/coder.py

Coding Agent
Responsibilities: generate code based on the plan and research,
add comments, and keep it simple to read.

NOTE: this agent only runs AFTER a human has approved the plan
(see workflows/human_loop.py + workflows/graph.py).
"""

from tools.llm import get_llm

CODING_PROMPT = """You are the Coding Agent in a multi-agent system.

Task: {task}

Plan (approved by a human):
{plan}

Research notes:
{research_notes}

Write clean, production-ready Python code that solves the task.
Add short comments explaining each part.
Only output the code, no extra explanation outside of code comments.
"""


def run_coder(task: str, plan: str, research_notes: str) -> str:
    """Generates code based on the approved plan and research notes."""
    llm = get_llm(temperature=0.2)
    prompt = CODING_PROMPT.format(
        task=task, plan=plan, research_notes=research_notes
    )
    response = llm.invoke(prompt)
    return response.content
