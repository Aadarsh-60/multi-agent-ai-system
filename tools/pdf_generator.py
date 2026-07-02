"""
tools/pdf_generator.py

Generates a PDF from a given text (markdown/report).
Uses fpdf2 library.
"""

from fpdf import FPDF


def _sanitize_text(text: str) -> str:
    """Convert report text to something the default PDF font can render."""
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "".join(ch if ord(ch) < 256 else "?" for ch in text)


def generate_pdf(report_text: str) -> bytes:
    """
    Takes the final report text and generates a PDF in-memory,
    returning the raw bytes which can be downloaded in Streamlit.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=12)

    safe_text = _sanitize_text(report_text or "")

    for line in safe_text.split("\n"):
        if not line.strip():
            pdf.ln(1)
            continue

        try:
            if line.startswith("# "):
                pdf.set_font("Helvetica", "B", 16)
                pdf.multi_cell(0, 10, text=line.replace("# ", ""))
                pdf.ln(2)
                pdf.set_font("Helvetica", size=12)
            elif line.startswith("## "):
                pdf.set_font("Helvetica", "B", 14)
                pdf.multi_cell(0, 10, text=line.replace("## ", ""))
                pdf.ln(2)
                pdf.set_font("Helvetica", size=12)
            elif line.startswith("### "):
                pdf.set_font("Helvetica", "B", 12)
                pdf.multi_cell(0, 8, text=line.replace("### ", ""))
                pdf.ln(1)
                pdf.set_font("Helvetica", size=12)
            else:
                pdf.multi_cell(0, 6, text=line)
        except Exception:
            fallback_line = line.encode("latin-1", "replace").decode("latin-1")
            try:
                pdf.multi_cell(0, 6, text=fallback_line or " ")
            except Exception:
                # Fallback for extremely long strings (like URLs/tracebacks) that exceed page width
                import textwrap
                wrapped = textwrap.wrap(fallback_line, width=80, break_long_words=True)
                for w_line in wrapped:
                    try:
                        pdf.multi_cell(0, 6, text=w_line)
                    except Exception:
                        pass

    return bytes(pdf.output(dest="S"))
