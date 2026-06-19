from src.etl.loader import load_companies

df = load_companies("data/raw/companies.xlsx")

print(df.head())
print(df.shape)
print(df.columns.tolist())