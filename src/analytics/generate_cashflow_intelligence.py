"""
Day 31 — Cash Flow Intelligence Module (runner)

Uses the pure functions in cashflow_kpis.py (existing Sprint 2 code +
Day 31 additions) against the raw `cashflow`, `profitandloss`, and
`balancesheet` tables to produce:

    output/cashflow_intelligence.xlsx
    output/distress_alerts.csv

Data-model note: the `cashflow` table stores years as "Mar-13" while
every other table uses "Mar 2013" — a flexible year parser below
normalizes both to a plain integer year so cashflow rows can be aligned
with profitandloss (sales, net_profit) and balancesheet (borrowings)
for the same fiscal year.
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

import cashflow_kpis as cfk

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"


def get_connection() -> sqlite3.Connection:
    """Returns a SQLite connection to the project database."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    return sqlite3.connect(DB_PATH)


def year_num_flexible(y):
    """
    Normalizes 'Mar 2013' / 'Dec 2012' (financial_ratios, balancesheet,
    profitandloss) and 'Mar-13' (cashflow) to the same integer year.
    Returns None for anything else (TTM, stub periods, malformed values).
    """
    s = str(y).strip()
    m = re.search(r"(\d{4})$", s)
    if m:
        return int(m.group(1))
    m2 = re.search(r"-(\d{2})$", s)
    if m2:
        return 2000 + int(m2.group(1))
    return None


def load_data(conn):
    """Loads cash flow and financial ratio data needed for cashflow intelligence metrics."""
    cashflow = pd.read_sql_query("SELECT * FROM cashflow", conn)
    pl = pd.read_sql_query("SELECT company_id, year, sales, net_profit, operating_profit FROM profitandloss", conn)
    bs = pd.read_sql_query("SELECT company_id, year, borrowings FROM balancesheet", conn)
    sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    companies = pd.read_sql_query("SELECT id AS company_id FROM companies", conn)

    for df in (cashflow, pl, bs):
        df["year_num"] = df["year"].apply(year_num_flexible)
        df.dropna(subset=["year_num"], inplace=True)
        df["year_num"] = df["year_num"].astype(int)
        df.sort_values(["company_id", "year_num"], inplace=True)

    return cashflow, pl, bs, sectors, companies


