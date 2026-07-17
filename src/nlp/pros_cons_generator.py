"""
Day 30 — NLP: Auto Pros/Cons Generator

Implements 12 pro rules and 12 con rules against financial_ratios,
balancesheet, and profitandloss, assigning a 0-100 confidence score
per triggered rule. Only rules with confidence > 60 are included in
the output.

Known data-model notes (see chat for full context):
  - Pro Rule 11 is implemented per the rule TEXT ("revenue growing
    slower than profits" = PAT CAGR > Revenue CAGR), not the literal
    header condition, which stated the reverse. Flagged as a spec
    conflict — swap swap_pro_11_direction() if the header was intended.
  - Con Rule 11 "Net Debt" is approximated as gross total_debt_cr,
    since balancesheet has no dedicated cash/bank balance column to
    net against. Labelled as gross debt in the output text.
  - cashflow table's year format ("Mar-13") differs from every other
    table ("Mar 2013") — irrelevant here since FCF trend rules use
    financial_ratios.free_cash_flow_cr instead of raw cashflow, but
    will matter for Day 31's direct cashflow-table work.
  - Confidence scoring is a documented heuristic (not spec'd exactly):
    60 base + up to 30 for margin beyond threshold + up to 10 for
    streak strength, capped at 100.

Outputs:
    output/pros_cons_generated.csv — company_id, type, rule_id, text, confidence_pct
    output/pros_cons_coverage_check.csv — companies missing a pro and/or a con (should be empty)
"""

import sqlite3
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

CONFIDENCE_THRESHOLD = 60


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def year_num(y):
    """Extracts the 4-digit year from formats like 'Mar 2013' or 'Dec 2012'.
    Returns None (instead of raising) for malformed year values, so one
    corrupt row doesn't crash the whole run."""
    try:
        return int(str(y).strip()[-4:])
    except ValueError:
        return None


def confidence_from_margin(value, threshold, direction="above", streak_extra=0):
    """
    Heuristic confidence: 60 base + up to 30 scaled by how far the value
    clears the threshold + up to 10 for streak strength beyond the minimum.
    """
    if threshold == 0:
        ratio = 1.0 if (direction == "above" and value > 0) or (direction == "below" and value < 0) else 0.0
    else:
        if direction == "above":
            ratio = (value - threshold) / abs(threshold)
        else:
            ratio = (threshold - value) / abs(threshold)
    ratio = max(0.0, min(ratio, 1.0))
    conf = 60 + ratio * 30 + min(10, streak_extra * 5)
    return round(min(conf, 100), 1)


# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------

def load_data(conn):
    ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    market_cap = pd.read_sql_query("SELECT company_id, year, dividend_yield_pct FROM market_cap", conn)
    companies = pd.read_sql_query(
        "SELECT id AS company_id, roe_percentage, roce_percentage FROM companies", conn
    )

    for name, df in (("financial_ratios", ratios), ("balancesheet", bs), ("profitandloss", pl)):
        df["year_num"] = df["year"].apply(year_num)
        bad_rows = df[df["year_num"].isna()]
        if not bad_rows.empty:
            print(f"NOTE: {len(bad_rows)} row(s) in {name} are non-annual or malformed (TTM/stub-period/bad year) — excluded from trend rules:")
            print(bad_rows[["company_id", "year"]].drop_duplicates().to_string(index=False))
        df.dropna(subset=["year_num"], inplace=True)
        df["year_num"] = df["year_num"].astype(int)
        df.sort_values(["company_id", "year_num"], inplace=True)

    return ratios, bs, pl, sectors, market_cap, companies


# ---------------------------------------------------------------------
# Rule evaluation — one function per rule, returns (triggered, confidence, text) or None
# ---------------------------------------------------------------------

