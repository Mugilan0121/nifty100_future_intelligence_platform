# Sprint 5 Retrospective

## Sprint Goal

Auto-generate pros and cons with confidence scores for all 92 companies, classify every company by CFO quality, CapEx intensity, and capital allocation pattern, and produce 92 company tearsheet PDFs plus sector and portfolio summary reports — all without text overflow or layout errors.

---

## What Went Well

- Built `src/nlp/parser.py`, correctly identifying that the `analysis` table stores one row per (company, period) rather than multi-period text packed into a single cell, and parsed all 4 target fields into `output/analysis_parsed.csv`.
- Built `src/nlp/pros_cons_generator.py` implementing all 24 pro/con rules with a documented confidence heuristic, plus fallback rules so every one of the 92 companies has at least 1 pro and 1 con — verified via an automated coverage check.
- Extended the existing Sprint 2 `cashflow_kpis.py` (rather than rebuilding it) with CFO quality scoring, CapEx intensity, distress signal detection, and deleveraging flags, generating `output/cashflow_intelligence.xlsx` (92 rows) and `output/distress_alerts.csv` (13 flagged companies).
- Investigated and fully resolved the `capital_allocation.csv` 100-vs-92 company discrepancy: found and fixed a genuine ticker typo (AGTL → ATGL) and correctly identified 8 other tickers as a Sprint 1 scope mismatch between the companies metadata source and the financial-statement source files, rather than a bug to chase.
- Built `src/reports/tearsheet.py`, a full 2-page ReportLab tearsheet with matplotlib-rendered charts, wordwrapped tables, and a capital allocation badge — tested on 5 sector-diverse companies before batch generation, per the sprint plan's own risk-mitigation step.
- Successfully batch-generated 89/92 tearsheets, 10/10 sector PDFs, and a 90-page portfolio summary with trend arrows, all meeting the size and layout exit criteria.

---

## Challenges Faced

- The `cashflow` table's year format (`"Mar-13"`) differs from every other table's format (`"Mar 2013"`) — required a flexible year parser to align data across tables for CFO/CFF-based calculations.
- Two spec ambiguities required documented judgment calls rather than guesses: Pro Rule 11's header and rule text described opposite conditions (implemented per the text), and the portfolio summary's "trend arrow" and "flat within 2%" logic weren't fully specified (documented per-metric direction and threshold assumptions, including inverting D/E since lower leverage is the improvement).
- Discovered a serious pre-existing data bug while spot-checking the Industrials sector report: `financial_ratios` ROE and ROCE values are corrupted for BEL and HAL (values in the thousands of percent instead of the correct ~26-29% shown on the `companies` table), traced to Sprint 2's ratio population engine. This likely already skewed Day 30's pros/cons output and earlier sprints' screener/composite scores for these two companies — flagged for the team lead rather than silently patched mid-sprint.
- A None-vs-NaN dtype inconsistency in `financial_ratios` (PNB) broke the new ROE/ROCE sanity guard with a `TypeError` on first batch run — required coercing to numeric before applying the guard.

---

## Improvements for Next Sprint

- Investigate and properly fix the BEL/HAL `financial_ratios` ROE/ROCE calculation bug at the source, and audit whether any other companies have similarly implausible values that haven't yet been spot-checked.
- Re-run Day 30's pros/cons generator and Sprint 3-4's screener/composite scoring after that fix, since BEL and HAL likely have fabricated "high ROE" signals baked into existing outputs.
- Standardize year formats across all raw tables during ETL, or centralize the flexible year parser into a shared utility, rather than re-implementing it in each Day 30-35 script.
- Consider a lightweight automated sanity-check pass (implausible-value detection) as a standing step after any new ratio calculation, rather than relying on visual spot-checks to catch it.

---

## Sprint Outcome

Sprint 5 completed successfully.

- `pros_cons_generated.csv` has at least 1 pro and 1 con for all 92 companies (verified).
- 89 of 92 tearsheets generated, all ≥30 KB (3 companies — ATGL, JIOFIN, SBIN — correctly skipped for insufficient underlying data).
- Visual review of 5+ tearsheets and sector reports confirmed no text overflow or blank pages.
- `cashflow_intelligence.xlsx` has 92 rows with all required columns.
- A real cross-sprint data-quality bug (BEL/HAL ROE/ROCE) was caught, contained at the display layer, and documented for proper resolution rather than shipped silently.
- Ready for Sprint 6, pending team lead sign-off on the BEL/HAL data-quality finding.