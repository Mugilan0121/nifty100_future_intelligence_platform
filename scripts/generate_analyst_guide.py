"""
Generates docs/analyst_guide.pdf - the Sprint 6 Day 44 analyst guide.

Covers: using the Streamlit screener, navigating each dashboard screen,
generating PDF tearsheets, calling the API with example curl commands,
and troubleshooting common issues.
"""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    ListFlowable, ListItem,
)

OUTPUT_PATH = Path("docs/analyst_guide.pdf")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "GuideTitle", parent=styles["Title"], fontSize=26, spaceAfter=6,
)
subtitle_style = ParagraphStyle(
    "GuideSubtitle", parent=styles["Normal"], fontSize=13,
    textColor=colors.HexColor("#555555"), spaceAfter=24,
)
h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"], fontSize=18, spaceBefore=18, spaceAfter=10,
    textColor=colors.HexColor("#1a3c6e"),
)
h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"], fontSize=13, spaceBefore=12, spaceAfter=6,
    textColor=colors.HexColor("#2c5a8c"),
)
body = ParagraphStyle(
    "Body", parent=styles["Normal"], fontSize=10.5, leading=15, spaceAfter=8,
)
code = ParagraphStyle(
    "Code", parent=styles["Normal"], fontName="Courier", fontSize=9, leading=13,
    backColor=colors.HexColor("#f2f2f2"), borderPadding=6, spaceAfter=10,
    leftIndent=6,
)
caption = ParagraphStyle(
    "Caption", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#777777"),
    spaceAfter=10,
)

story = []

# ---------------------------------------------------------------------
# Cover
# ---------------------------------------------------------------------
story.append(Spacer(1, 2.2 * inch))
story.append(Paragraph("Nifty 100 Future Intelligence Platform", title_style))
story.append(Paragraph("Analyst Guide", subtitle_style))
story.append(Paragraph(
    "A practical guide to the Streamlit dashboard, PDF tearsheets, and REST API — "
    "for analysts using the platform day to day.", body,
))
story.append(Spacer(1, 1.5 * inch))
story.append(Paragraph("Sprint 6 · Day 44 · Version 1.0", caption))
story.append(PageBreak())

# ---------------------------------------------------------------------
# Table of contents (static)
# ---------------------------------------------------------------------
story.append(Paragraph("Contents", h1))
toc_items = [
    "1. Overview",
    "2. Using the Streamlit Screener",
    "3. Navigating the Dashboard",
    "4. Generating PDF Tearsheets",
    "5. Calling the API",
    "6. Troubleshooting",
]
story.append(ListFlowable(
    [ListItem(Paragraph(t, body)) for t in toc_items],
    bulletType="bullet",
))
story.append(PageBreak())

# ---------------------------------------------------------------------
# 1. Overview
# ---------------------------------------------------------------------
story.append(Paragraph("1. Overview", h1))
story.append(Paragraph(
    "The Nifty 100 Future Intelligence Platform covers 92 Nifty 100 listed companies "
    "across ETL, financial ratios, screening, peer benchmarking, sector analytics, "
    "NLP-driven pros/cons, PDF reporting, ML clustering, and a REST API layer.", body,
))
story.append(Paragraph(
    "This guide is written for analysts using the finished platform, not for developers "
    "working on the codebase. It covers three ways to interact with the data:", body,
))
story.append(ListFlowable([
    ListItem(Paragraph("The <b>Streamlit dashboard</b> — an interactive, browser-based UI "
                        "with 8 screens (Home, Profile, Screener, Peers, Trends, Sectors, "
                        "Capital, Reports).", body)),
    ListItem(Paragraph("<b>PDF tearsheets</b> — one-page company summaries and sector/"
                        "portfolio reports, pre-generated for offline use.", body)),
    ListItem(Paragraph("The <b>REST API</b> — a FastAPI server exposing the same "
                        "underlying data programmatically, for anyone building their "
                        "own tools on top of the platform.", body)),
], bulletType="bullet"))
story.append(Paragraph(
    "Data is refreshed by an ETL pipeline that pulls from company annual reports and "
    "consolidates them into a single SQLite database (nifty100.db). All three access "
    "methods above read from this same database, so the numbers you see in the "
    "dashboard, in a tearsheet, and in an API response for the same company and year "
    "should always agree.", body,
))
story.append(PageBreak())

