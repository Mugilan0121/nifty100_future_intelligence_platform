import pandas as pd
from pathlib import Path

folders = ["data/raw"]

for folder in folders:
    print(f"\n===== {folder} =====")

    for file in Path(folder).glob("*.xlsx"):
        try:
            df = pd.read_excel(file, header=1, nrows=0)
            print(f"\n{file.name}")
            print(list(df.columns))
        except Exception as e:
            print(file.name, e)