import pandas as pd
from pathlib import Path

INPUT = Path("data/processed/mplads_validated_dedup.csv")
OUTPUT = Path("data/processed/mplads_expenditure_transactions.csv")

WORK_KEY = "WORK_RECOMMENDATION_DTL_ID"

print("=" * 70)
print("FUNDGUARD AI — PHASE 2.3")
print("BUILD EXPENDITURE TRANSACTION DATASET")
print("=" * 70)

# ---------------------------------------------------------
# Load
# ---------------------------------------------------------

df = pd.read_csv(INPUT)

exp = df[
    df["_SOURCE_KEY"]
    == "Expenditure on Completed and On-going Works as on Date"
].copy()

print(f"\nExpenditure records: {len(exp):,}")
print(f"Unique works: {exp[WORK_KEY].nunique():,}")


# ---------------------------------------------------------
# Keep only expenditure-relevant fields
# ---------------------------------------------------------

columns = [
    WORK_KEY,
    "WORK_ID",
    "MP_NAME",
    "CONSTITUENCY",
    "CONSTITUENCY_ID",
    "STATE_NAME",
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
    "WORK_DESCRIPTION",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "VENDOR_NAME",
    "VENDOR_ID",
    "IA_NAME",
    "EXPENDITURE_DATE",
    "FUND_DISBURSED_AMT",
]

columns = [
    c for c in columns
    if c in exp.columns
]

transactions = exp[columns].copy()


# ---------------------------------------------------------
# Clean numeric values
# ---------------------------------------------------------

for column in [
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "VENDOR_ID",
    "FUND_DISBURSED_AMT",
]:

    if column in transactions.columns:
        transactions[column] = pd.to_numeric(
            transactions[column],
            errors="coerce"
        )


# ---------------------------------------------------------
# Clean expenditure date
# ---------------------------------------------------------

if "EXPENDITURE_DATE" in transactions.columns:

    transactions["EXPENDITURE_DATE"] = pd.to_datetime(
        transactions["EXPENDITURE_DATE"],
        errors="coerce",
        dayfirst=True
    )


# ---------------------------------------------------------
# Transaction-level identifier
# ---------------------------------------------------------

transactions.insert(
    0,
    "TRANSACTION_ID",
    range(1, len(transactions) + 1)
)


# ---------------------------------------------------------
# Exact transaction duplicate check
# ---------------------------------------------------------

duplicate_columns = [
    WORK_KEY,
    "EXPENDITURE_DATE",
    "VENDOR_ID",
    "FUND_DISBURSED_AMT",
]

duplicate_columns = [
    c for c in duplicate_columns
    if c in transactions.columns
]

transactions["POSSIBLE_DUPLICATE"] = (
    transactions
    .duplicated(
        subset=duplicate_columns,
        keep=False
    )
    .astype(int)
)


# ---------------------------------------------------------
# Sort
# ---------------------------------------------------------

sort_columns = [
    WORK_KEY,
    "EXPENDITURE_DATE",
    "TRANSACTION_ID",
]

sort_columns = [
    c for c in sort_columns
    if c in transactions.columns
]

transactions = transactions.sort_values(
    sort_columns
).reset_index(drop=True)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

transactions.to_csv(
    OUTPUT,
    index=False
)


# ---------------------------------------------------------
# Report
# ---------------------------------------------------------

print("\n" + "-" * 70)
print("TRANSACTION DATASET")
print("-" * 70)

print(f"Rows:              {len(transactions):,}")
print(
    f"Unique works:      "
    f"{transactions[WORK_KEY].nunique():,}"
)

print(
    f"Unique vendors:    "
    f"{transactions['VENDOR_ID'].nunique():,}"
)

print(
    f"Unique dates:      "
    f"{transactions['EXPENDITURE_DATE'].nunique():,}"
)

print(
    f"Possible duplicate: "
    f"{transactions['POSSIBLE_DUPLICATE'].sum():,}"
)

print("\nDisbursement statistics:")

print(
    transactions["FUND_DISBURSED_AMT"]
    .describe()
    .to_string()
)

print(f"\nSaved → {OUTPUT}")

print("\n" + "=" * 70)
print("PHASE 2.3 COMPLETE")
print("=" * 70)