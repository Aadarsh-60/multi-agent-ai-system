"""
agents/coder.py

Coding Agent
Responsibilities: generate code based on the plan and research,
add comments, and keep it simple to read.

NOTE: this agent only runs AFTER a human has approved the plan
(see workflows/human_loop.py + workflows/graph.py).
"""

from tools.llm import get_llm

CODING_PROMPT = """You are the Coder Agent in a multi-agent system.
Write clean, production-ready code strictly following the approved plan and research findings.

Task:
{task}

Approved Plan:
{plan}

{research_section}
{validation_feedback_section}

STRICT PROGRAMMING LANGUAGE & ARCHITECTURE RULES:
1. ADHERE TO THE PLAN'S TARGET LANGUAGE & TECH STACK:
   Read the 'Approved Plan' and 'Task' carefully.
   You MUST write code in the EXACT programming language, framework, and architecture specified in the plan (e.g. Java / Spring Boot, Go, TypeScript / Node.js, C++, Rust, Python / FastAPI, etc.).
   NEVER default to or substitute Python if the plan or task requests Java, Go, TypeScript, C++, or another language!

2. COMPLETE & SELF-CONTAINED IMPLEMENTATION:
   Provide realistic, complete code with appropriate components (models/entities, controllers/handlers, services, repositories) and configuration as requested in the plan. Include clear comments.

3. PROPER MARKDOWN CODE BLOCKS:
   Wrap your code in standard Markdown code blocks with the appropriate language tag (e.g. ```java ... ``` for Java, ```go ... ``` for Go, ```typescript ... ``` for TypeScript, ```python ... ``` for Python).
"""


def run_coder(task: str, plan: str, research_notes: str = "", execution_feedback: str = "", config=None) -> str:
    """Generates code based on the approved plan, research notes, and execution feedback."""
    llm = get_llm(temperature=0.2)

    research_section = ""
    if research_notes:
        research_section = f"Research Findings:\n{research_notes}\n"

    validation_feedback_section = ""
    if execution_feedback:
        validation_feedback_section = f"Execution/Review Feedback to Fix:\n{execution_feedback}\n"

    prompt = CODING_PROMPT.format(
        task=task,
        plan=plan,
        research_section=research_section,
        validation_feedback_section=validation_feedback_section
    )
    return llm.stream(prompt, config=config)