def main():
    """Computes cashflow intelligence KPIs for all companies and writes them to the database."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    conn = get_connection()
    cashflow, pl, bs, sectors, companies = load_data(conn)
    conn.close()

    print(f"cashflow: {cashflow['company_id'].nunique()} companies, {len(cashflow)} rows (after year parsing)")

    sector_map = dict(zip(sectors["company_id"], sectors["broad_sector"]))

    rows = []
    distress_rows = []
    skipped = []

    for company_id in companies["company_id"]:
        cf_hist = cashflow[cashflow["company_id"] == company_id]
        pl_hist = pl[pl["company_id"] == company_id]
        bs_hist = bs[bs["company_id"] == company_id]

        if cf_hist.empty:
            skipped.append(company_id)
            rows.append({
                "company_id": company_id,
                "sector": sector_map.get(company_id),
                "cfo_quality_score": None,
                "cfo_quality_label": None,
                "capex_intensity_pct": None,
                "capex_label": None,
                "fcf_cagr_5yr": None,
                "fcf_conversion_pct": None,
                "distress_flag": False,
                "deleveraging_flag": False,
                "capital_allocation_label": None,
            })
            continue

        # --- CFO Quality Score: avg(CFO/PAT) over up to last 5 years ---
        cf_last5 = cf_hist.tail(5)
        quality_scores = []
        for _, cf_row in cf_last5.iterrows():
            pl_match = pl_hist[pl_hist["year_num"] == cf_row["year_num"]]
            if not pl_match.empty:
                net_profit = pl_match.iloc[0]["net_profit"]
                score = cfk.cfo_quality_score(cf_row["operating_activity"], net_profit)
                if score is not None:
                    quality_scores.append(score)

        cfo_quality_avg = sum(quality_scores) / len(quality_scores) if quality_scores else None
        cfo_quality_label = cfk.classify_cfo_quality(cfo_quality_avg)

        # --- CapEx Intensity: latest year, abs(CFI)/sales * 100 ---
        cf_latest = cf_hist.iloc[-1]
        pl_latest_match = pl_hist[pl_hist["year_num"] == cf_latest["year_num"]]
        capex_intensity_pct = None
        capex_label = None
        fcf_conversion_pct = None
        if not pl_latest_match.empty:
            sales_latest = pl_latest_match.iloc[0]["sales"]
            op_profit_latest = pl_latest_match.iloc[0]["operating_profit"]
            capex_intensity_pct = cfk.capex_intensity(cf_latest["investing_activity"], sales_latest)
            capex_label = cfk.classify_capex_intensity(capex_intensity_pct)

            fcf_latest = cfk.free_cash_flow(cf_latest["operating_activity"], cf_latest["investing_activity"])
            fcf_conversion_pct = cfk.fcf_conversion_rate(fcf_latest, op_profit_latest)

        # --- FCF CAGR 5yr ---
        fcf_cagr_5yr = None
        if len(cf_hist) >= 6:
            cf_6 = cf_hist.tail(6)
            fcf_start = cfk.free_cash_flow(cf_6.iloc[0]["operating_activity"], cf_6.iloc[0]["investing_activity"])
            fcf_end = cfk.free_cash_flow(cf_6.iloc[-1]["operating_activity"], cf_6.iloc[-1]["investing_activity"])
            fcf_cagr_5yr = cfk.fcf_cagr(fcf_start, fcf_end, 5)

        # --- Distress Signal: latest year CFO<0 AND CFF>0 ---
        distress = cfk.distress_signal(cf_latest["operating_activity"], cf_latest["financing_activity"])

        # --- Deleveraging flag: latest year CFF<0 AND borrowings declining YoY ---
        deleveraging = False
        bs_match_latest = bs_hist[bs_hist["year_num"] == cf_latest["year_num"]]
        bs_before = bs_hist[bs_hist["year_num"] < cf_latest["year_num"]]
        if not bs_match_latest.empty and not bs_before.empty:
            borrow_latest = bs_match_latest.iloc[0]["borrowings"]
            borrow_prev = bs_before.iloc[-1]["borrowings"]
            borrowings_declining = borrow_latest < borrow_prev
            deleveraging = cfk.deleveraging_flag(cf_latest["financing_activity"], borrowings_declining)

        # --- Capital Allocation label (latest year, using the existing classifier) ---
        capital_allocation_label = cfk.capital_allocation_pattern(
            cf_latest["operating_activity"], cf_latest["investing_activity"], cf_latest["financing_activity"]
        )

        rows.append({
            "company_id": company_id,
            "sector": sector_map.get(company_id),
            "cfo_quality_score": round(cfo_quality_avg, 3) if cfo_quality_avg is not None else None,
            "cfo_quality_label": cfo_quality_label,
            "capex_intensity_pct": round(capex_intensity_pct, 2) if capex_intensity_pct is not None else None,
            "capex_label": capex_label,
            "fcf_cagr_5yr": round(fcf_cagr_5yr, 2) if fcf_cagr_5yr is not None else None,
            "fcf_conversion_pct": round(fcf_conversion_pct, 2) if fcf_conversion_pct is not None else None,
            "distress_flag": distress,
            "deleveraging_flag": deleveraging,
            "capital_allocation_label": capital_allocation_label,
        })

        if distress:
            pl_match = pl_hist[pl_hist["year_num"] == cf_latest["year_num"]]
            latest_net_profit = pl_match.iloc[0]["net_profit"] if not pl_match.empty else None
            distress_rows.append({
                "company_id": company_id,
                "cfo_value": cf_latest["operating_activity"],
                "cff_value": cf_latest["financing_activity"],
                "latest_net_profit": latest_net_profit,
            })

    out_df = pd.DataFrame(rows)
    out_path = OUTPUT_DIR / "cashflow_intelligence.xlsx"
    out_df.to_excel(out_path, index=False)
    print(f"\nWrote {len(out_df)} rows -> {out_path}")

    if skipped:
        print(f"Included {len(skipped)} companies with null metrics (no cashflow data at all): {skipped}")

    distress_df = pd.DataFrame(distress_rows)
    distress_path = OUTPUT_DIR / "distress_alerts.csv"
    distress_df.to_csv(distress_path, index=False)
    print(f"Wrote {len(distress_df)} distress alerts -> {distress_path}")
    if not distress_df.empty:
        print(distress_df.to_string(index=False))


if __name__ == "__main__":
    main()