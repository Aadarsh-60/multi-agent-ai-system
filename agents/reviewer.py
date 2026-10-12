"""
agents/reviewer.py

Reviewer Agent
Responsibilities: check the generated code for quality,
point out bugs/issues, and suggest improvements.
"""

from tools.llm import get_llm

REVIEW_PROMPT = """You are the Reviewer Agent in a multi-agent system.
Check the correctness, quality, safety, and requirement coverage of the generated solution.

STRICT LANGUAGE & PLAN CONFORMANCE:
- Verify that the generated code is written in the EXACT programming language and framework specified in the Plan and Task (e.g. Java, Go, TypeScript, Rust, Python).
- If the plan specifies Java, and the code was written in Python (or vice versa), you MUST flag this as a critical failure and return "DECISION: need_changes" specifying that the code must be rewritten in the target language designated in the plan.

Task & Requirements:
{task}

Plan:
{plan}

Generated Code:
{code}

Sandbox Execution & Validation Results:
{execution_results}

Evaluate the solution:
1. Language & Plan Conformance: Is the code written in the exact language and architecture required by the plan?
2. Correctness & Functionality: Does the code fulfill all requirements?
3. Execution Analysis: Did the code execute successfully in the sandbox? If there were runtime errors, tracebacks, or syntax issues, detail them.
4. Code Quality & Safety: Is the code clean, modular, and free of dangerous calls?
5. Final Review Decision:
   You MUST end your review with an explicit decision line exactly in one of these three formats:
   - "DECISION: approved" (Code is correct, in the right language, runs without fatal errors, and fulfills requirements)
   - "DECISION: need_changes" (Code has bugs, wrong programming language, syntax/runtime errors, missing logic, or needs refactoring)
   - "DECISION: more_research_needed" (Missing external documentation, unfamiliar third-party API changes, or foundational research is required)
"""


def parse_review_decision(review_text: str) -> str:
    """Parses whether the reviewer decided approved, need_changes, or more_research_needed."""
    lower = review_text.lower()
    if "decision: more_research_needed" in lower or "more_research_needed" in lower:
        return "more_research_needed"
    if "decision: need_changes" in lower or "needs work" in lower or "need_changes" in lower:
        return "need_changes"
    if "decision: approved" in lower or "approved" in lower:
        return "approved"
    return "approved"


def run_reviewer(task: str, code: str, execution_results: str = "", plan: str = "", config=None) -> str:
    """Reviews the generated code and sandbox execution results."""
    llm = get_llm(temperature=0.2)
    exec_text = execution_results or "No execution output captured."
    prompt = REVIEW_PROMPT.format(
        task=task,
        code=code,
        execution_results=exec_text,
        plan=plan or "Refer to task requirements."
    )
    return llm.stream(prompt, config=config)
