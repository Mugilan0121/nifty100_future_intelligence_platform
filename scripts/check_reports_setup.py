from pathlib import Path
import importlib.util

PROJECT_ROOT = Path(__file__).resolve().parents[1]

print("=== Files in src/reports/ ===")
reports_dir = PROJECT_ROOT / "src" / "reports"
if reports_dir.exists():
    for f in sorted(reports_dir.rglob("*")):
        print(f" - {f.relative_to(reports_dir)}")
else:
    print("src/reports/ not found")

print("\n=== Package availability ===")
for pkg in ["reportlab", "matplotlib", "openpyxl", "plotly", "kaleido"]:
    spec = importlib.util.find_spec(pkg)
    print(f"{pkg}: {'available' if spec else 'NOT installed'}")

print("\n=== requirements.txt ===")
req_path = PROJECT_ROOT / "requirements.txt"
if req_path.exists():
    print(req_path.read_text())