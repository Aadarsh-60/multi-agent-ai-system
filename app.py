import streamlit as st, time
from dotenv import load_dotenv
load_dotenv()

from graph import graph, AgentState, route_after_planner, route_review_decision
from graph.nodes import (
    planner_node,
    researcher_node,
    coder_node,
    execution_sandbox_node,
    reviewer_node,
    reporter_node
)
from agents.planner    import run_planner, check_research_needed
from agents.researcher import run_researcher
from agents.coder      import run_coder
from agents.reviewer   import run_reviewer, parse_review_decision
from agents.reporter   import run_reporter
from tools.sandbox import run_code_in_sandbox, detect_code_language
from memory.shared_memory import memory
from tools.pdf_generator import generate_pdf
from tools.monitor import monitor

st.set_page_config(page_title="AgentMind", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Playfair+Display:wght@700;900&display=swap');
:root {
    --navy: #0B1120;
    --navy2: #131B2C;
    --gold: #D4AF37;
    --gold2: rgba(212,175,55,.14);
    --g1: #E8ECF4;
    --g2: #9BA8BF;
    --g3: #3A4560;
    --b: rgba(255,255,255,.07);
    --glass: rgba(255,255,255,.04);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: var(--navy) !important; color: #fff !important; font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding: 40px !important; max-width: 95% !important; margin: 0 auto; }
::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-thumb { background: var(--gold2); border-radius: 2px; }

/* BRANDING & HERO */
.brand-container { display: flex; align-items: center; justify-content: space-between; margin-bottom: 40px; }
.brand { font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 900; color: #fff; }
.brand span { color: var(--gold); }
.badge { background: var(--glass); border: 1px solid rgba(255,255,255,.1); border-radius: 30px; padding: 6px 16px; font-size: 10px; font-weight: 700; letter-spacing: 1.5px; color: var(--gold); text-transform: uppercase; }

.h1 { font-family: 'Playfair Display', serif; font-size: clamp(40px, 4vw, 65px); font-weight: 900; line-height: 1.1; letter-spacing: -1px; color: #fff; margin-bottom: 8px; }
.h1 .gold { color: var(--gold); }
.h1-sub { font-family: 'Playfair Display', serif; font-size: clamp(24px, 2.5vw, 40px); font-weight: 700; color: rgba(255,255,255,.4); margin-bottom: 24px; }
.agents-list { font-size: 10px; font-weight: 1500; letter-spacing: 3px; color: var(--g2); text-transform: uppercase; margin-bottom: 48px; }

/* INPUT & CHIPS */
.lbl { font-size: 11px; font-weight: 700; letter-spacing: 3px; color: var(--g2); text-transform: uppercase; margin-bottom: 12px; }
.stTextInput>div>div>input, .stTextArea>div>div>textarea { background: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 8px !important; font-family: 'Inter', sans-serif !important; font-size: 16px !important; color: #000 !important; caret-color: #000 !important; padding: 18px 24px !important; box-shadow: none !important; transition: all .25s !important; }
.stTextInput>div>div>input::placeholder, .stTextArea>div>div>textarea::placeholder { color: #94a3b8 !important; }
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus { border-color: var(--gold) !important; box-shadow: 0 0 0 3px rgba(212,175,55,.15) !important; }
.stTextInput label, .stTextArea label { display: none !important; }

/* TOPIC BUTTONS */
[data-testid="stHorizontalBlock"] .stButton>button { background: rgba(255,255,255,.02) !important; border: 1px solid var(--b) !important; border-radius: 8px !important; font-size: 12px !important; font-weight: 500 !important; color: var(--g1) !important; padding: 12px 16px !important; letter-spacing: 0 !important; text-transform: uppercase !important; transition: all .2s !important; width: 100% !important; }
[data-testid="stHorizontalBlock"] .stButton>button:hover { background: rgba(255,255,255,.05) !important; border-color: rgba(255,255,255,.2) !important; color: #fff !important; }

/* PRIMARY RUN BUTTON */
.stButton>button[kind="primary"] { background: #0F172A !important; color: #fff !important; border: 1px solid rgba(255,255,255,.1) !important; border-radius: 8px !important; font-family: 'Inter', sans-serif !important; font-size: 14px !important; font-weight: 700 !important; letter-spacing: 1px; padding: 18px 32px !important; width: 100% !important; transition: all .25s !important; text-transform: uppercase; }
.stButton>button[kind="primary"]:hover { background: #1E293B !important; border-color: rgba(255,255,255,.2) !important; }

/* VERTICAL PIPELINE (RIGHT COLUMN) */
.vert-pipeline { display: flex; flex-direction: column; align-items: center; padding-top: 20px; }
.agent-card { background: var(--navy2); border: 1px solid var(--b); border-radius: 16px; padding: 20px 24px; width: 100%; max-width: 320px; display: flex; align-items: center; justify-content: space-between; transition: all .3s; }
.card-running { border-color: var(--gold); box-shadow: 0 0 20px rgba(212,175,55,.1); }
.card-done { border-color: rgba(16,185,129,.4); }
.agent-left { display: flex; align-items: center; gap: 16px; }
.agent-num { font-size: 14px; font-weight: 800; color: var(--gold); }
.agent-name { font-size: 16px; font-weight: 700; color: #fff; margin-bottom: 2px; }
.agent-role { font-size: 12px; color: var(--g2); }
.agent-dot { width: 10px; height: 10px; border-radius: 50%; background: #374151; transition: all .3s; }
.dot-running { background: #60A5FA; box-shadow: 0 0 10px #60A5FA; animation: pulse 1.5s infinite; }
.dot-done { background: #10B981; }
@keyframes pulse { 0% { opacity: 1; transform: scale(1); } 50% { opacity: 0.6; transform: scale(1.2); } 100% { opacity: 1; transform: scale(1); } }

.agent-connector { display: flex; flex-direction: column; align-items: center; margin: 4px 0; }
.agent-line { width: 1px; height: 24px; background: rgba(212,175,55,.4); }
.agent-arrow { font-size: 10px; color: rgba(212,175,55,.8); margin-top: -4px; }

/* PLAN / RESULT CARDS */
.task-title { font-size: 22px; font-weight: 700; color: #fff; margin-bottom: 24px; line-height: 1.3; }
.plan-card { background: var(--navy2); border: 1px solid rgba(212,175,55,.2); border-radius: 16px; padding: 26px; margin: 16px 0; }
.plan-hdr { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.plan-title { font-size: 17px; font-weight: 700; color: #fff; }
.plan-body { font-size: 14px; color: var(--g1); line-height: 1.8; white-space: pre-wrap; }

/* EXPANDERS */
[data-testid="stExpander"] { background: var(--navy2) !important; border: 1px solid var(--b) !important; border-radius: 12px !important; margin-bottom: 8px !important; }
[data-testid="stExpander"] summary { color: var(--g1) !important; font-size: 14px !important; font-weight: 600 !important; }

/* HORIZONTAL LINE */
hr.divider-line { border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 40px 0; }

/* 🎯 CONSTANT WIDTH CENTERED BLACK BOX FOR FINAL REPORT 🎯 */
div[data-testid="column"]:has(.report-box-marker) {
    background-color: #000000 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 16px !important;
    padding: 40px 50px !important;
    box-shadow: 0 20px 40px rgba(0,0,0,0.6) !important;
}

[data-testid="stMarkdownContainer"] { color: #F8FAFC !important; }
[data-testid="stMarkdownContainer"] h1, 
[data-testid="stMarkdownContainer"] h2, 
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] strong,
[data-testid="stMarkdownContainer"] b {
    color: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 800 !important;
    margin-top: 1.5em !important;
    margin-bottom: 0.5em !important;
}

/* 🎯 CUSTOM DOWNLOAD BUTTON - HIGH VISIBILITY PITCH BLACK TEXT 🎯 */

/* 🎯 CUSTOM DOWNLOAD BUTTON - HIGH VISIBILITY PITCH BLACK TEXT 🎯 */
[data-testid="stDownloadButton"] button,
[data-testid="stDownloadButton"] button p {
    background-color: #ffffff !important;
    color: #000000 !important;
    font-weight: 900 !important;
    font-size: 15px !important;
    border-radius: 8px !important;
    border: none !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
[data-testid="stDownloadButton"] button {
    padding: 16px 24px !important;
    box-shadow: 0 4px 14px rgba(255,255,255,0.2) !important;
}
[data-testid="stDownloadButton"] button:hover {
    background-color: #e2e8f0 !important;
    transform: translateY(-2px) !important;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown("## 💬 Chat with Agents")
    st.markdown("Ask questions or request quick revisions directly from any agent.", help="You can interact with agents outside the automated pipeline.")
    
    agent_choice = st.selectbox("Select Agent", ["Planner", "Researcher", "Coder", "Reviewer", "Reporter"])
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input(f"Message {agent_choice}..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            sys_msg = f"You are the {agent_choice} Agent in a multi-agent AI system. Answer the human's queries directly, concisely, and professionally. Ensure your output is highly structured using clear markdown headings and bullet points."
            full_prompt = f"{sys_msg}\n\nHuman: {prompt}\nAI:"
            
            from tools.llm import get_llm
            chat_llm = get_llm(temperature=0.3)
            response_text = st.write_stream(chat_llm.stream(full_prompt))
            st.session_state.chat_history.append({"role": "assistant", "content": response_text})

AGENTS = [
    ("Planner", "Plan & research check"),
    ("Researcher", "Web data & citations"),
    ("Coder", "Generates solution"),
    ("Sandbox", "Execution & validation"),
    ("Reviewer", "Quality & safety check"),
    ("Reporter", "Final deliverable")
]
CHIPS = ["Write a Python Web Scraper", "Build a REST API in FastAPI", "Sort Algorithms Comparison", "ML Model for Sentiment Analysis", "Docker Setup for Node.js App"]

# Initialize States
init_states = {
    "stage": "idle",
    "task": "",
    "plan": "",
    "feedback": "",
    "research_needed": True,
    "human_approval": "approved",
    "research_notes": "",
    "code": "",
    "execution_output": "",
    "review_feedback": "",
    "final_report": "",
    "sel_topic": "",
    "hide_report": False,
    "statuses": {n: "idle" for n, _ in AGENTS}
}
for k, v in init_states.items():
    if k not in st.session_state: st.session_state[k] = v

def render_vertical_pipeline():
    html = '<div class="vert-pipeline">'
    for i, (name, role) in enumerate(AGENTS, 1):
        status = st.session_state.statuses.get(name, "idle")
        dot_class = "dot-running" if status == "running" else "dot-done" if status == "done" else ""
        border_class = "card-running" if status == "running" else "card-done" if status == "done" else ""
        
        html += f'<div class="agent-card {border_class}"><div class="agent-left"><div class="agent-num">0{i}</div><div class="agent-info"><div class="agent-name">{name}</div><div class="agent-role">{role}</div></div></div><div class="agent-right"><div class="agent-dot {dot_class}"></div></div></div>'
        
        if i < len(AGENTS):
            html += '<div class="agent-connector"><div class="agent-line"></div><div class="agent-arrow">↓</div></div>'
            
    html += '</div>'
    return html

# --- LAYOUT SETUP ---
col_left, col_right = st.columns([3.5, 1], gap="large")

with col_right:
    pipeline_placeholder = st.empty()
    pipeline_placeholder.markdown(render_vertical_pipeline(), unsafe_allow_html=True)

def update_pipeline_ui():
    pipeline_placeholder.markdown(render_vertical_pipeline(), unsafe_allow_html=True)

left_col_container = col_left.container()
bottom_container = col_left.container()

with left_col_container:
    st.markdown("""
    <div class="brand-container">
        <div class="brand">Agent<span>Mind</span></div>
    </div>
    <div class="badge">⚡ PRODUCTION WORKFLOW · LANGGRAPH</div>
    <div class="h1">Intelligent <span class="gold">automation,</span></div>
    <div class="h1-sub">multi-agent thinking with sandbox validation.</div>
    <div class="agents-list">PLANNER · RESEARCHER · CODER · SANDBOX · REVIEWER · REPORTER</div>
    """, unsafe_allow_html=True)

    stage = st.session_state.stage

    # ── IDLE ──
    if stage == "idle":
        st.markdown('<div class="lbl">YOUR TASK</div>', unsafe_allow_html=True)
        task = st.text_input("t", value=st.session_state.sel_topic, placeholder="e.g. Build a REST API for a todo app using FastAPI", label_visibility="collapsed", key="task_field")
        
        st.markdown('<div class="lbl" style="margin-top:24px;">SUGGESTED TOPICS</div>', unsafe_allow_html=True)
        cols = st.columns(len(CHIPS))
        for i, c in enumerate(CHIPS):
            with cols[i]:
                if st.button(c, key=f"c{i}"):
                    st.session_state.sel_topic = c
                    st.rerun()
                    
        st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
        
        if st.button("⚡ RUN AGENT PIPELINE →", type="primary", key="run"):
            if task.strip():
                monitor.reset()
                st.session_state.task = task.strip()
                st.session_state.sel_topic = ""
                st.session_state.hide_report = False
                st.session_state.statuses["Planner"] = "running"
                st.session_state.stage = "planning"
                st.rerun()
            else: 
                st.error("Please enter a task.")


with left_col_container:
    # ── PLANNING ──
    if stage == "planning":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="plan-card"><div class="plan-hdr"><div class="plan-title">🧠 2. Planner Agent — Generating Execution Plan & Research Assessment...</div></div></div>', unsafe_allow_html=True)
        p = memory.recall_past_runs(st.session_state.task)
        plan_ph = st.empty()
        plan = plan_ph.write_stream(run_planner(st.session_state.task, st.session_state.feedback, p))
        st.session_state.plan = plan
        st.session_state.research_needed = check_research_needed(plan, st.session_state.task)
        st.session_state.statuses["Planner"] = "done"
        st.session_state.stage = "plan_ready"
        st.rerun()

    # ── PLAN READY (STEP 3: HUMAN APPROVAL) ──
    elif stage == "plan_ready":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### 📋 Proposed Execution Plan")
            st.markdown(st.session_state.plan)
            if st.session_state.research_needed:
                st.info("🔍 **Research Assessment**: External research evaluated as **Needed** (will query Tavily & gather documentation).")
            else:
                st.info("⚡ **Research Assessment**: Task is **Self-Contained** (will bypass Researcher and proceed directly to Coder).")

        st.markdown('<div class="lbl" style="margin-top:16px;">3. HUMAN APPROVAL</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.5, 1.2, 1], gap="medium")
        with c1:
            if st.button("✅ Approve Plan & Run", type="primary", key="app"):
                st.session_state.human_approval = "approved"
                if st.session_state.research_needed:
                    st.session_state.statuses["Researcher"] = "running"
                else:
                    st.session_state.statuses["Coder"] = "running"
                st.session_state.stage = "running"
                st.rerun()
        with c2:
            if st.button("✏️ Revise Plan (Feedback)", key="rej"):
                st.session_state.human_approval = "revise"
                st.session_state.stage = "rejected"
                st.rerun()
        with c3:
            if st.button("❌ Reject & Cancel", key="canc"):
                st.session_state.human_approval = "rejected"
                st.session_state.stage = "cancelled"
                st.rerun()

    # ── REJECTED (REVISE PLAN) ──
    elif stage == "rejected":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### 📋 Proposed Plan")
            st.markdown(st.session_state.plan)
        fb = st.text_area("What should change in the plan?", placeholder="e.g. Include SQLite schema, add error handling, use FastAPI instead…", height=100, key="fb")

        c1, c2 = st.columns(2, gap="medium")
        with c1:
            if st.button("🔄 Re-Plan (Loop to Planner)", type="primary", key="rp"):
                if fb.strip():
                    st.session_state.feedback = fb.strip() 
                    st.session_state.statuses["Planner"] = "running"
                    st.session_state.stage = "planning"
                    st.rerun()
                else: 
                    st.error("Enter feedback first.")
        with c2:
            if st.button("← Back", key="bk"):
                st.session_state.stage = "plan_ready"
                st.rerun()

    # ── CANCELLED (REJECTED BY USER) ──
    elif stage == "cancelled":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        st.error("❌ Workflow Cancelled (Rejected by User upon plan review).")
        with st.container(border=True):
            st.markdown("### 📋 Rejected Plan Proposal")
            st.markdown(st.session_state.plan)
        if st.button("⚡ Start New Task", type="primary", key="new_from_cancel"):
            for k in ["task", "plan", "feedback", "research_notes", "code", "execution_output", "review_feedback", "final_report", "sel_topic"]:
                st.session_state[k] = ""
            st.session_state.hide_report = False
            st.session_state.stage = "idle"
            st.session_state.statuses = {n: "idle" for n, _ in AGENTS}
            st.rerun()

    # ── RUNNING (LANGGRAPH PIPELINE EXECUTION) ──
    elif stage == "running":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### 📋 Approved Plan")
            st.markdown(st.session_state.plan)

        res_ph = st.empty()
        cod_ph = st.empty()
        sandbox_ph = st.empty()
        rev_ph = st.empty()
        line_ph = st.empty()
        report_title_ph = st.empty()
        report_box_ph = st.empty()

        prog = st.progress(0)
        stat = st.empty()

        def go(n, s): 
            st.session_state.statuses[n] = s
            update_pipeline_ui()

        # LangGraph State Initialization
        graph_state: AgentState = {
            "task": st.session_state.task,
            "plan": st.session_state.plan,
            "past_context": memory.recall_past_runs(st.session_state.task),
            "research_needed": st.session_state.get("research_needed", True),
            "research_notes": "",
            "research_feedback": "",
            "code": "",
            "execution_output": "",
            "review_feedback": "",
            "review_decision": "approved",
            "final_report": "",
            "iteration_count": 0,
            "max_iterations": 2,
            "status": "running"
        }

        # Step 4: Research Check & Step 4A: Researcher Agent
        if graph_state["research_needed"]:
            stat.info("🔍 4A. Researcher Agent — Gathering relevant information & source links…")
            prog.progress(15)
            go("Researcher", "running")
            with res_ph.expander("🔍 4A. Research Notes & Sources", expanded=True):
                notes = st.write_stream(run_researcher(graph_state["task"], graph_state["plan"], graph_state.get("research_feedback", "")))
            graph_state["research_notes"] = notes
            st.session_state.research_notes = notes
            go("Researcher", "done")
        else:
            stat.info("⏩ 4. Research Check — External research evaluated as not needed; proceeding to Coder.")
            prog.progress(15)
            graph_state["research_notes"] = "Self-contained task; external research was bypassed."
            st.session_state.research_notes = graph_state["research_notes"]
            with res_ph.expander("🔍 4. Research Check", expanded=False):
                st.markdown("*Task is self-contained. External web research was bypassed.*")
            go("Researcher", "done")

        # Step 5 -> Step 6 -> Step 7 -> Step 8 Loop
        while True:
            iteration = graph_state.get("iteration_count", 0)
            iter_suffix = f" (Attempt {iteration + 1})" if iteration > 0 else ""

            # Step 5: Coder Agent
            stat.info(f"💻 5. Coder Agent — Writing executable solution{iter_suffix}…")
            prog.progress(35 if iteration == 0 else 45)
            go("Coder", "running")

            coder_task = graph_state["task"]
            execution_feedback = ""
            if iteration > 0 and (graph_state.get("review_feedback") or graph_state.get("execution_output")):
                execution_feedback = (
                    f"Review Critique:\n{graph_state.get('review_feedback', '')[:2500]}\n\n"
                    f"Sandbox Execution Output:\n{graph_state.get('execution_output', '')[:2500]}"
                )

            notes_safe = graph_state["research_notes"][:6000] if graph_state.get("research_notes") else ""
            with cod_ph.expander(f"📄 5. Code Payload{iter_suffix}", expanded=True):
                code = st.write_stream(run_coder(coder_task, graph_state["plan"], notes_safe, execution_feedback))
            graph_state["code"] = code
            st.session_state.code = code
            go("Coder", "done")

            # Step 6: Execution & Validation (Sandbox)
            stat.info(f"⚙️ 6. Execution & Validation — Running code in sandbox{iter_suffix}…")
            prog.progress(55)
            go("Sandbox", "running")
            sandbox_res = run_code_in_sandbox(code, timeout_seconds=15)
            exec_formatted = (
                f"Status: {sandbox_res.get('summary')}\n"
                f"Exit Code: {sandbox_res.get('exit_code')}\n"
                f"--- STDOUT ---\n{sandbox_res.get('stdout', '') or '(empty)'}\n"
                f"--- STDERR ---\n{sandbox_res.get('stderr', '') or '(empty)'}"
            )
            graph_state["execution_output"] = exec_formatted
            st.session_state.execution_output = exec_formatted
            with sandbox_ph.expander(f"⚙️ 6. Execution & Validation (Sandbox){iter_suffix}", expanded=True):
                if sandbox_res.get("success"):
                    st.success(f"✅ {sandbox_res.get('summary')}")
                else:
                    st.warning(f"⚠️ {sandbox_res.get('summary')}")
                st.code(exec_formatted, language="text")
            go("Sandbox", "done")

            # Step 7: Reviewer Agent
            stat.info(f"🔎 7. Reviewer Agent — Evaluating correctness, quality & safety{iter_suffix}…")
            prog.progress(70)
            go("Reviewer", "running")
            code_safe = code[:6000] if code else ""
            with rev_ph.expander(f"🔎 7. Reviewer Feedback & Decision{iter_suffix}", expanded=True):
                rev = st.write_stream(run_reviewer(graph_state["task"], code_safe, exec_formatted, graph_state["plan"]))
            graph_state["review_feedback"] = rev
            st.session_state.review_feedback = rev

            decision = parse_review_decision(rev)
            graph_state["review_decision"] = decision
            graph_state["iteration_count"] = iteration + 1
            go("Reviewer", "done")

            # Step 8: Review Decision Routing
            next_route = route_review_decision(graph_state)
            if next_route == "coder":
                stat.warning(f"🔁 8. Review Decision: Need Changes! Looping back to Coder with critique and sandbox results (Attempt {graph_state['iteration_count'] + 1})...")
                time.sleep(1.2)
                go("Coder", "running")
                continue
            elif next_route == "researcher":
                stat.warning(f"🔁 8. Review Decision: More Research Needed! Looping back to Researcher for missing documentation...")
                time.sleep(1.2)
                go("Researcher", "running")
                with res_ph.expander(f"🔍 4A. Supplementary Research (Attempt {graph_state['iteration_count'] + 1})", expanded=True):
                    extra_notes = st.write_stream(run_researcher(graph_state["task"], graph_state["plan"], rev[:1500]))
                graph_state["research_notes"] += f"\n\n--- Supplementary Research ---\n{extra_notes}"
                st.session_state.research_notes = graph_state["research_notes"]
                go("Researcher", "done")
                go("Coder", "running")
                continue
            else:
                stat.success("✅ 8. Review Decision: Approved! Proceeding to Reporter Agent.")
                time.sleep(0.5)
                break

        # Step 9: Reporter Agent
        go("Reporter", "running")
        line_ph.markdown('<hr class="divider-line">', unsafe_allow_html=True)
        report_title_ph.markdown('<div style="text-align:center;font-size:12px;font-weight:700;color:var(--gold);margin-bottom:24px;letter-spacing:2px;">✦ 9. FINAL DELIVERABLE & REPORT</div>', unsafe_allow_html=True)

        with report_box_ph.container():
            st.markdown('<div class="report-box-marker"></div>', unsafe_allow_html=True)
            stat.info("📝 9. Reporter Agent — Writing comprehensive report & deliverable…")
            prog.progress(90)
            notes_safe = graph_state.get("research_notes", "")[:6000]
            code_safe = graph_state.get("code", "")[:6000]
            rev_safe = graph_state.get("review_feedback", "")[:3000]
            exec_safe = graph_state.get("execution_output", "")[:2500]

            rpt = st.write_stream(run_reporter(graph_state["task"], graph_state["plan"], notes_safe, code_safe, rev_safe, exec_safe))
            graph_state["final_report"] = rpt
            st.session_state.final_report = rpt 
            memory.save_run(graph_state["task"], rpt)

        go("Reporter", "done")
        prog.progress(100)
        time.sleep(0.3)
        stat.empty()
        prog.empty()
        st.session_state.stage = "done"
        st.rerun()

    # ── 10. END FINAL OUTPUT ──
    elif stage == "done":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("### 📋 Approved Plan")
            st.markdown(st.session_state.plan)

        # Expanders explicitly set to Open
        with st.expander("🔍 Research Notes & Sources", expanded=True): 
            st.markdown(st.session_state.research_notes)
        with st.expander("📄 Generated Code Solution", expanded=True): 
            detected_lang = detect_code_language(st.session_state.code)
            st.code(st.session_state.code, language=detected_lang)
        with st.expander("⚙️ Execution & Validation (Sandbox)", expanded=True):
            st.code(st.session_state.execution_output, language="text")
        with st.expander("🔎 Reviewer Evaluation & Decision", expanded=True): 
            st.markdown(st.session_state.review_feedback)

        # Telemetry & Observability Metrics Card
        metrics = monitor.get_summary()
        st.markdown('<div class="lbl" style="margin-top:20px;">📊 PIPELINE OBSERVABILITY & PERFORMANCE</div>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Tokens", f"{metrics['total_tokens']:,}", f"{metrics['input_tokens']:,} in / {metrics['output_tokens']:,} out")
        with m2:
            st.metric("Execution Latency", f"{metrics['total_latency_seconds']}s")
        with m3:
            st.metric("Estimated Cost", f"${metrics['estimated_cost_usd']:.4f} USD")
        with m4:
            err_label = "0 Errors" if metrics['error_count'] == 0 else f"{metrics['error_count']} Errors"
            st.metric("Pipeline Status", "Operational", err_label)

        with st.expander("🔍 Observability Debug Traces & Node Metrics", expanded=False):
            st.text(monitor.get_debug_trace())

        st.markdown('<hr class="divider-line">', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-size:12px;font-weight:700;color:var(--gold);margin-bottom:24px;letter-spacing:2px;">✦ 10. FINAL REPORT</div>', unsafe_allow_html=True)

        # Centered Output Box
        if not st.session_state.hide_report:
            st.markdown('<div class="report-box-marker"></div>', unsafe_allow_html=True)
            st.markdown(st.session_state.final_report)
        else:
            st.info("👁️ The final report is currently hidden. Click 'Show Report' below to reveal it.")

        # Action Buttons
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1, 1, 1, 1])

        with btn_col1:
            st.download_button(
                label="⬇️ Download Markdown",
                data=st.session_state.final_report,
                file_name="final_report.md",
                mime="text/markdown",
                use_container_width=True
            )

        with btn_col2:
            st.download_button(
                label="⬇️ Download PDF",
                data=generate_pdf(st.session_state.final_report),
                file_name="final_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with btn_col3:
            hide_btn_label = "👁️ Show Report" if st.session_state.hide_report else "👁️ Hide Report"
            if st.button(hide_btn_label, use_container_width=True):
                st.session_state.hide_report = not st.session_state.hide_report
                st.rerun()

        with btn_col4:
            if st.button("⚡ New Task", type="primary", key="nt", use_container_width=True):
                for k in ["task", "plan", "feedback", "research_notes", "code", "execution_output", "review_feedback", "final_report", "sel_topic"]:
                    st.session_state[k] = ""
                st.session_state.hide_report = False
                st.session_state.stage = "idle"
                st.session_state.statuses = {n: "idle" for n, _ in AGENTS}
                st.rerun()