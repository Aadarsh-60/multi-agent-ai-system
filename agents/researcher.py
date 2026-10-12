"""
agents/researcher.py

Research Agent
Responsibilities: search the web (using Tavily), collect
information, and summarize the findings for the other agents.
"""

from tools.llm import get_llm
from tools.search_tool import search_tool

RESEARCH_PROMPT = """You are the Researcher Agent in a multi-agent system.
Search and collect relevant and reliable information from trusted sources to guide implementation.

ACCURACY & CITATION RULES:
- Include only verifiable facts and actual URLs from the search results provided.
- Do not fabricate sources or invent links.
- Clearly present source URLs so the Coder and Reporter can cite them.

STRICT PROGRAMMING LANGUAGE & ECOSYSTEM RULES:
1. ADHERE TO THE PLAN'S TARGET LANGUAGE & ECOSYSTEM:
   Carefully examine the 'Plan from Planner Agent' and 'Task'.
   You MUST align ALL findings, dependencies, packages, and practical implementation notes to the EXACT programming language and stack specified in the plan (e.g. Java, Go, TypeScript/JavaScript, Rust, C++, C#, Python).
   - If the plan specifies Java:
     * Focus research exclusively on Java libraries (e.g. Jsoup, java.net.http.HttpClient, Spring Boot, JUnit 5).
     * Recommend Java build tools and dependency snippets (e.g. Maven <dependency> in pom.xml, or Gradle build.gradle).
     * DO NOT recommend Python tools (pip, poetry, requirements.txt, requests, beautifulsoup4, pytest)!
   - If the plan specifies Go:
     * Recommend Go modules (`go get`), standard library packages (net/http), and Go idioms.
     * DO NOT recommend Python or Java tools!
   - If the plan specifies TypeScript / JavaScript:
     * Recommend npm/yarn/pnpm packages (`package.json`), TypeScript types, and modern JS/TS libraries.
   - If the plan specifies Python:
     * Recommend Python libraries, pip/poetry dependencies, and pytest.
   NEVER substitute or hallucinate Python tools when the plan has designated Java, Go, TypeScript, C++, or another language!

Task: {task}
Plan from Planner Agent:
{plan}

{feedback_section}

Here are the search results:
{search_results}

Using the results above, compile concise, structured key findings with authentic source links/citations.
Outline practical implementation notes, APIs, dependencies, and caveats for the Coding Agent in the EXACT programming language specified in the plan.
"""


def _extract_plan_tech_terms(task: str, plan: str) -> str:
    """Extracts target language or key libraries from plan to ensure focused web queries."""
    plan_lower = plan.lower()
    task_lower = task.lower()
    terms = []
    candidates = [
        ("java", "Java"),
        ("jsoup", "Jsoup"),
        ("spring", "Spring Boot"),
        ("golang", "Go"),
        (" go ", "Go"),
        ("typescript", "TypeScript"),
        ("node", "Node.js"),
        ("rust", "Rust"),
        ("cpp", "C++"),
        ("c++", "C++"),
        ("c#", "C#"),
        (".net", ".NET"),
        ("python", "Python"),
        ("fastapi", "FastAPI"),
    ]
    for kw, label in candidates:
        if kw in plan_lower and label.lower() not in task_lower and label not in terms:
            terms.append(label)
    return " ".join(terms[:3])


def run_researcher(task: str, plan: str, research_feedback: str = "", config=None) -> str:
    """Searches the web and summarizes findings relevant to the task and plan tech stack."""
    query = task
    plan_terms = _extract_plan_tech_terms(task, plan)
    if plan_terms:
        query = f"{query} {plan_terms}"
    if research_feedback:
        query = f"{query} {research_feedback}"

    # 1. search the web with Tavily
    search_results = "WEB SEARCH RESULTS:\n" + search_tool(query)

    feedback_section = ""
    if research_feedback:
        feedback_section = f"Reviewer Note (Additional Research Requested):\n{research_feedback}\n"

    # 2. ask the LLM to turn raw search results into a clean summary
    llm = get_llm(temperature=0.2)
    prompt = RESEARCH_PROMPT.format(
        task=task,
        plan=plan,
        feedback_section=feedback_section,
        search_results=search_results
    )
    return llm.stream(prompt, config=config)