# ---------------------------------------------------------------------
# 2. Streamlit Screener
# ---------------------------------------------------------------------
story.append(Paragraph("2. Using the Streamlit Screener", h1))
story.append(Paragraph(
    "The Screener screen lets you filter all 92 companies against 10 financial metrics "
    "and export the results.", body,
))

story.append(Paragraph("2.1 Quick Presets", h2))
story.append(Paragraph(
    "Six preset buttons sit above the filter sliders. Clicking one instantly sets all "
    "10 sliders to that strategy's thresholds:", body,
))
preset_table_data = [
    ["Preset", "Strategy"],
    ["Quality", "High ROE, low leverage, positive growth"],
    ["Value", "Low P/E and P/B, modest ROE floor"],
    ["Growth", "High revenue and PAT CAGR"],
    ["Dividend", "Meaningful dividend yield floor"],
    ["Debt-Free", "Zero debt-to-equity, ROE floor of 12%"],
    ["Turnaround", "Positive recent revenue growth, wide tolerance elsewhere"],
]
t = Table(preset_table_data, colWidths=[1.4 * inch, 4.6 * inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c6e")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f7f7")]),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
]))
story.append(t)
story.append(Spacer(1, 10))

story.append(Paragraph("2.2 Manual Filtering", h2))
story.append(Paragraph(
    "Any preset can be adjusted afterward using the 10 sidebar sliders: ROE minimum, "
    "D/E maximum, FCF minimum, Revenue CAGR minimum, PAT CAGR minimum, OPM minimum, "
    "P/E maximum, P/B maximum, Dividend Yield minimum, and Interest Coverage minimum. "
    "Two filters have built-in exceptions worth knowing about:", body,
))
story.append(ListFlowable([
    ListItem(Paragraph("The <b>D/E filter</b> automatically excludes Financials-sector "
                        "companies (banks and NBFCs naturally run high leverage as part "
                        "of their business model).", body)),
    ListItem(Paragraph("The <b>Interest Coverage filter</b> automatically passes any "
                        "debt-free company (ICR is undefined when there's no interest "
                        "expense to cover).", body)),
], bulletType="bullet"))

story.append(Paragraph("2.3 Results and Export", h2))
story.append(Paragraph(
    "The results table updates live as you move any slider, sorted by composite "
    "quality score (highest first). A \"Download results as CSV\" button below the "
    "table exports exactly what's shown, including every filter column, for further "
    "analysis in Excel or elsewhere.", body,
))
story.append(PageBreak())

# ---------------------------------------------------------------------
# 3. Navigating the Dashboard
# ---------------------------------------------------------------------
story.append(Paragraph("3. Navigating the Dashboard", h1))
story.append(Paragraph(
    "The sidebar on the left lists all 8 screens. Each is described below.", body,
))

screens = [
    ("Home", "Portfolio-wide overview: sector distribution donut chart, top/bottom "
             "companies by composite quality score, and headline statistics across "
             "all 92 companies."),
    ("Profile", "Search any company by name or ticker to see its profile card, 6 KPI "
                "tiles (ROE, ROCE, Net Profit Margin, D/E, Revenue CAGR, FCF), a "
                "10-year revenue/profit bar chart, a 10-year ROE-vs-ROCE trend line, "
                "and its recorded pros and cons."),
    ("Screener", "The filtering tool described in Section 2."),
    ("Peers", "Compare a company against its peer group average and a designated "
              "benchmark company across multiple metrics, shown as percentile ranks "
              "and radar-style comparisons."),
    ("Trends", "Multi-year trend views across the full company universe or a "
               "selected sector."),
    ("Sectors", "Sector-level aggregates: company counts, median ROE/P-E/D-E per "
                "sector, and drill-down into any sector's constituent companies."),
    ("Capital", "Capital allocation pattern classification per company (e.g. "
                "Reinvestor, Shareholder Returns, Cash Burn) based on operating, "
                "investing, and financing cash flow direction."),
    ("Reports", "Access point for generating and downloading PDF tearsheets and "
                "sector/portfolio summary reports — see Section 4."),
]
for name, desc in screens:
    story.append(Paragraph(name, h2))
    story.append(Paragraph(desc, body))

