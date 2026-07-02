# ⚡ AgentMind: Multi-Agent AI System

A modern, highly capable multi-agent application that turns a user request into a structured plan, gets human approval, and then runs specialized AI agents for research, coding, review, and reporting. 

The application is built on a unified **Streamlit** architecture, featuring a premium dark-mode UI, human-in-the-loop control, real-time status tracking, automated database querying, Slack notifications, and PDF report generation.

## 🚀 Key Features

- **5-Agent Pipeline:** Planner → Researcher → Coder → Reviewer → Reporter.
- **Human-in-the-Loop:** Explicitly approve or request revisions to the Planner's proposed execution plan before work begins.
- **Unified Streamlit UI:** A stunning, responsive, single-page application built entirely in Python without separate frontend/backend layers.
- **Intelligent Tooling:** 
  - **Tavily Search** for live web data.
  - **Auto-SQL Tool** that dynamically spins up databases, writes queries, and executes them if your task involves data or databases.
  - **Notifier** that sends the final completion message straight to your **Slack**.
- **Memory:** Uses ChromaDB to persist run data and recall past runs so the agents learn from history.
- **Exporting:** Download the final comprehensive report as raw Markdown or a perfectly formatted PDF.

## 🛠️ Tech Stack

- **Python 3.11+**
- **Streamlit** (UI & State Management)
- **LangChain** (Agent orchestration)
- **Grok API** (xAI LLM Engine)
- **Tavily API** (Web Search)
- **SQLite** (Database tool)
- **ChromaDB** (Memory storage)
- **FPDF2** (PDF Generation)

## 📁 Project Structure

```text
multi-agent-ai-system/
├── app.py               # Main Streamlit application and UI logic
├── agents/              # The 5 specialized agents (Planner, Researcher, Coder, Reviewer, Reporter)
├── tools/               # Tools used by agents (LLM config, Web Search, SQL query, PDF generator, Slack Notifier)
├── memory/              # ChromaDB shared memory layer
├── requirements.txt     # Python dependencies
└── .env                 # Environment variables (API Keys)
```

## ⚙️ Setup Locally

1. **Clone the repository and enter the directory:**
   ```bash
   git clone <your-repo-url>
   cd multi-agent-ai-system
   ```

2. **Create and activate a Python virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   XAI_API_KEY="your_grok_key_here"
   TAVILY_API_KEY="your_tavily_key_here"
   SLACK_WEBHOOK_URL="your_slack_webhook_here"  # Optional: For Slack notifications
   ```

## 🏃‍♂️ Run the App

Because everything is unified in Streamlit, you only need one command to start the entire system:

```bash
streamlit run app.py
```

Open the provided `localhost` URL in your browser to interact with AgentMind.

## 🔄 Structural Flow

The system orchestrates a sophisticated graph of agents that work together sequentially. Here is how data moves through the application:

                    User Input / Task Request
                              │
                              ▼
                        Planner Agent
                              │
                              ▼
                    Human-in-the-Loop
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
          Reject / Feedback        Approve
                    │                   │
                    └───────┐           ▼
                            │    Researcher Agent
                            │      ┌──────┴──────┐
                            │      │             │
                            ▼      ▼             ▼
                     Planner Agent Tavily API  SQLite Tool
                                           │
                                           ▼
                                      Coder Agent
                                           │
                                           ▼
                                     Reviewer Agent
                                           │
                                           ▼
                                     Reporter Agent
                                   ┌────────┴────────┐
                                   │                 │
                                   ▼                 ▼
                         Render Final Report   Slack Notification
                                   │
                                   ▼
                         Download PDF / Markdown    



### The Execution Steps
1. **Input Task**: You enter a prompt (e.g., *"Write a Python Web Scraper"*).
2. **Planning Phase**: The **Planner** generates a detailed step-by-step strategy.
3. **Approval**: You review the plan. You can either approve it or write feedback to force a re-plan.
4. **Execution Phase**:
   - **Researcher**: Gathers context from the web and executes SQL queries if needed.
   - **Coder**: Writes the actual code based on the plan and research.
   - **Reviewer**: Critiques the code and provides improvements.
   - **Reporter**: Compiles everything into a clean, comprehensive Markdown report.
5. **Delivery**: The app sends a Slack notification and displays the final report, allowing you to instantly download it as a **Markdown file** or **PDF**.

## 💡 Examples

Here are a few ways to interact with the AgentMind system depending on your needs.

### Example 1: Standard Coding Task
**Prompt:** `"Write a robust Python Web Scraper using BeautifulSoup that extracts article titles from a blog and saves them to a CSV."`

* **What happens:** The Planner breaks down the steps. Once approved, the Researcher looks up best practices for BeautifulSoup. The Coder writes the script. The Reviewer ensures error handling is in place, and the Reporter outputs a full guide with the final code snippet.

### Example 2: Database / SQL Task
**Prompt:** `"Write a Python script to fetch the Premium users from our database."`
* **What happens:** The system detects database keywords. During the Research phase, the **Auto-SQL Tool** automatically spins up a local SQLite dummy database, queries the schema for "Premium" users, and passes the schema structure and data to the Coder. The final report will include a perfectly tailored script to access your specific database schema.
