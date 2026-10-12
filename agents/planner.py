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

Break this task down into a clear, structured execution plan with 4-6 numbered steps.
Include:
1. Executive summary of the goal
2. Research Assessment: Explicitly state "Research Needed: Yes" or "Research Needed: No" with a 1-sentence justification (e.g. Yes if external documentation, libraries, or live info is required; No if it is standard self-contained code/logic).
3. Detailed breakdown of responsibilities:
   - Research Agent (if research is needed): specific queries and documentation topics
   - Coding Agent: architecture, classes/functions, and implementation details
   - Execution & Validation: what outputs, tests, or assertions to run in the sandbox
   - Reviewer Agent: specific correctness, quality, and edge case checklist
   - Reporter Agent: final deliverable structure and summaries

Ensure your output is highly structured using clear markdown headings and bullet points.
"""


def check_research_needed(plan_text: str, task: str = "") -> bool:
    """Parses whether external research is needed from planner output or task context."""
    text = (plan_text + "\n" + task).lower()
    if "research needed: no" in text or "research needed: false" in text:
        return False
    if "research needed: yes" in text or "research needed: true" in text:
        return True
    # Default to False for basic algorithms/math unless external/real-time info is asked
    research_indicators = ["search", "latest", "recent", "api", "docs", "documentation", "scrap", "live data", "news", "trend"]
    return any(ind in text for ind in research_indicators)


def run_planner(task: str, feedback: str = "", past_context: str = "", image_name: str = "", config=None) -> str:
    """Creates a step-by-step plan for the given task."""
    llm = get_llm(temperature=0.2)

    prompt = PLANNER_PROMPT.format(task=task, image_name=image_name or 'none')
    if past_context:
        prompt += f"\n\nContext from similar past runs:\n{past_context}\nUse this to avoid repeating mistakes or to build on previous success."

    if feedback:
        # if the human rejected the last plan, include their feedback
        prompt += f"\n\nThe human reviewer asked for this change: {feedback}\nUpdate the plan accordingly."

    return llm.stream(prompt, config=config)


