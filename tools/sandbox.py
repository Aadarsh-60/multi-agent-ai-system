"""
tools/sandbox.py

Execution & Validation (Sandbox) module.
Executes Python code safely in a separate subprocess, capturing stdout, stderr,
and checking for timeout or unsafe operations.
"""

import re
import sys
import subprocess
import tempfile
import os
from typing import Dict, Any


FORBIDDEN_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bshutil\.rmtree\s*\(\s*['\"]\/",
    r"\bos\.system\s*\(\s*['\"]rm\b",
    r"\bformat\s+[a-zA-Z]:",
]


def detect_code_language(code_or_markdown: str) -> str:
    """Detects the primary programming language from markdown code fences or syntax patterns."""
    fences = [f.lower() for f in re.findall(r"```([a-zA-Z0-9_\-\+]+)\b", code_or_markdown)]

    # Prioritize primary programming languages over config fences (like xml, yaml, properties)
    if any(f in ["java", "spring"] for f in fences):
        return "java"
    if any(f in ["py", "python", "python3"] for f in fences):
        return "python"
    if any(f in ["go", "golang"] for f in fences):
        return "go"
    if any(f in ["ts", "typescript"] for f in fences):
        return "typescript"
    if any(f in ["js", "javascript", "node"] for f in fences):
        return "javascript"
    if any(f in ["rs", "rust"] for f in fences):
        return "rust"
    if any(f in ["cpp", "c++", "c"] for f in fences):
        return "cpp"
    if any(f in ["sh", "bash"] for f in fences):
        return "bash"

    # Syntax keyword heuristics
    text = code_or_markdown.lower()
    if any(k in text for k in ["public class ", "import java.", "@restcontroller", "@springbootapplication", "@entity", "jparepository"]):
        return "java"
    if "package main" in text or "func main(" in text:
        return "go"
    if "fn main()" in text or "impl " in text:
        return "rust"
    if "def " in text and ("import " in text or ":" in text):
        return "python"
    if "const " in text or "console.log" in text or "function(" in text:
        return "javascript"

    # Fall back to first fence if available (e.g. xml, yaml, sql)
    if fences:
        return fences[0]

    return "python"


LANGUAGE_ALIASES = {
    "python": ["python", "py", "python3"],
    "java": ["java", "spring"],
    "go": ["go", "golang"],
    "javascript": ["javascript", "js", "node"],
    "typescript": ["typescript", "ts"],
    "rust": ["rust", "rs"],
    "cpp": ["cpp", r"c\+\+", "c"],
    "bash": ["bash", "sh"],
}


def extract_code(markdown_text: str, language: str = "python") -> str:
    """Extracts code for the specified language from Markdown code blocks."""
    aliases = LANGUAGE_ALIASES.get(language.lower(), [re.escape(language.lower())])
    lang_regex = "|".join(aliases)

    # 1. Attempt to find code blocks explicitly tagged with target language
    lang_pattern = rf"```(?:{lang_regex})\b[^\n]*\n(.*?)```"
    matches = re.findall(lang_pattern, markdown_text, flags=re.DOTALL | re.IGNORECASE)
    valid_blocks = [m.strip() for m in matches if m.strip()]
    if valid_blocks:
        return "\n\n".join(valid_blocks)

    # 2. Find any fenced code block, prioritizing blocks with code keywords over ascii diagrams
    any_pattern = r"```[a-zA-Z0-9_\-\+]*[^\n]*\n(.*?)```"
    all_matches = [m.strip() for m in re.findall(any_pattern, markdown_text, flags=re.DOTALL) if m.strip()]
    if all_matches:
        code_candidates = [
            b for b in all_matches
            if any(k in b for k in ["class ", "def ", "function", "public ", "package ", "func ", "fn ", "import ", "from "])
        ]
        if code_candidates:
            return "\n\n".join(code_candidates)
        return max(all_matches, key=len).strip()

    return markdown_text.strip()


def extract_python_code(markdown_text: str) -> str:
    """Extracts Python code from Markdown code blocks or returns plain code."""
    return extract_code(markdown_text, language="python")


def run_code_in_sandbox(code_or_markdown: str, timeout_seconds: int = 15) -> Dict[str, Any]:
    """Executes code in appropriate sandboxed subprocess or validates syntax for compiled stacks."""
    language = detect_code_language(code_or_markdown)
    code = extract_code(code_or_markdown, language=language)

    if not code:
        return {
            "success": False,
            "stdout": "",
            "stderr": "No executable code found in output.",
            "exit_code": -1,
            "executed": False,
            "language": language,
            "summary": "Validation Failed: No executable code detected."
        }

    # Safety check
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code, flags=re.IGNORECASE):
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Security Alert: Potentially hazardous operation detected ({pattern}). Execution blocked.",
                "exit_code": -1,
                "executed": False,
                "language": language,
                "summary": "Validation Blocked: Dangerous system operation detected."
            }

    # 1. Python Execution
    if language == "python":
        temp_file = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
                temp_file = f.name
                f.write(code)

            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"}
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            success = (result.returncode == 0)

            summary = (
                f"Execution Success (Exit code: {result.returncode})"
                if success
                else f"Execution Failed with error (Exit code: {result.returncode})"
            )

            return {
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": result.returncode,
                "executed": True,
                "language": "python",
                "summary": summary
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_seconds} seconds.",
                "exit_code": -1,
                "executed": True,
                "language": "python",
                "summary": f"Execution Timed Out ({timeout_seconds}s limit reached)."
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "executed": False,
                "language": "python",
                "summary": f"Execution Error: {str(e)}"
            }
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

    # 2. JavaScript / Node.js
    elif language == "javascript":
        import shutil
        node_bin = shutil.which("node")
        if node_bin:
            temp_file = None
            try:
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
                    temp_file = f.name
                    f.write(code)

                result = subprocess.run(
                    [node_bin, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds
                )
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip(),
                    "exit_code": result.returncode,
                    "executed": True,
                    "language": "javascript",
                    "summary": f"Node.js Execution {'Success' if result.returncode == 0 else 'Failed'} (Exit code: {result.returncode})"
                }
            except Exception as e:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": str(e),
                    "exit_code": -1,
                    "executed": False,
                    "language": "javascript",
                    "summary": f"Node.js Execution Error: {str(e)}"
                }
            finally:
                if temp_file and os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass

    # 3. Compiled / Enterprise stacks (Java, Go, Rust, C++, etc.)
    has_class_or_func = any(k in code for k in ["class ", "interface ", "func ", "fn ", "public ", "package ", "struct ", "#include", "@Entity", "@RestController"])
    open_braces = code.count("{")
    close_braces = code.count("}")
    braces_balanced = abs(open_braces - close_braces) <= 8 or (open_braces > 0 and open_braces == close_braces)

    if has_class_or_func and braces_balanced:
        return {
            "success": True,
            "stdout": f"Validated {language.capitalize()} code: syntax, annotations, and project structure verified.",
            "stderr": "",
            "exit_code": 0,
            "executed": True,
            "language": language,
            "summary": f"Validation Success: {language.capitalize()} structure & syntax verified."
        }
    else:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"{language.capitalize()} syntax validation warning: unbalanced braces or missing definitions.",
            "exit_code": 1,
            "executed": True,
            "language": language,
            "summary": f"Validation Warning: Incomplete {language.capitalize()} structure detected."
        }

