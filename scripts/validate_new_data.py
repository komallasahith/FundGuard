import json
import pandas as pd
from pathlib import Path

RAW_FILE = Path("data/raw/mplads_all_works.json")
OUT_DIR = Path("data/processed")

print("=" * 70)
print("FUNDGUARD AI — NEW MPLADS DATA VALIDATION")
print("=" * 70)

# ---------------------------------------------------------
# 1. Load raw JSON
# ---------------------------------------------------------
with open(RAW_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"\nRaw records: {len(data):,}")

df = pd.DataFrame(data)

print(f"Columns: {len(df.columns)}")

# ---------------------------------------------------------
# 2. Show source breakdown
# ---------------------------------------------------------
print("\n" + "-" * 70)
print("SOURCE BREAKDOWN")
print("-" * 70)

if "_SOURCE_KEY" in df.columns:
    print(df["_SOURCE_KEY"].value_counts(dropna=False).to_string())
else:
    print("WARNING: _SOURCE_KEY not found")

# ---------------------------------------------------------
# 3. MP breakdown
# ---------------------------------------------------------
print("\n" + "-" * 70)
print("MP BREAKDOWN")
print("-" * 70)

if "_MP_NAME" in df.columns:
    print(f"Unique MPs: {df['_MP_NAME'].nunique()}")
    print(df["_MP_NAME"].value_counts().to_string())

# ---------------------------------------------------------
# 4. Constituency breakdown
# ---------------------------------------------------------
print("\n" + "-" * 70)
print("CONSTITUENCY BREAKDOWN")
print("-" * 70)

if "CONSTITUENCY" in df.columns:
    print(f"Unique constituencies: {df['CONSTITUENCY'].nunique()}")
    print(df["CONSTITUENCY"].value_counts().head(30).to_string())

# ---------------------------------------------------------
# 5. Exact duplicate analysis
# ---------------------------------------------------------
print("\n" + "-" * 70)
print("DUPLICATE ANALYSIS")
print("-" * 70)

duplicates = df.duplicated().sum()

print(f"Exact duplicate rows: {duplicates:,}")
print(f"Duplicate percentage: {(duplicates / len(df) * 100):.2f}%")

df_unique = df.drop_duplicates().copy()

print(f"Records after exact deduplication: {len(df_unique):,}")

# ---------------------------------------------------------
# 6. Work ID analysis
# ---------------------------------------------------------
print("\n" + "-" * 70)
print("WORK ID ANALYSIS")
print("-" * 70)

work_id_col = None

for col in [
    "WORK_RECOMMENDATION_DTL_ID",
    "WORK_ID",
]:
    if col in df.columns:
        non_null = df[col].notna().sum()

        print(f"{col}:")
        print(f"  Non-null: {non_null:,}")
        print(f"  Unique:   {df[col].nunique(dropna=True):,}")

        if work_id_col is None and non_null > 0:
            work_id_col = col

if work_id_col:
    print(f"\nPrimary work identifier: {work_id_col}")

    counts = (
        df[df[work_id_col].notna()]
        .groupby(work_id_col)
        .size()
    )

    print(f"Works appearing once:  {(counts == 1).sum():,}")
    print(f"Works appearing >1:    {(counts > 1).sum():,}")
    print(f"Maximum repetitions:   {counts.max()}")

    print("\nMost repeated work IDs:")
    print(counts.sort_values(ascending=False).head(20).to_string())

# ---------------------------------------------------------
# 7. Important financial fields
# ---------------------------------------------------------
print("\n" + "-" * 70)
print("FINANCIAL FIELD AVAILABILITY")
print("-" * 70)

financial_cols = [
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "FUND_DISBURSED_AMT",
    "ALLOCATED_AMOUNT",
    "EXPENDITURE",
]

for col in financial_cols:
    if col in df.columns:
        numeric = pd.to_numeric(df[col], errors="coerce")

        print(
            f"{col:25} "
            f"non-null={numeric.notna().sum():6,} "
            f"unique={numeric.nunique():6,}"
        )

# ---------------------------------------------------------
# 8. Important identity fields
# ---------------------------------------------------------
print("\n" + "-" * 70)
print("IDENTITY FIELD AVAILABILITY")
print("-" * 70)

identity_cols = [
    "WORK_ID",
    "WORK_RECOMMENDATION_DTL_ID",
    "MP_NAME",
    "CONSTITUENCY",
    "CONSTITUENCY_ID",
    "WORK_DESCRIPTION",
    "ACTIVITY_NAME",
    "WORK_CATEGORY",
    "WORK_STAGE",
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "ACTUAL_END_DATE",
]

for col in identity_cols:
    if col in df.columns:
        print(
            f"{col:30} "
            f"non-null={df[col].notna().sum():6,}"
        )

# ---------------------------------------------------------
# 9. Save exact-deduplicated raw dataset
# ---------------------------------------------------------
output_file = OUT_DIR / "mplads_validated_dedup.csv"

df_unique.to_csv(output_file, index=False)

print("\n" + "-" * 70)
print("OUTPUT")
print("-" * 70)

print(f"Saved: {output_file}")
print(f"Rows:  {len(df_unique):,}")

print("\nValidation complete.")