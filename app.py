import streamlit as st, time
from dotenv import load_dotenv
load_dotenv()

from agents.planner    import run_planner
from agents.researcher import run_researcher
from agents.coder      import run_coder
from agents.reviewer   import run_reviewer
from agents.reporter   import run_reporter
from memory.shared_memory import memory
from tools.pdf_generator import generate_pdf
from tools.notifier import notify_run_finished

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
#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="collapsedControl"], [data-testid="stDecoration"], section[data-testid="stSidebar"] { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding: 40px !important; max-width: 1400px !important; margin: 0 auto; }
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
.stTextInput>div>div>input, .stTextArea>div>div>textarea { background: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 8px !important; font-family: 'Inter', sans-serif !important; font-size: 16px !important; color: #000 !important; padding: 18px 24px !important; box-shadow: none !important; transition: all .25s !important; }
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

AGENTS = [
    ("Planner", "Plans subtasks"),
    ("Researcher", "Gathers info"),
    ("Coder", "Writes code"),
    ("Reviewer", "Reviews code"),
    ("Reporter", "Final report")
]
CHIPS = ["Write a Python Web Scraper", "Build a REST API in FastAPI", "Sort Algorithms Comparison", "ML Model for Sentiment Analysis", "Docker Setup for Node.js App"]

# Initialize States (Added hide_report to track visibility toggle)
for k, v in {"stage": "idle", "task": "", "plan": "", "feedback": "", "research_notes": "", "code": "", "review_feedback": "", "final_report": "", "sel_topic": "", "hide_report": False, "statuses": {n: "idle" for n, _ in AGENTS}}.items():
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
col_left, col_right = st.columns([1.6, 1], gap="large")

with col_right:
    pipeline_placeholder = st.empty()
    pipeline_placeholder.markdown(render_vertical_pipeline(), unsafe_allow_html=True)

def update_pipeline_ui():
    pipeline_placeholder.markdown(render_vertical_pipeline(), unsafe_allow_html=True)

with col_left:
    st.markdown("""
    <div class="brand-container">
        <div class="brand">Agent<span>Mind</span></div>
    </div>
    <div class="badge">⚡ MULTI-AGENT ENGINE</div>
    <div class="h1">Intelligent <span class="gold">automation,</span></div>
    <div class="h1-sub">five agents thinking together.</div>
    <div class="agents-list">PLANNER · RESEARCHER · CODER · REVIEWER · REPORTER</div>
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
                st.session_state.task = task.strip()
                st.session_state.sel_topic = ""
                st.session_state.hide_report = False
                st.session_state.statuses["Planner"] = "running"
                st.session_state.stage = "planning"
                st.rerun()
            else: 
                st.error("Please enter a task.")

    # ── PLANNING ──
    elif stage == "planning":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        with st.spinner("🧠 Planner Agent crafting your plan…"):
            p = memory.recall_past_runs(st.session_state.task)
            plan = run_planner(st.session_state.task, st.session_state.feedback, p)
            st.session_state.plan = plan 
            st.session_state.statuses["Planner"] = "done"
            st.session_state.stage = "plan_ready"
            st.rerun()

    # ── PLAN READY ──
    elif stage == "plan_ready":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="plan-card">
            <div class="plan-hdr">
                <div class="plan-title">📋 Proposed Plan</div>
            </div>
            <div class="plan-body">{st.session_state.plan}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            if st.button("✅ Approve & Run", type="primary", key="app"):
                st.session_state.statuses["Researcher"] = "running"
                st.session_state.stage = "running"
                st.rerun()
        with c2:
            if st.button("✏️ Reject & Revise", key="rej"):
                st.session_state.stage = "rejected"
                st.rerun()

    # ── REJECTED ──
    elif stage == "rejected":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="plan-card"><div class="plan-body">{st.session_state.plan}</div></div>', unsafe_allow_html=True)
        fb = st.text_area("What should change?", placeholder="e.g. Use TypeScript, add error handling…", height=100, key="fb")
        
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            if st.button("🔄 Re-Plan", type="primary", key="rp"):
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

    # ── RUNNING ──
    elif stage == "running":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="plan-card"><div class="plan-hdr"><div class="plan-title">📋 Approved Plan</div></div><div class="plan-body">{st.session_state.plan}</div></div>', unsafe_allow_html=True)
        
        res_ph = st.empty()
        cod_ph = st.empty()
        rev_ph = st.empty()
        line_ph = st.empty()
        report_title_ph = st.empty()
        report_box_ph = st.empty()
        
        prog = st.progress(0)
        stat = st.empty()
        
        def go(n, s): 
            st.session_state.statuses[n] = s
            update_pipeline_ui()

        # Step 1: Research
        stat.info("🔍 Researcher — gathering info…")
        prog.progress(20)
        notes = run_researcher(st.session_state.task, st.session_state.plan)
        st.session_state.research_notes = notes 
        with res_ph.expander("🔍 Research Notes", expanded=True):
            st.markdown(notes)
        go("Researcher", "done")
        go("Coder", "running")

        # Step 2: Code
        stat.info("💻 Coder — writing solution…")
        prog.progress(45)
        code = run_coder(st.session_state.task, st.session_state.plan, notes)
        st.session_state.code = code 
        with cod_ph.expander("📄 Code Payload", expanded=True):
            st.code(code, language="python")
        go("Coder", "done")
        go("Reviewer", "running")

        # Step 3: Review
        stat.info("🔎 Reviewer — reviewing code…")
        prog.progress(70)
        rev = run_reviewer(st.session_state.task, code)
        st.session_state.review_feedback = rev 
        with rev_ph.expander("🔎 Reviewer Feedback", expanded=True):
            st.markdown(rev)
        go("Reviewer", "done")
        go("Reporter", "running")

        line_ph.markdown('<hr class="divider-line">', unsafe_allow_html=True)
        report_title_ph.markdown('<div style="text-align:center;font-size:12px;font-weight:700;color:var(--gold);margin-bottom:24px;letter-spacing:2px;">✦ FINAL REPORT</div>', unsafe_allow_html=True)

        with report_box_ph.container():
            spacer_l, report_col, spacer_r = st.columns([0.5, 6, 0.5]) 
            with report_col:
                st.markdown('<div class="report-box-marker"></div>', unsafe_allow_html=True)
                stat.info("📝 Reporter — writing final report…")
                prog.progress(90)
                rpt = run_reporter(st.session_state.task, st.session_state.plan, notes, code, rev)
                st.session_state.final_report = rpt 
                memory.save_run(st.session_state.task, rpt)
                notify_run_finished(st.session_state.task, rpt)

        go("Reporter", "done")
        prog.progress(100)
        time.sleep(0.3)
        stat.empty()
        prog.empty()
        st.session_state.stage = "done"
        st.rerun()

    # ── DONE ──
    elif stage == "done":
        st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="plan-card"><div class="plan-hdr"><div class="plan-title">📋 Approved Plan</div></div><div class="plan-body">{st.session_state.plan}</div></div>', unsafe_allow_html=True)
        
        # Expanders explicitly set to Open
        with st.expander("🔍 Research Notes", expanded=True): 
            st.markdown(st.session_state.research_notes)
        with st.expander("📄 Code Payload", expanded=True): 
            st.code(st.session_state.code, language="python")
        with st.expander("🔎 Reviewer Feedback", expanded=True): 
            st.markdown(st.session_state.review_feedback)
            
        st.markdown('<hr class="divider-line">', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-size:12px;font-weight:700;color:var(--gold);margin-bottom:24px;letter-spacing:2px;">✦ FINAL REPORT</div>', unsafe_allow_html=True)
        
        # 🎯 Centered Output Logic with Hide Toggle 🎯
        spacer_l, report_col, spacer_r = st.columns([0.5, 6, 0.5])
        with report_col:
            if not st.session_state.hide_report:
                st.markdown('<div class="report-box-marker"></div>', unsafe_allow_html=True)
                st.markdown(st.session_state.final_report)
            else:
                st.info("👁️ The final report is currently hidden. Click 'Show Report' below to reveal it.")
            
        # 🎯 4 Actions Buttons Centered under the Report 🎯
        st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
        btn_spacer_l, btn_col1, btn_col2, btn_col3, btn_col4, btn_spacer_r = st.columns([0.5, 1.5, 1.5, 1.5, 1.5, 0.5])
        
        with btn_col1:
            st.download_button(
                label="⬇️ Download final Report (Markdown)",
                data=st.session_state.final_report,
                file_name="final_report.md",
                mime="text/markdown",
                use_container_width=True
            )
            
        with btn_col2:
            st.download_button(
                label="⬇️ Download final Report (PDF)",
                data=generate_pdf(st.session_state.final_report),
                file_name="final_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        with btn_col3:
            hide_btn_label = "👁️ Show final Report" if st.session_state.hide_report else "👁️ Hide final Report"
            if st.button(hide_btn_label, use_container_width=True):
                st.session_state.hide_report = not st.session_state.hide_report
                st.rerun()

        with btn_col4:
            if st.button("⚡ New Task", type="primary", key="nt", use_container_width=True):
                for k in ["task", "plan", "feedback", "research_notes", "code", "review_feedback", "final_report", "sel_topic"]:
                    st.session_state[k] = ""
                st.session_state.hide_report = False
                st.session_state.stage = "idle"
                st.session_state.statuses = {n: "idle" for n, _ in AGENTS}
                st.rerun()