story.append(Paragraph(
    "All screens read from the same underlying SQLite database, refreshed on a "
    "10-minute cache (screen data) or 24-hour cache (logos and external URL checks), "
    "so numbers stay consistent across screens without needing a page reload for "
    "every click.", body,
))
story.append(PageBreak())

# ---------------------------------------------------------------------
# 4. Generating PDF Tearsheets
# ---------------------------------------------------------------------
story.append(Paragraph("4. Generating PDF Tearsheets", h1))
story.append(Paragraph(
    "Tearsheets are one-page PDF summaries per company, pre-generated and stored in "
    "reports/tearsheets/. There are three ways to obtain one:", body,
))
story.append(Paragraph("4.1 From the Dashboard", h2))
story.append(Paragraph(
    "On the Company Profile screen, look for a tearsheet download option; on the "
    "Reports screen, tearsheets can be generated or re-generated for any company or "
    "in bulk for the full universe.", body,
))
story.append(Paragraph("4.2 From the API", h2))
story.append(Paragraph(
    "GET /api/v1/companies/{ticker}/tearsheet returns the PDF directly as a binary "
    "file download. Example:", body,
))
story.append(Paragraph(
    "curl -o tcs_tearsheet.pdf http://localhost:8000/api/v1/companies/TCS/tearsheet",
    code,
))
story.append(Paragraph("4.3 Bulk Generation (all 92 companies)", h2))
story.append(Paragraph(
    "Run the batch generator directly from the project root:", body,
))
story.append(Paragraph(
    "python src/reports/generate_all_tearsheets.py",
    code,
))
story.append(Paragraph(
    "This regenerates all tearsheets in reports/tearsheets/ from the current database "
    "state — useful after an ETL refresh.", body,
))
story.append(PageBreak())

# ---------------------------------------------------------------------
# 5. Calling the API
# ---------------------------------------------------------------------
story.append(Paragraph("5. Calling the API", h1))
story.append(Paragraph(
    "The API is a FastAPI server. Start it from the project root:", body,
))
story.append(Paragraph("uvicorn src.api.main:app --port 8000", code))
story.append(Paragraph(
    "Interactive documentation (Swagger UI) is available at "
    "http://localhost:8000/docs once the server is running. All endpoints are "
    "prefixed with /api/v1. Below are example curl commands for the most commonly "
    "used endpoints.", body,
))

api_examples = [
    ("Health check", "curl http://localhost:8000/api/v1/health"),
    ("List all companies", "curl http://localhost:8000/api/v1/companies"),
    ("Filter companies by sector",
     'curl "http://localhost:8000/api/v1/companies?sector=Information Technology"'),
    ("Full company profile",
     "curl http://localhost:8000/api/v1/companies/TCS"),
    ("Company P&L history",
     "curl http://localhost:8000/api/v1/companies/TCS/pl"),
    ("Company ratios, single year",
     'curl "http://localhost:8000/api/v1/companies/TCS/ratios?year=2024"'),
    ("Screener with filters",
     'curl "http://localhost:8000/api/v1/screener?min_roe=15&max_de=1.0"'),
    ("Sector list", "curl http://localhost:8000/api/v1/sectors"),
    ("Companies in a sector",
     'curl "http://localhost:8000/api/v1/sectors/Information Technology/companies"'),
    ("Peer group comparison",
     "curl http://localhost:8000/api/v1/companies/TCS/peers/compare"),
    ("Historical valuation multiples",
     "curl http://localhost:8000/api/v1/market-cap/TCS"),
    ("Portfolio-wide percentile stats",
     "curl http://localhost:8000/api/v1/portfolio/stats"),
    ("Annual report document links",
     "curl http://localhost:8000/api/v1/companies/TCS/documents"),
    ("Download tearsheet PDF",
     "curl -o tcs_tearsheet.pdf http://localhost:8000/api/v1/companies/TCS/tearsheet"),
]
for label, cmd in api_examples:
    story.append(Paragraph(label, h2))
    story.append(Paragraph(cmd, code))

