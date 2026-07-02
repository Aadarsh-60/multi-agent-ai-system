"""
agents/researcher.py

Research Agent
Responsibilities: search the web (using Tavily), collect
information, and summarize the findings for the other agents.
"""

from tools.llm import get_llm
from tools.search_tool import search_tool
from tools.sql_tool import ask_database

RESEARCH_PROMPT = """You are the Research Agent in a multi-agent system.

Task: {task}
Plan from Planner Agent:
{plan}

Here are the combined context/results (Web Search + Database if applicable):
{search_results}

Using the results above, write a short, clear research summary
(bullet points are fine) that the Coding Agent can use to build the solution.
Only include information relevant to the task.
"""


def run_researcher(task: str, plan: str) -> str:
    """Searches the web and DB, and summarizes findings relevant to the task."""
    # 1. search the web with Tavily
    search_results = "WEB SEARCH RESULTS:\n" + search_tool(task)
    
    # If the task mentions database or users, query the SQL DB too
    if any(keyword in task.lower() for keyword in ["database", "sql", "users", "query"]):
        search_results += "\n\nDATABASE RESULTS:\n" + ask_database(task)

    # 2. ask the LLM to turn raw search results into a clean summary
    llm = get_llm(temperature=0.2)
    prompt = RESEARCH_PROMPT.format(
        task=task, plan=plan, search_results=search_results
    )
    response = llm.invoke(prompt)
    return response.content
