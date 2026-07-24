"""
Scans src/ for public functions/methods missing a docstring.

Sprint 6 - Day 44

"Public" = doesn't start with underscore. Reports file, line number,
and function name for anything missing one.
"""

import ast
from pathlib import Path

SRC_ROOT = Path("src")


def check_file(path: Path):
    missing = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as e:
        print(f"SYNTAX ERROR in {path}: {e}")
        return missing

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            docstring = ast.get_docstring(node)
            if not docstring:
                missing.append((path, node.lineno, node.name))
    return missing


def main():
    all_missing = []
    for py_file in sorted(SRC_ROOT.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        all_missing.extend(check_file(py_file))

    if not all_missing:
        print("All public functions have docstrings.")
        return

    print(f"Found {len(all_missing)} public function(s) missing a docstring:\n")
    for path, lineno, name in all_missing:
        print(f"  {path}:{lineno}  {name}()")


if __name__ == "__main__":
    main()