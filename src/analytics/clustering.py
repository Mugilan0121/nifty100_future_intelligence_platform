"""
Company Archetype Clustering.

Sprint 6 - Day 36

Runs KMeans clustering (k=5) on the 92 companies using 5 financial
features, imputing missing values with the sector median, and writes
output/cluster_labels.csv plus reports/elbow_plot.png.

Reuses output/cashflow_intelligence.xlsx (Day 31) for fcf_cagr_5yr
rather than recomputing it, since financial_ratios has no such column.
"""

import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / "nifty100.db"
CASHFLOW_INTEL_PATH = PROJECT_ROOT / "output" / "cashflow_intelligence.xlsx"
OUTPUT_PATH = PROJECT_ROOT / "output" / "cluster_labels.csv"
ELBOW_PLOT_PATH = PROJECT_ROOT / "reports" / "elbow_plot.png"

N_CLUSTERS = 5
RANDOM_STATE = 42

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]

# Note: names are NOT assigned by a fixed cluster_id -> name lookup.
# KMeans's cluster_id numbering isn't guaranteed identical across
# scikit-learn versions/machines even with the same random_state (the
# internal kmeans++ seeding can differ), so a hardcoded {0: "...", 1:
# "..."} dict broke when the same code ran on a different machine and
# produced a different id ordering for the same 5 underlying groups.
# assign_cluster_names() below looks at each cluster's actual computed
# profile instead, so naming is correct regardless of numbering.
def assign_cluster_names(df: pd.DataFrame, cluster_ids: np.ndarray) -> dict:
    """
    Map each cluster_id to a descriptive name based on its profile,
    not its numeric id. Rule order (each step picks from clusters not
    already named):
      1. Highest mean fcf_cagr_5yr -> Distressed or Turnaround
         (a large recovery swing, e.g. CIPLA's Day 37 profile)
      2. Highest mean debt_to_equity -> Leveraged Financials
         (high D/E is structurally normal for banks/NBFCs)
      3. Highest mean return_on_equity_pct -> High-Quality Compounders
      4. Highest mean operating_profit_margin_pct -> Defensive Dividend Payers
      5. Whatever's left -> Core Compounders
    """
    profile = df.assign(cluster_id=cluster_ids).groupby("cluster_id")[FEATURES].mean()
    remaining = set(profile.index)
    names = {}

    turnaround_id = profile.loc[list(remaining), "fcf_cagr_5yr"].idxmax()
    names[turnaround_id] = "Distressed or Turnaround"
    remaining.discard(turnaround_id)

    financials_id = profile.loc[list(remaining), "debt_to_equity"].idxmax()
    names[financials_id] = "Leveraged Financials"
    remaining.discard(financials_id)

    quality_id = profile.loc[list(remaining), "return_on_equity_pct"].idxmax()
    names[quality_id] = "High-Quality Compounders"
    remaining.discard(quality_id)

    defensive_id = profile.loc[list(remaining), "operating_profit_margin_pct"].idxmax()
    names[defensive_id] = "Defensive Dividend Payers"
    remaining.discard(defensive_id)

    for cluster_id in remaining:
        names[cluster_id] = "Core Compounders"

    return names


def get_connection() -> sqlite3.Connection:
    if not DATABASE_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DATABASE_PATH}")
    return sqlite3.connect(DATABASE_PATH)


