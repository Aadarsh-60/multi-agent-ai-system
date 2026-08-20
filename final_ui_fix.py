import re

with open("app.py", "r") as f:
    app_code = f.read()

# 1. Fix CSS to allow the sidebar and its expand control to show
app_code = app_code.replace(
    '#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="collapsedControl"], [data-testid="stDecoration"], section[data-testid="stSidebar"] { display: none !important; }',
    '#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }'
)

# 2. Fix the Plan Card HTML rendering in `plan_ready`
plan_ready_old = """            elif stage == "plan_ready":
                st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
                st.markdown(f'''
                <div class="plan-card">
                    <div class="plan-hdr">
                        <div class="plan-title">📋 Proposed Plan</div>
                    </div>
                    <div class="plan-body">{st.session_state.plan}</div>
                </div>
                ''', unsafe_allow_html=True)"""
plan_ready_new = """            elif stage == "plan_ready":
                st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("### 📋 Proposed Plan")
                    st.markdown(st.session_state.plan)"""
app_code = app_code.replace(plan_ready_old, plan_ready_new)

# 3. Fix the Plan Card HTML rendering in `rejected`
rejected_old = """            # ── REJECTED ──
            elif stage == "rejected":
                st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="plan-card"><div class="plan-body">{st.session_state.plan}</div></div>', unsafe_allow_html=True)"""
rejected_new = """            # ── REJECTED ──
            elif stage == "rejected":
                st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("### 📋 Proposed Plan")
                    st.markdown(st.session_state.plan)"""
app_code = app_code.replace(rejected_old, rejected_new)

# 4. Fix the Plan Card HTML rendering in `running`
running_old = """            # ── RUNNING ──
            elif stage == "running":
                st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="plan-card"><div class="plan-hdr"><div class="plan-title">📋 Approved Plan</div></div><div class="plan-body">{st.session_state.plan}</div></div>', unsafe_allow_html=True)"""
running_new = """            # ── RUNNING ──
            elif stage == "running":
                st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("### 📋 Approved Plan")
                    st.markdown(st.session_state.plan)"""
app_code = app_code.replace(running_old, running_new)

# 5. Fix the Plan Card HTML rendering in `done`
done_old = """            # ── DONE ──
            elif stage == "done":
                st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="plan-card"><div class="plan-hdr"><div class="plan-title">📋 Approved Plan</div></div><div class="plan-body">{st.session_state.plan}</div></div>', unsafe_allow_html=True)"""
done_new = """            # ── DONE ──
            elif stage == "done":
                st.markdown(f'<div class="task-title">{st.session_state.task}</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("### 📋 Approved Plan")
                    st.markdown(st.session_state.plan)"""
app_code = app_code.replace(done_old, done_new)

with open("app.py", "w") as f:
    f.write(app_code)
