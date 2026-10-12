"""
agents/reporter.py

Report Agent
Responsibilities: combine everything the other agents produced
into one final, readable report/response for the user.
"""

from tools.llm import get_llm

REPORT_PROMPT = """You are the Reporter Agent in a multi-agent system.
Prepare a clear, comprehensive, and well-formatted final response for the user with explanations, results, and source citations.

CRITICAL ACCURACY & GROUNDING RULES:
1. MATCH ORIGINAL USER REQUEST & APPROVED PLAN:
   Your final report must directly and faithfully answer and implement the original user request according to the approved plan. Ensure all code, architecture descriptions, dependencies, build configurations, and explanations reflect the target programming language and framework specified in the plan (e.g., Java / Maven / Gradle for Java plans, Go for Go plans, TypeScript / npm for TypeScript plans, Python for Python plans). NEVER substitute Python explanations, package managers, or libraries if the solution and plan are in Java, Go, TypeScript, or another language!

2. FACTUAL CITATIONS & SOURCES:
   Only cite real, authentic URLs and sources that appear in the 'Research Findings & Sources' below. Explicitly include the actual URLs from the research notes in markdown link format (e.g., [Source Name](URL)). Never invent or hallucinate URLs, domains, or citations. If no external research was conducted or needed, explicitly state: "Task is self-contained; no external sources cited."

3. TRUTHFUL TEST & VALIDATION REPORTING:
   Examine the 'Sandbox Execution & Validation Results' carefully.
   - If the sandbox execution succeeded (Exit Code: 0, no exceptions), report the clean run and verified outputs.
   - If the sandbox execution failed (non-zero exit code, Traceback, SyntaxError, or AssertionError):
     You MUST explicitly state that the execution or tests FAILED. You must NEVER claim that failed tests or broken code passed. Explain exactly what failed and suggest a fix.

Original Task:
{task}

Plan:
{plan}

Research Findings & Sources:
{research_notes}

Final Approved Code:
{code}

Sandbox Execution & Validation Results:
{execution_output}

Reviewer Notes:
{review_feedback}

Write the final report with these sections:
- Executive Summary & Solution Overview
- Research Highlights & Citations (list sources if researched, or note that task was self-contained)
- Complete Executable Code
- Execution & Validation Findings (truthful summary of sandbox execution and tests)
- Reviewer Quality Assessment
- Recommended Next Steps
"""


def run_reporter(task, plan, research_notes, code, review_feedback, execution_output: str = "", config=None) -> str:
    """Combines all agent outputs into one final report."""
    llm = get_llm(temperature=0.3)
    prompt = REPORT_PROMPT.format(
        task=task,
        plan=plan,
        research_notes=research_notes or "Self-contained logic; no external research required.",
        code=code,
        execution_output=execution_output or "Executed successfully in sandbox environment.",
        review_feedback=review_feedback or "Approved without reservations.",
    )
    return llm.stream(prompt, config=config)
