import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_works_raw_combined.csv"
)

EXPENDITURE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_expenditure.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_financial_master.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("FUNDGUARD INDIA FINANCIAL MASTER BUILDER")
print("=" * 70)

print("\nLoading expenditure dataset...")

expenditure = pd.read_csv(
    EXPENDITURE_FILE,
    low_memory=False
)

print(
    f"Expenditure rows: {len(expenditure):,}"
)


print("\nLoading raw collection...")

raw = pd.read_csv(
    RAW_FILE,
    low_memory=False
)

print(
    f"Raw rows: {len(raw):,}"
)


# ============================================================
# CANONICAL ID
# ============================================================

raw["WORK_RECOMMENDATION_DTL_ID"] = pd.to_numeric(
    raw["WORK_RECOMMENDATION_DTL_ID"],
    errors="coerce"
)


expenditure["WORK_ID"] = pd.to_numeric(
    expenditure["WORK_ID"],
    errors="coerce"
)


# ============================================================
# SELECT COMPLETED WORKS
# ============================================================

completed = raw[
    raw["_SOURCE_KEY"].eq("Works Completed")
    & raw["ACTUAL_AMOUNT"].notna()
].copy()


print("\nCompleted-work records:", len(completed))


# ============================================================
# VALIDATE COMPLETED DATA
# ============================================================

print(
    "Unique completed DTL IDs:",
    completed["WORK_RECOMMENDATION_DTL_ID"].nunique()
)

print(
    "Duplicate completed DTL IDs:",
    completed["WORK_RECOMMENDATION_DTL_ID"]
    .duplicated()
    .sum()
)


if completed["WORK_RECOMMENDATION_DTL_ID"].duplicated().any():

    raise ValueError(
        "Duplicate completed-work DTL IDs detected."
    )


# ============================================================
# CLEAN FIELDS
# ============================================================

completed["ACTUAL_AMOUNT"] = pd.to_numeric(
    completed["ACTUAL_AMOUNT"],
    errors="coerce"
)

completed["AVERAGE_RATING"] = pd.to_numeric(
    completed["AVERAGE_RATING"],
    errors="coerce"
)

completed["ACTUAL_END_DATE"] = pd.to_datetime(
    completed["ACTUAL_END_DATE"],
    errors="coerce",
    dayfirst=True
)


# ============================================================
# COMPLETION DATAFRAME
# ============================================================

completion = completed[
    [
        "WORK_RECOMMENDATION_DTL_ID",
        "ACTUAL_AMOUNT",
        "ACTUAL_END_DATE",
        "AVERAGE_RATING",
    ]
].copy()


completion = completion.rename(
    columns={
        "ACTUAL_END_DATE": "ACTUAL_END_DATE"
    }
)


# ============================================================
# MERGE
# ============================================================

print("\nMerging completed-work data...")

financial = expenditure.merge(
    completion,
    how="left",
    left_on="WORK_ID",
    right_on="WORK_RECOMMENDATION_DTL_ID",
    validate="one_to_one"
)


financial.drop(
    columns=["WORK_RECOMMENDATION_DTL_ID"],
    inplace=True
)


# ============================================================
# COMPLETION FLAG
# ============================================================

financial["HAS_COMPLETION_RECORD"] = (
    financial["ACTUAL_AMOUNT"].notna()
)


# ============================================================
# DATE CONVERSION
# ============================================================

financial["RECOMMENDATION_DATE"] = pd.to_datetime(
    financial["RECOMMENDATION_DATE"],
    errors="coerce",
    dayfirst=True
)

financial["SANCTION_DATE"] = pd.to_datetime(
    financial["SANCTION_DATE"],
    errors="coerce",
    dayfirst=True
)

financial["FIRST_EXPENDITURE_DATE"] = pd.to_datetime(
    financial["FIRST_EXPENDITURE_DATE"],
    errors="coerce"
)

financial["LAST_EXPENDITURE_DATE"] = pd.to_datetime(
    financial["LAST_EXPENDITURE_DATE"],
    errors="coerce"
)


# ============================================================
# ACTUAL / SANCTION RATIO
# ============================================================

financial["ACTUAL_TO_SANCTION_RATIO"] = np.where(
    (
        financial["ACTUAL_AMOUNT"].notna()
        &
        financial["SANCTION_AMOUNT"].notna()
        &
        financial["SANCTION_AMOUNT"].gt(0)
    ),

    financial["ACTUAL_AMOUNT"]
    / financial["SANCTION_AMOUNT"],

    np.nan
)


# ============================================================
# ACTUAL / RECOMMENDED RATIO
# ============================================================

financial["ACTUAL_TO_RECOMMENDED_RATIO"] = np.where(
    (
        financial["ACTUAL_AMOUNT"].notna()
        &
        financial["RECOMMENDED_AMOUNT"].notna()
        &
        financial["RECOMMENDED_AMOUNT"].gt(0)
    ),

    financial["ACTUAL_AMOUNT"]
    / financial["RECOMMENDED_AMOUNT"],

    np.nan
)