story.append(Paragraph(
    "All ticker lookups are case-insensitive (the API normalizes to uppercase "
    "internally) and return HTTP 404 with a JSON error body if the ticker, sector, "
    "or peer group is not found.", body,
))
story.append(PageBreak())

# ---------------------------------------------------------------------
# 6. Troubleshooting
# ---------------------------------------------------------------------
story.append(Paragraph("6. Troubleshooting Common Issues", h1))

issues = [
    ("Dashboard shows \"No financial ratio data found\"",
     "The ETL pipeline hasn't been run yet, or nifty100.db is missing/empty. Run "
     "python src/etl/loader.py from the project root, then restart the Streamlit app."),
    ("A company logo doesn't load on the Profile screen",
     "Logos are fetched live from an external URL on first view and cached for 24 "
     "hours. If the source URL is slow, temporarily unreachable, or the file isn't "
     "an image, the platform falls back to a generic building icon rather than "
     "erroring — this is expected behavior, not a bug."),
    ("A company's ROE or ROCE shows as \"N/A*\"",
     "A small number of companies (currently Bharat Electronics and Hindustan "
     "Aeronautics) have known data-quality issues in their source ratio calculations "
     "that produce implausible values (thousands of percent). These are intentionally "
     "suppressed at the display layer with an N/A* label and a +/-200% sanity guard, "
     "rather than silently showing an incorrect number."),
    ("API returns HTTP 404 for a ticker I know exists",
     "Confirm the ticker matches the id column in the companies table exactly "
     "(case-insensitive) — the API has no separate \"ticker\" field, company id IS "
     "the ticker. Use GET /api/v1/companies?search=<partial name> to look it up."),
    ("API returns HTTP 400 on a screener request",
     "One or more query parameters were out of a plausible range (e.g. a deeply "
     "negative max_de or an implausibly large min_roe). Check the parameter values "
     "against the ranges shown in the Streamlit Screener's sliders as a sanity check."),
    ("Streamlit shows stale data after an ETL re-run",
     "Dashboard data is cached for 10 minutes (financial data) or 24 hours (logos/"
     "URL checks) via @st.cache_data. If you've just re-run the ETL pipeline, a full "
     "server restart clears the cache immediately; changes to shared utils/ modules "
     "specifically require a restart rather than a browser refresh."),
    ("FastAPI and Streamlit both need to run at once",
     "They use separate ports (8000 and 8501 respectively) and do not conflict. "
     "Start each in its own terminal: uvicorn src.api.main:app --port 8000 and "
     "streamlit run src/dashboard/app.py --server.port 8501."),
    ("A sector count of 10 instead of an expected 11",
     "The database contains 10 distinct sectors, not 11. This was verified directly "
     "against the sectors table and is reflected consistently across the dashboard, "
     "the API, and the test suite."),
]
for problem, solution in issues:
    story.append(Paragraph(problem, h2))
    story.append(Paragraph(solution, body))

story.append(Spacer(1, 20))
story.append(Paragraph(
    "For issues not covered here, check output/perf_notes.md for known performance "
    "characteristics, or output/validation_failures.csv for known data-quality flags "
    "raised by the automated DQ rule checks.", caption,
))

doc = SimpleDocTemplate(
    str(OUTPUT_PATH), pagesize=letter,
    topMargin=0.85 * inch, bottomMargin=0.85 * inch,
    leftMargin=0.9 * inch, rightMargin=0.9 * inch,
)
doc.build(story)

print(f"Generated: {OUTPUT_PATH.resolve()}")