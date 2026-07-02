"""
agents/planner.py

Planner Agent
Responsibilities: understand the user goal, break it into
smaller subtasks, and decide what the Research Agent and
Coding Agent should each do.
"""

from tools.llm import get_llm

PLANNER_PROMPT = """You are the Planner Agent in a multi-agent system.

The user wants this done:
{task}

Image file name: {image_name}

Break this down into a short, numbered plan with 4-6 steps.
Clearly separate:
- what the Research Agent should look up
- what the Coding Agent should build

Keep it short and easy to read.
"""


def run_planner(task: str, feedback: str = "", past_context: str = "", image_name: str = "") -> str:
    """Creates a step-by-step plan for the given task."""
    llm = get_llm(temperature=0.2)

    prompt = PLANNER_PROMPT.format(task=task, image_name=image_name or 'none')
    if past_context:
        prompt += f"\n\nContext from similar past runs:\n{past_context}\nUse this to avoid repeating mistakes or to build on previous success."

    if feedback:
        # if the human rejected the last plan, include their feedback
        prompt += f"\n\nThe human reviewer asked for this change: {feedback}\nUpdate the plan accordingly."

    response = llm.invoke(prompt)
    return response.content

