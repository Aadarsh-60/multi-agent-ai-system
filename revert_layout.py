with open("app.py", "r") as f:
    code = f.read()

# I need to change:
# if stage != 'idle':
#     with bottom_container:
#         st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
#         _, center_col, _ = st.columns([1.5, 5, 1.5])
#         with center_col:
#             # ── PLANNING ──
# To:
#     # ── PLANNING ──

# First, let's locate the block
old_block = """if stage != 'idle':
    with bottom_container:
        st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
        _, center_col, _ = st.columns([1.5, 5, 1.5])
        with center_col:"""

new_block = """with left_col_container:"""

code = code.replace(old_block, new_block)

# Now, we need to unindent everything from line 228 to the end of the file by 8 spaces (since we are replacing 3 levels of indentation with 1).
# Actually, `with left_col_container:` is at the root level, so we just unindent by 8 spaces.
lines = code.split("\n")
new_lines = []
in_stages = False
for line in lines:
    if "with left_col_container:" in line and "st.columns([1.5, 5, 1.5])" not in line: # Only our new block
        # Wait, the first `with left_col_container:` is at line 186:
        pass
        
# Let's just use string replacement for the exact prefix
# Since it's easier, let's do the indentation fix safely:

# Instead of doing it line by line, let's just write a smart script
with open("app.py", "r") as f:
    lines = f.readlines()

new_lines = []
inside_center_col = False
for i, line in enumerate(lines):
    if line.strip() == "if stage != 'idle':":
        inside_center_col = True
        new_lines.append("with left_col_container:\n")
        continue
    
    if inside_center_col:
        if line.strip() == "with bottom_container:" or line.strip() == 'st.markdown("<div style=\'height:32px\'></div>", unsafe_allow_html=True)' or "center_col, _ = st.columns(" in line or line.strip() == "with center_col:":
            continue # skip these lines
            
        # Unindent by 8 spaces
        if line.startswith("            "):
            new_lines.append(line[8:])
        elif line.startswith("        "):
            new_lines.append(line[4:])
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open("app.py", "w") as f:
    f.writelines(new_lines)