def evaluate_rules(company_id, ratios_hist, bs_hist, pl_hist, sector, div_yield_latest):
    results = []

    if ratios_hist.empty:
        return results

    latest = ratios_hist.iloc[-1]
    pl_latest = pl_hist.iloc[-1] if not pl_hist.empty else None
    bs_latest = bs_hist.iloc[-1] if not bs_hist.empty else None

    def add(rule_id, rule_type, triggered, confidence, text):
        if triggered and confidence > CONFIDENCE_THRESHOLD:
            results.append(
                {
                    "company_id": company_id,
                    "type": rule_type,
                    "rule_id": rule_id,
                    "text": text,
                    "confidence_pct": confidence,
                }
            )

    # ---------------- PRO RULES ----------------

    # Pro 1: ROE > 20% sustained for 3+ years
    roe_last3 = ratios_hist["return_on_equity_pct"].tail(3)
    if len(roe_last3) == 3 and roe_last3.notna().all() and (roe_last3 > 20).all():
        conf = confidence_from_margin(roe_last3.mean(), 20, "above")
        add("pro_1", "pro", True, conf,
            "Consistently high return on equity above 20% demonstrates exceptional capital efficiency")

    # Pro 2: FCF positive for 5+ consecutive years
    fcf_last5 = ratios_hist["free_cash_flow_cr"].tail(5)
    if len(fcf_last5) == 5 and fcf_last5.notna().all() and (fcf_last5 > 0).all():
        conf = confidence_from_margin(fcf_last5.min(), 0, "above", streak_extra=1)
        add("pro_2", "pro", True, conf,
            "Strong free cash flow generation over 5 years signals healthy business fundamentals")

    # Pro 3: D/E = 0 in latest year
    if pd.notna(latest["debt_to_equity"]) and latest["debt_to_equity"] == 0:
        add("pro_3", "pro", True, 90.0,
            "Debt-free balance sheet provides financial flexibility and eliminates interest burden")

    # Pro 4: Revenue CAGR > 15% over 5 years
    if pd.notna(latest["revenue_cagr_5yr"]) and latest["revenue_cagr_5yr"] > 15:
        conf = confidence_from_margin(latest["revenue_cagr_5yr"], 15, "above")
        add("pro_4", "pro", True, conf,
            "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum")

    # Pro 5: OPM > 25% in latest year
    if pd.notna(latest["operating_profit_margin_pct"]) and latest["operating_profit_margin_pct"] > 25:
        conf = confidence_from_margin(latest["operating_profit_margin_pct"], 25, "above")
        add("pro_5", "pro", True, conf,
            "Operating profit margin above 25% indicates strong pricing power and cost discipline")

    # Pro 6: PAT CAGR > 20% over 5 years
    if pd.notna(latest["pat_cagr_5yr"]) and latest["pat_cagr_5yr"] > 20:
        conf = confidence_from_margin(latest["pat_cagr_5yr"], 20, "above")
        add("pro_6", "pro", True, conf,
            "Net profit compounding at above 20% over 5 years creates significant shareholder value")

    # Pro 7: ICR > 10 or Debt Free
    debt_free = pd.notna(latest["total_debt_cr"]) and latest["total_debt_cr"] == 0
    icr_high = pd.notna(latest["interest_coverage"]) and latest["interest_coverage"] > 10
    if debt_free or icr_high:
        conf = 90.0 if debt_free else confidence_from_margin(latest["interest_coverage"], 10, "above")
        add("pro_7", "pro", True, conf,
            "Very high interest coverage ratio reflects negligible financial stress from debt servicing")

    # Pro 8: Dividend Yield > 2% with FCF positive
    fcf_latest = latest["free_cash_flow_cr"]
    if div_yield_latest is not None and pd.notna(div_yield_latest) and div_yield_latest > 2 \
            and pd.notna(fcf_latest) and fcf_latest > 0:
        conf = confidence_from_margin(div_yield_latest, 2, "above")
        add("pro_8", "pro", True, conf,
            "Consistent dividend yield above 2% backed by positive free cash flow")

    # Pro 9: EPS CAGR > 15% over 5 years
    if pd.notna(latest["eps_cagr_5yr"]) and latest["eps_cagr_5yr"] > 15:
        conf = confidence_from_margin(latest["eps_cagr_5yr"], 15, "above")
        add("pro_9", "pro", True, conf,
            "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding")

    # Pro 10: ROE improving for 3 consecutive years
    roe3 = ratios_hist["return_on_equity_pct"].tail(3).tolist()
    if len(roe3) == 3 and all(pd.notna(v) for v in roe3) and roe3[0] < roe3[1] < roe3[2]:
        conf = confidence_from_margin(roe3[2] - roe3[0], 0, "above", streak_extra=1)
        add("pro_10", "pro", True, conf,
            "Return on equity improving for 3 consecutive years shows strengthening business quality")

    # Pro 11: implemented per rule TEXT — PAT CAGR > Revenue CAGR (operating leverage)
    # (header literally said Revenue CAGR > PAT CAGR; text described the opposite — see module docstring)
    if pd.notna(latest["pat_cagr_5yr"]) and pd.notna(latest["revenue_cagr_5yr"]) \
            and latest["pat_cagr_5yr"] > latest["revenue_cagr_5yr"]:
        conf = confidence_from_margin(latest["pat_cagr_5yr"] - latest["revenue_cagr_5yr"], 0, "above")
        add("pro_11", "pro", True, conf,
            "Revenue growing slower than profits shows improving operating leverage and scale benefits")

    # Pro 12: Balance sheet assets growing with declining debt
    if len(bs_hist) >= 2:
        bs_last2 = bs_hist.tail(2)
        assets_growing = bs_last2["total_assets"].iloc[-1] > bs_last2["total_assets"].iloc[0]
        debt_declining = bs_last2["borrowings"].iloc[-1] < bs_last2["borrowings"].iloc[0]
        if assets_growing and debt_declining:
            asset_growth_pct = (bs_last2["total_assets"].iloc[-1] / max(bs_last2["total_assets"].iloc[0], 1) - 1) * 100
            conf = confidence_from_margin(asset_growth_pct, 0, "above")
            add("pro_12", "pro", True, conf,
                "Growing asset base funded by internal accruals reflects self-sustaining growth")

    # ---------------- CON RULES ----------------

    is_financial_sector = isinstance(sector, str) and "financial" in sector.lower()

    # Con 1: D/E > 2.0 for non-financial companies
    if not is_financial_sector and pd.notna(latest["debt_to_equity"]) and latest["debt_to_equity"] > 2.0:
        conf = confidence_from_margin(latest["debt_to_equity"], 2.0, "above")
        add("con_1", "con", True, conf,
            f"Debt-to-equity ratio of {latest['debt_to_equity']:.2f} is elevated for a non-financial company and warrants monitoring")

    # Con 2: FCF negative for 3 consecutive years
    fcf_last3 = ratios_hist["free_cash_flow_cr"].tail(3)
    if len(fcf_last3) == 3 and fcf_last3.notna().all() and (fcf_last3 < 0).all():
        conf = confidence_from_margin(fcf_last3.mean(), 0, "below", streak_extra=1)
        add("con_2", "con", True, conf,
            "Free cash flow negative for 3 consecutive years raises concern about cash generation quality")

    # Con 3: OPM declining for 3 consecutive years
    opm3 = ratios_hist["operating_profit_margin_pct"].tail(3).tolist()
    if len(opm3) == 3 and all(pd.notna(v) for v in opm3) and opm3[0] > opm3[1] > opm3[2]:
        conf = confidence_from_margin(opm3[0] - opm3[2], 0, "above")
        add("con_3", "con", True, conf,
            "Operating margins declining for 3 consecutive years suggest pricing or cost pressure")

    # Con 4: Net profit negative in latest year
    if pl_latest is not None and pd.notna(pl_latest["net_profit"]) and pl_latest["net_profit"] < 0:
        add("con_4", "con", True, 90.0, "Company reported a net loss in the most recent financial year")

    # Con 5: Revenue declining for 2+ years (2 consecutive YoY declines, needs 3 data points)
    sales3 = pl_hist["sales"].tail(3).tolist()
    if len(sales3) == 3 and all(pd.notna(v) for v in sales3) and sales3[0] > sales3[1] > sales3[2]:
        conf = confidence_from_margin(sales3[0] - sales3[2], 0, "above")
        add("con_5", "con", True, conf,
            "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss")

    # Con 6: ICR < 1.5 (only meaningful if company carries debt)
    has_debt = pd.notna(latest["total_debt_cr"]) and latest["total_debt_cr"] > 0
    if has_debt and pd.notna(latest["interest_coverage"]) and latest["interest_coverage"] < 1.5:
        conf = confidence_from_margin(latest["interest_coverage"], 1.5, "below")
        add("con_6", "con", True, conf,
            "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations")

    # Con 7: Dividend payout > 100%
    if pd.notna(latest["dividend_payout_ratio_pct"]) and latest["dividend_payout_ratio_pct"] > 100:
        conf = confidence_from_margin(latest["dividend_payout_ratio_pct"], 100, "above")
        add("con_7", "con", True, conf,
            "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable")

    # Con 8: D/E rising for 3 consecutive years
    de3 = ratios_hist["debt_to_equity"].tail(3).tolist()
    if len(de3) == 3 and all(pd.notna(v) for v in de3) and de3[0] < de3[1] < de3[2]:
        conf = confidence_from_margin(de3[2] - de3[0], 0, "above")
        add("con_8", "con", True, conf,
            "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk")

    # Con 9: EPS declining for 3 consecutive years
    eps3 = ratios_hist["earnings_per_share"].tail(3).tolist()
    if len(eps3) == 3 and all(pd.notna(v) for v in eps3) and eps3[0] > eps3[1] > eps3[2]:
        conf = confidence_from_margin(eps3[0] - eps3[2], 0, "above")
        add("con_9", "con", True, conf,
            "Earnings per share declining for 3 consecutive years reflects deteriorating profitability")

    # Con 10: ROCE < 10%
    if pd.notna(latest["return_on_capital_employed_pct"]) and latest["return_on_capital_employed_pct"] < 10:
        conf = confidence_from_margin(latest["return_on_capital_employed_pct"], 10, "below")
        add("con_10", "con", True, conf,
            "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital")

    # Con 11: Net Debt > 3x EBITDA (approximated as gross total_debt_cr — see module docstring)
    if pl_latest is not None and pd.notna(pl_latest["operating_profit"]) and pd.notna(pl_latest["depreciation"]):
        ebitda = pl_latest["operating_profit"] + pl_latest["depreciation"]
        gross_debt = latest["total_debt_cr"]
        if pd.notna(gross_debt) and ebitda > 0 and gross_debt > 3 * ebitda:
            conf = confidence_from_margin(gross_debt / ebitda, 3, "above")
            add("con_11", "con", True, conf,
                "Gross debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility")

    # Con 12: Revenue CAGR < 5% over 5 years
    if pd.notna(latest["revenue_cagr_5yr"]) and latest["revenue_cagr_5yr"] < 5:
        conf = confidence_from_margin(latest["revenue_cagr_5yr"], 5, "below")
        add("con_12", "con", True, conf,
            "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum")

    return results