# ============================================================
# ACTUAL / DISBURSED RATIO
# ============================================================

financial["ACTUAL_VS_DISBURSED_RATIO"] = np.where(
    (
        financial["ACTUAL_AMOUNT"].notna()
        &
        financial["TOTAL_FUND_DISBURSED_AMT"].notna()
        &
        financial["TOTAL_FUND_DISBURSED_AMT"].gt(0)
    ),

    financial["ACTUAL_AMOUNT"]
    / financial["TOTAL_FUND_DISBURSED_AMT"],

    np.nan
)


# ============================================================
# COMPLETION DURATION
# ============================================================

financial["COMPLETION_DURATION_DAYS"] = np.nan

mask = (
    financial["ACTUAL_END_DATE"].notna()
    &
    financial["RECOMMENDATION_DATE"].notna()
)

financial.loc[mask, "COMPLETION_DURATION_DAYS"] = (
    financial.loc[mask, "ACTUAL_END_DATE"]
    -
    financial.loc[mask, "RECOMMENDATION_DATE"]
).dt.days


# ============================================================
# SANCTION TO COMPLETION DURATION
# ============================================================

financial["SANCTION_TO_COMPLETION_DAYS"] = np.nan

mask = (
    financial["ACTUAL_END_DATE"].notna()
    &
    financial["SANCTION_DATE"].notna()
)

financial.loc[mask, "SANCTION_TO_COMPLETION_DAYS"] = (
    financial.loc[mask, "ACTUAL_END_DATE"]
    -
    financial.loc[mask, "SANCTION_DATE"]
).dt.days


# ============================================================
# DATE FORMAT
# ============================================================

date_columns = [
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "FIRST_EXPENDITURE_DATE",
    "LAST_EXPENDITURE_DATE",
    "ACTUAL_END_DATE",
]

for col in date_columns:

    if col in financial.columns:

        financial[col] = financial[col].dt.strftime(
            "%Y-%m-%d"
        )


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("FINANCIAL MASTER VALIDATION")
print("=" * 70)

print(
    f"\nRows: {len(financial):,}"
)

print(
    f"Columns: {len(financial.columns):,}"
)

print(
    "Unique WORK_ID:",
    financial["WORK_ID"].nunique()
)

print(
    "Missing WORK_ID:",
    financial["WORK_ID"].isna().sum()
)

print(
    "Duplicate WORK_ID:",
    financial["WORK_ID"].duplicated().sum()
)


# ============================================================
# COMPLETION COVERAGE
# ============================================================

completed_works = financial[
    financial["HAS_COMPLETION_RECORD"]
]

not_completed = financial[
    ~financial["HAS_COMPLETION_RECORD"]
]

print("\nCompletion coverage:")

print(
    "Works with completion records:",
    len(completed_works)
)

print(
    "Works without completion records:",
    len(not_completed)
)

print(
    "Completion coverage:",
    f"{len(completed_works) / len(financial) * 100:.2f}%"
)


# ============================================================
# ACTUAL AMOUNT
# ============================================================

actual = financial["ACTUAL_AMOUNT"]

print("\nActual amount:")

print(
    "Available:",
    actual.notna().sum()
)

print(
    "Zero:",
    (actual == 0).sum()
)

print(
    "Minimum:",
    actual.min()
)

print(
    "Median:",
    actual.median()
)

print(
    "Maximum:",
    actual.max()
)


# ============================================================
# RATIO CHECKS
# ============================================================

print("\nActual / sanction ratio:")

ratio = financial["ACTUAL_TO_SANCTION_RATIO"]

print(
    "Available:",
    ratio.notna().sum()
)

print(
    "Minimum:",
    ratio.min()
)

print(
    "Median:",
    ratio.median()
)

print(
    "Maximum:",
    ratio.max()
)

print(
    "Above 1.0:",
    (ratio > 1).sum()
)

print(
    "Above 1.5:",
    (ratio > 1.5).sum()
)

print(
    "Above 2.0:",
    (ratio > 2).sum()
)


# ============================================================
# RATING
# ============================================================

print("\nAverage rating:")

print(
    "Available:",
    financial["AVERAGE_RATING"].notna().sum()
)

print(
    "Unique ratings:",
    financial["AVERAGE_RATING"]
    .dropna()
    .nunique()
)


# ============================================================
# COMPLETION DURATION
# ============================================================

duration = financial[
    "COMPLETION_DURATION_DAYS"
]

print("\nCompletion duration:")

print(
    "Available:",
    duration.notna().sum()
)

print(
    "Negative:",
    (duration < 0).sum()
)

print(
    "Minimum:",
    duration.min()
)

print(
    "Median:",
    duration.median()
)

print(
    "Maximum:",
    duration.max()
)


# ============================================================
# SAVE
# ============================================================

financial.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 70)

print(
    "Saved financial master:"
)

print(OUTPUT_FILE)

print("=" * 70)