def load_latest_financial_ratios(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load the latest-year financial_ratios row per company, joined
    with broad_sector from the sectors table.
    """
    df = pd.read_sql_query(
        """
        SELECT
            fr.company_id,
            fr.year,
            fr.return_on_equity_pct,
            fr.debt_to_equity,
            fr.revenue_cagr_5yr,
            fr.operating_profit_margin_pct,
            s.broad_sector
        FROM financial_ratios fr
        LEFT JOIN sectors s
        ON fr.company_id = s.company_id
        """,
        conn,
    )

    df = df.drop_duplicates()

    df = (
        df.sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    return df


def load_fcf_cagr() -> pd.DataFrame:
    """
    Load fcf_cagr_5yr from the Day 31 cashflow intelligence output.
    """
    if not CASHFLOW_INTEL_PATH.exists():
        raise FileNotFoundError(
            f"Cashflow intelligence output not found: {CASHFLOW_INTEL_PATH}. "
            "Run src/analytics/generate_cashflow_intelligence.py first."
        )

    df = pd.read_excel(CASHFLOW_INTEL_PATH)
    return df[["company_id", "fcf_cagr_5yr"]]


def load_all_company_ids(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load every company_id from the companies table, so companies with
    zero financial_ratios rows (ATGL, SBIN) still surface in the
    output rather than silently disappearing.
    """
    return pd.read_sql_query("SELECT id AS company_id FROM companies", conn)


def build_feature_frame() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Assemble the feature frame for companies with financial_ratios
    history, impute missing values with the sector median for each
    metric, and separately return the full company_id roster so
    no-data companies can be flagged rather than dropped.
    """
    with get_connection() as conn:
        df = load_latest_financial_ratios(conn)
        all_companies = load_all_company_ids(conn)

    fcf_df = load_fcf_cagr()

    df = df.merge(fcf_df, on="company_id", how="left")

    # Canonical universe is the companies table (92 rows, matches Gate
    # AC-01). financial_ratios independently has 92 distinct ids too,
    # but they differ by 2 tickers (ULTRACEMCO, UNIONBANK are in
    # financial_ratios but not companies; ATGL, SBIN are the reverse -
    # a known gap since Day 30/32). Excluding the former here rather
    # than expanding the universe mid-sprint, per the Day 32 precedent.
    out_of_scope = set(df["company_id"]) - set(all_companies["company_id"])
    if out_of_scope:
        print(
            f"Excluding {sorted(out_of_scope)} from clustering: present in "
            "financial_ratios but not in the companies table (scope "
            "mismatch, not part of the canonical 92)."
        )
        df = df[~df["company_id"].isin(out_of_scope)].reset_index(drop=True)

    missing_sector = df["broad_sector"].isna().sum()
    if missing_sector:
        print(
            f"Warning: {missing_sector} companies have financial_ratios "
            "rows but no matching sectors entry (known scope gap - see "
            "Day 32 note). Falling back to overall-dataset median for "
            "their imputation."
        )

    # Day 34 sanity guard: financial_ratios ROE is corrupted for BEL and
    # HAL (thousands of percent instead of ~26-29%), traced to Sprint 2's
    # ratio engine and never patched retroactively. Left uncorrected here,
    # these two outliers wreck StandardScaler's mean/std for the ROE
    # feature and collapse everyone else's scaled ROE toward zero.
    # Treating values beyond +-200% as N/A mirrors the same guard already
    # used in tearsheet.py and sector_report.py, then letting the normal
    # sector-median imputation below fill them back in.
    before = df["return_on_equity_pct"].abs() > 200
    if before.any():
        print(
            f"Applying Day 34 ROE sanity guard: {before.sum()} row(s) "
            f"beyond +-200% ({df.loc[before, 'company_id'].tolist()}) "
            "set to NaN before imputation."
        )
        df.loc[before, "return_on_equity_pct"] = np.nan

    for feature in FEATURES:
        sector_median = df.groupby("broad_sector")[feature].transform("median")
        overall_median = df[feature].median()

        df[feature] = df[feature].fillna(sector_median)
        # Fallback for any sector-median gaps (e.g. entire sector missing
        # the metric) to the overall dataset median.
        df[feature] = df[feature].fillna(overall_median)

    return df, all_companies


def run_elbow_analysis(scaled_features: np.ndarray) -> None:
    """
    Fit KMeans for k=2..10, plot inertia, and save reports/elbow_plot.png.
    """
    inertias = []
    k_range = range(2, 11)

    for k in k_range:
        model = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        model.fit(scaled_features)
        inertias.append(model.inertia_)

    ELBOW_PLOT_PATH.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(8, 5))
    plt.plot(list(k_range), inertias, marker="o")
    plt.axvline(x=N_CLUSTERS, color="red", linestyle="--", label=f"k={N_CLUSTERS}")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Plot")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ELBOW_PLOT_PATH)
    plt.close()

    print(f"Wrote elbow plot -> {ELBOW_PLOT_PATH}")


def run_clustering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Scale features, fit KMeans (k=5), and attach cluster_id,
    cluster_name, and distance_from_centroid to each company.
    """
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[FEATURES])

    run_elbow_analysis(scaled_features)

    model = KMeans(n_clusters=N_CLUSTERS, random_state=RANDOM_STATE, n_init=10)
    cluster_ids = model.fit_predict(scaled_features)

    distances = model.transform(scaled_features)
    distance_from_centroid = distances[np.arange(len(df)), cluster_ids]

    result_df = df[["company_id"]].copy()
    result_df["cluster_id"] = cluster_ids
    cluster_names = assign_cluster_names(df, cluster_ids)
    result_df["cluster_name"] = result_df["cluster_id"].map(cluster_names)
    result_df["distance_from_centroid"] = np.round(distance_from_centroid, 4)

    return result_df


def main() -> None:
    df, all_companies = build_feature_frame()

    n_clusterable = len(df)
    print(f"{n_clusterable} companies have financial_ratios history and were clustered.")

    result_df = run_clustering(df)

    # Companies with zero financial_ratios rows (ATGL, SBIN - known since
    # Day 30) can't be scaled/clustered. Add them back with a No Data
    # label so every row in the companies table still appears in the
    # output, satisfying Gate AC-15, rather than silently dropping them.
    missing_ids = sorted(set(all_companies["company_id"]) - set(result_df["company_id"]))
    if missing_ids:
        print(f"No financial_ratios history for: {missing_ids} - tagging as No Data.")
        no_data_rows = pd.DataFrame({
            "company_id": missing_ids,
            "cluster_id": -1,
            "cluster_name": "No Data",
            "distance_from_centroid": np.nan,
        })
        result_df = pd.concat([result_df, no_data_rows], ignore_index=True)

    if len(result_df) != 92:
        print(f"Warning: expected 92 companies in final output, found {len(result_df)}.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(OUTPUT_PATH, index=False)

    print(f"Wrote {len(result_df)} rows -> {OUTPUT_PATH}")
    print(result_df["cluster_name"].value_counts())


if __name__ == "__main__":
    main()