# ---------------------------------------------------------------------
# Fallback rules — ensure every company has >=1 pro and >=1 con
#
# The 24 spec'd rules are strict thresholds; mid-performing companies with
# no clear strength or clear red flag legitimately trigger nothing on one
# side. These fallbacks pick the single most favorable / most concerning
# metric for that company and generate a softer statement, pegged at a
# lower confidence (61%) so they're distinguishable from the 24 primary
# rules in the output.
# ---------------------------------------------------------------------

def fallback_pro(latest):
    """
    Priority list of metrics to describe when no primary pro rule triggered.
    Phrased neutrally/descriptively (not "strong" or "excellent") since these
    values didn't clear any of the 12 primary pro thresholds — we're reporting
    the most relevant available figure, not claiming it's exceptional.
    """
    candidates = [
        ("return_on_equity_pct", "Return on equity of {:.1f}% reflects the company's current capital efficiency level"),
        ("return_on_capital_employed_pct", "Return on capital employed of {:.1f}% reflects the current return generated on invested capital"),
        ("operating_profit_margin_pct", "An operating margin of {:.1f}% reflects the company's current cost and pricing structure"),
        ("revenue_cagr_5yr", "Revenue has grown at a {:.1f}% CAGR over the past 5 years"),
        ("free_cash_flow_cr", "The company generated \u20b9{:.0f} Cr of free cash flow in the latest reported year"),
    ]
    for col, template in candidates:
        val = latest.get(col)
        if pd.notna(val):
            return template.format(val)
    return "Limited standardized ratio data is available for this company for a specific strength assessment."


