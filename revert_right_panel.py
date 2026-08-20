with open("app.py", "r") as f:
    app_code = f.read()

# 1. Remove the pipeline from sidebar
sidebar_old = """# ── SIDEBAR ──
with st.sidebar:
    st.markdown("## ⚙️ Agent Pipeline")
    pipeline_placeholder = st.empty()
    
    st.markdown("---")
    st.markdown("## 💬 Chat with Agents")"""

sidebar_new = """# ── SIDEBAR ──
with st.sidebar:
    st.markdown("## 💬 Chat with Agents")"""

app_code = app_code.replace(sidebar_old, sidebar_new)

# 2. Add the pipeline back to the main area right column
layout_old = """# --- LAYOUT SETUP ---
# Initialize sidebar pipeline
pipeline_placeholder.markdown(render_vertical_pipeline(), unsafe_allow_html=True)

def update_pipeline_ui():
    pipeline_placeholder.markdown(render_vertical_pipeline(), unsafe_allow_html=True)

_, center_col, _ = st.columns([1.5, 6, 1.5])
left_col_container = center_col.container()
bottom_container = center_col.container()"""

layout_new = """# --- LAYOUT SETUP ---
col_left, col_right = st.columns([2, 1], gap="large")

with col_right:
    pipeline_placeholder = st.empty()
    pipeline_placeholder.markdown(render_vertical_pipeline(), unsafe_allow_html=True)

def update_pipeline_ui():
    pipeline_placeholder.markdown(render_vertical_pipeline(), unsafe_allow_html=True)

left_col_container = col_left.container()
bottom_container = col_left.container()"""

app_code = app_code.replace(layout_old, layout_new)

with open("app.py", "w") as f:
    f.write(app_code)
