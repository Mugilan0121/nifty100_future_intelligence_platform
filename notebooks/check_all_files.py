import pandas as pd

files = [
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "profitandloss.xlsx",
    "companies.xlsx"
]

for file in files:
    print("\n" + "=" * 70)
    print(file)
    print("=" * 70)

    df = pd.read_excel(
        f"data/raw/{file}",
        header=1
    )

    print(df.columns.tolist())