def fallback_con(latest):
    """
    Priority list of metrics to flag as a monitoring point when no primary
    con rule triggered. Phrased as neutrally "worth monitoring" rather than
    alarmist, since these values didn't cross any of the 12 primary con
    thresholds — this is a watch-point, not a confirmed red flag.
    """
    candidates = [
        ("debt_to_equity", "Debt-to-equity ratio of {:.2f} is a factor worth monitoring given the company's capital structure"),
        ("return_on_capital_employed_pct", "Return on capital employed of {:.1f}% is a metric worth tracking over time"),
        ("revenue_cagr_5yr", "Revenue CAGR of {:.1f}% over 5 years is a growth trend worth monitoring"),
        ("net_profit_margin_pct", "Net profit margin of {:.1f}% is a margin level worth monitoring relative to peers"),
    ]
    for col, template in candidates:
        val = latest.get(col)
        if pd.notna(val):
            return template.format(val)
    return "Limited standardized ratio data is available for this company for a specific risk assessment."


def apply_fallbacks(company_id, company_results, latest):
    has_pro = any(r["type"] == "pro" for r in company_results)
    has_con = any(r["type"] == "con" for r in company_results)

    if not has_pro:
        text = fallback_pro(latest)
        if text:
            company_results.append({
                "company_id": company_id, "type": "pro", "rule_id": "pro_fallback",
                "text": text, "confidence_pct": 61.0,
            })

    if not has_con:
        text = fallback_con(latest)
        if text:
            company_results.append({
                "company_id": company_id, "type": "con", "rule_id": "con_fallback",
                "text": text, "confidence_pct": 61.0,
            })

    return company_results


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    conn = get_connection()
    ratios, bs, pl, sectors, market_cap, companies = load_data(conn)
    conn.close()

    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))

    all_results = []

    for _, company_row in companies.iterrows():
        company_id = company_row["company_id"]
        ratios_hist = ratios[ratios["company_id"] == company_id]
        bs_hist = bs[bs["company_id"] == company_id]
        pl_hist = pl[pl["company_id"] == company_id]
        sector = sector_map.get(company_id)

        div_rows = market_cap[market_cap["company_id"] == company_id]
        div_yield_latest = div_rows["dividend_yield_pct"].iloc[-1] if not div_rows.empty else None

        results = evaluate_rules(company_id, ratios_hist, bs_hist, pl_hist, sector, div_yield_latest)

        if not ratios_hist.empty:
            latest_row = ratios_hist.iloc[-1]
        else:
            # No financial_ratios history at all for this company (e.g. ATGL, SBIN) —
            # fall back to the companies table's own roe/roce fields as a last resort.
            latest_row = pd.Series({
                "return_on_equity_pct": company_row.get("roe_percentage"),
                "return_on_capital_employed_pct": company_row.get("roce_percentage"),
                "operating_profit_margin_pct": None,
                "revenue_cagr_5yr": None,
                "free_cash_flow_cr": None,
                "debt_to_equity": None,
                "net_profit_margin_pct": None,
            })

        results = apply_fallbacks(company_id, results, latest_row)
        all_results.extend(results)

    out_df = pd.DataFrame(all_results)
    out_path = OUTPUT_DIR / "pros_cons_generated.csv"
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {len(out_df)} pros/cons rows for {companies['company_id'].nunique()} companies -> {out_path}")

    # Coverage check: every company should have >=1 pro and >=1 con
    coverage_rows = []
    for company_id in companies["company_id"]:
        company_rows = out_df[out_df["company_id"] == company_id] if not out_df.empty else pd.DataFrame()
        has_pro = (company_rows["type"] == "pro").any() if not company_rows.empty else False
        has_con = (company_rows["type"] == "con").any() if not company_rows.empty else False
        if not has_pro or not has_con:
            coverage_rows.append({"company_id": company_id, "has_pro": has_pro, "has_con": has_con})

    coverage_df = pd.DataFrame(coverage_rows)
    coverage_path = OUTPUT_DIR / "pros_cons_coverage_check.csv"
    coverage_df.to_csv(coverage_path, index=False)

    if coverage_df.empty:
        print("Coverage check passed: every company has at least 1 pro and 1 con.")
    else:
        print(f"\nCoverage check FAILED for {len(coverage_df)} companies (see {coverage_path}):")
        print(coverage_df.to_string(index=False))


if __name__ == "__main__":
    main()