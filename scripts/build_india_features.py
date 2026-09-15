import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_financial_master.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_features.csv"
)


# ============================================================
# HELPERS
# ============================================================

def numeric(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )


def date(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce"
            )


def safe_ratio(numerator, denominator):
    return np.where(
        (
            numerator.notna()
            &
            denominator.notna()
            &
            denominator.gt(0)
        ),
        numerator / denominator,
        np.nan
    )


# ============================================================
# START
# ============================================================

print("=" * 70)
print("FUNDGUARD INDIA FEATURE ENGINEERING")
print("=" * 70)


# ============================================================
# LOAD
# ============================================================

print("\nLoading financial master...")

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print(
    f"Rows: {len(df):,}"
)

print(
    f"Columns: {len(df.columns):,}"
)


# ============================================================
# BASIC VALIDATION
# ============================================================

if "WORK_ID" not in df.columns:
    raise ValueError(
        "WORK_ID not found in financial master."
    )


df["WORK_ID"] = pd.to_numeric(
    df["WORK_ID"],
    errors="coerce"
)


if df["WORK_ID"].isna().any():
    raise ValueError(
        "Missing WORK_ID values found."
    )


if df["WORK_ID"].duplicated().any():
    raise ValueError(
        "Duplicate WORK_ID values found."
    )


# ============================================================
# NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "TOTAL_FUND_DISBURSED_AMT",
    "ACTUAL_AMOUNT",

    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",
    "UNIQUE_VENDOR_NAME_COUNT",

    "PAYMENT_SUCCESS_COUNT",
    "PAYMENT_IN_PROGRESS_COUNT",

    "AVERAGE_RATING",

    "DISBURSED_TO_SANCTION_RATIO",
    "REMAINING_SANCTION_AMOUNT",

    "ACTUAL_TO_SANCTION_RATIO",
    "ACTUAL_TO_RECOMMENDED_RATIO",
    "ACTUAL_VS_DISBURSED_RATIO",

    "EXPENDITURE_DURATION_DAYS",
    "PAYMENTS_PER_100_DAYS",

    "COMPLETION_DURATION_DAYS",
    "SANCTION_TO_COMPLETION_DAYS",
]


numeric(
    df,
    numeric_columns
)


# ============================================================
# DATE COLUMNS
# ============================================================

date_columns = [
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "FIRST_EXPENDITURE_DATE",
    "LAST_EXPENDITURE_DATE",
    "ACTUAL_END_DATE",
]


date(
    df,
    date_columns
)


# ============================================================
# SECTION 1
# BASIC FINANCIAL FEATURES
# ============================================================

print("\nCreating financial features...")


# Recommended - Sanctioned

df["RECOMMENDED_TO_SANCTION_DIFFERENCE"] = np.where(
    (
        df["RECOMMENDED_AMOUNT"].notna()
        &
        df["SANCTION_AMOUNT"].notna()
    ),

    df["RECOMMENDED_AMOUNT"]
    -
    df["SANCTION_AMOUNT"],

    np.nan
)


# Sanction / Recommended

df["SANCTION_TO_RECOMMENDED_RATIO"] = safe_ratio(
    df["SANCTION_AMOUNT"],
    df["RECOMMENDED_AMOUNT"]
)


# Disbursed / Recommended

df["DISBURSED_TO_RECOMMENDED_RATIO"] = safe_ratio(
    df["TOTAL_FUND_DISBURSED_AMT"],
    df["RECOMMENDED_AMOUNT"]
)


# Remaining sanction ratio

df["REMAINING_SANCTION_RATIO"] = safe_ratio(
    df["REMAINING_SANCTION_AMOUNT"],
    df["SANCTION_AMOUNT"]
)


# ============================================================
# SECTION 2
# PAYMENT FEATURES
# ============================================================

print("Creating payment features...")


# Average payment amount

df["AVERAGE_PAYMENT_AMOUNT"] = safe_ratio(
    df["TOTAL_FUND_DISBURSED_AMT"],
    df["PAYMENT_COUNT"]
)


# Successful payment ratio

df["PAYMENT_SUCCESS_RATIO"] = safe_ratio(
    df["PAYMENT_SUCCESS_COUNT"],
    df["PAYMENT_COUNT"]
)


# In-progress payment ratio

df["PAYMENT_IN_PROGRESS_RATIO"] = safe_ratio(
    df["PAYMENT_IN_PROGRESS_COUNT"],
    df["PAYMENT_COUNT"]
)


# Payments per vendor

df["PAYMENTS_PER_VENDOR"] = safe_ratio(
    df["PAYMENT_COUNT"],
    df["UNIQUE_VENDOR_COUNT"]
)


# ============================================================
# SECTION 3
# TIMELINE FEATURES
# ============================================================

print("Creating timeline features...")


# Recommendation -> Sanction

mask = (
    df["RECOMMENDATION_DATE"].notna()
    &
    df["SANCTION_DATE"].notna()
)

df["RECOMMENDATION_TO_SANCTION_DAYS"] = np.nan

df.loc[mask, "RECOMMENDATION_TO_SANCTION_DAYS"] = (
    df.loc[mask, "SANCTION_DATE"]
    -
    df.loc[mask, "RECOMMENDATION_DATE"]
).dt.days


# Sanction -> First Payment

mask = (
    df["SANCTION_DATE"].notna()
    &
    df["FIRST_EXPENDITURE_DATE"].notna()
)

df["SANCTION_TO_FIRST_PAYMENT_DAYS"] = np.nan

df.loc[mask, "SANCTION_TO_FIRST_PAYMENT_DAYS"] = (
    df.loc[mask, "FIRST_EXPENDITURE_DATE"]
    -
    df.loc[mask, "SANCTION_DATE"]
).dt.days


# Recommendation -> First Payment

mask = (
    df["RECOMMENDATION_DATE"].notna()
    &
    df["FIRST_EXPENDITURE_DATE"].notna()
)

df["RECOMMENDATION_TO_FIRST_PAYMENT_DAYS"] = np.nan

df.loc[
    mask,
    "RECOMMENDATION_TO_FIRST_PAYMENT_DAYS"
] = (
    df.loc[mask, "FIRST_EXPENDITURE_DATE"]
    -
    df.loc[mask, "RECOMMENDATION_DATE"]
).dt.days


# Last Payment -> Completion

mask = (
    df["LAST_EXPENDITURE_DATE"].notna()
    &
    df["ACTUAL_END_DATE"].notna()
)

df["LAST_PAYMENT_TO_COMPLETION_DAYS"] = np.nan

df.loc[
    mask,
    "LAST_PAYMENT_TO_COMPLETION_DAYS"
] = (
    df.loc[mask, "ACTUAL_END_DATE"]
    -
    df.loc[mask, "LAST_EXPENDITURE_DATE"]
).dt.days


# Recommendation -> Completion

mask = (
    df["RECOMMENDATION_DATE"].notna()
    &
    df["ACTUAL_END_DATE"].notna()
)

df["RECOMMENDATION_TO_COMPLETION_DAYS"] = np.nan

df.loc[
    mask,
    "RECOMMENDATION_TO_COMPLETION_DAYS"
] = (
    df.loc[mask, "ACTUAL_END_DATE"]
    -
    df.loc[mask, "RECOMMENDATION_DATE"]
).dt.days


# ============================================================
# SECTION 4
# PAYMENT INTENSITY
# ============================================================

print("Creating payment intensity features...")


# Payments per 30 days

df["PAYMENTS_PER_30_DAYS"] = np.where(
    (
        df["EXPENDITURE_DURATION_DAYS"].notna()
        &
        df["EXPENDITURE_DURATION_DAYS"].gt(0)
    ),

    df["PAYMENT_COUNT"]
    /
    df["EXPENDITURE_DURATION_DAYS"]
    * 30,

    np.nan
)


# Disbursed amount per expenditure day

df["DISBURSED_PER_EXPENDITURE_DAY"] = np.where(
    (
        df["EXPENDITURE_DURATION_DAYS"].notna()
        &
        df["EXPENDITURE_DURATION_DAYS"].gt(0)
        &
        df["TOTAL_FUND_DISBURSED_AMT"].notna()
    ),

    df["TOTAL_FUND_DISBURSED_AMT"]
    /
    df["EXPENDITURE_DURATION_DAYS"],

    np.nan
)


# ============================================================
# SECTION 5
# COMPLETION FEATURES
# ============================================================

print("Creating completion features...")


df["IS_COMPLETED"] = (
    df["HAS_COMPLETION_RECORD"]
    .fillna(False)
    .astype(int)
)


df["HAS_ACTUAL_AMOUNT"] = (
    df["ACTUAL_AMOUNT"]
    .notna()
    .astype(int)
)


df["HAS_ACTUAL_END_DATE"] = (
    df["ACTUAL_END_DATE"]
    .notna()
    .astype(int)
)


# Actual - Sanction

df["ACTUAL_MINUS_SANCTION"] = np.where(
    (
        df["ACTUAL_AMOUNT"].notna()
        &
        df["SANCTION_AMOUNT"].notna()
    ),

    df["ACTUAL_AMOUNT"]
    -
    df["SANCTION_AMOUNT"],

    np.nan
)


# Actual - Disbursed

df["ACTUAL_MINUS_DISBURSED"] = np.where(
    (
        df["ACTUAL_AMOUNT"].notna()
        &
        df["TOTAL_FUND_DISBURSED_AMT"].notna()
    ),

    df["ACTUAL_AMOUNT"]
    -
    df["TOTAL_FUND_DISBURSED_AMT"],

    np.nan
)


# ============================================================
# SECTION 6
# GEOGRAPHIC FEATURES
# ============================================================

print("Creating geographic features...")


df["STATE_WORK_COUNT"] = (
    df.groupby("STATE_NAME")["WORK_ID"]
    .transform("count")
)


df["MP_WORK_COUNT"] = (
    df.groupby("MP_ID")["WORK_ID"]
    .transform("count")
)


df["CONSTITUENCY_WORK_COUNT"] = (
    df.groupby("CONSTITUENCY_ID")["WORK_ID"]
    .transform("count")
)


# ============================================================
# SECTION 7
# STATE FINANCIAL AGGREGATES
# ============================================================

print("Creating state-level financial aggregates...")


state_group = df.groupby(
    "STATE_NAME"
)


df["STATE_TOTAL_RECOMMENDED"] = (
    state_group["RECOMMENDED_AMOUNT"]
    .transform("sum")
)


df["STATE_TOTAL_SANCTIONED"] = (
    state_group["SANCTION_AMOUNT"]
    .transform("sum")
)


df["STATE_TOTAL_DISBURSED"] = (
    state_group["TOTAL_FUND_DISBURSED_AMT"]
    .transform("sum")
)


df["STATE_AVG_WORK_COST"] = (
    state_group["SANCTION_AMOUNT"]
    .transform("mean")
)


# ============================================================
# SECTION 8
# MP FINANCIAL AGGREGATES
# ============================================================

print("Creating MP-level financial aggregates...")


mp_group = df.groupby(
    "MP_ID"
)


df["MP_TOTAL_RECOMMENDED"] = (
    mp_group["RECOMMENDED_AMOUNT"]
    .transform("sum")
)


df["MP_TOTAL_SANCTIONED"] = (
    mp_group["SANCTION_AMOUNT"]
    .transform("sum")
)


df["MP_TOTAL_DISBURSED"] = (
    mp_group["TOTAL_FUND_DISBURSED_AMT"]
    .transform("sum")
)


df["MP_AVG_SANCTION_AMOUNT"] = (
    mp_group["SANCTION_AMOUNT"]
    .transform("mean")
)


df["MP_MEDIAN_SANCTION_AMOUNT"] = (
    mp_group["SANCTION_AMOUNT"]
    .transform("median")
)


# ============================================================
# SECTION 9
# CONSTITUENCY FINANCIAL AGGREGATES
# ============================================================

print("Creating constituency-level aggregates...")


const_group = df.groupby(
    "CONSTITUENCY_ID"
)


df["CONSTITUENCY_TOTAL_SANCTIONED"] = (
    const_group["SANCTION_AMOUNT"]
    .transform("sum")
)


df["CONSTITUENCY_TOTAL_DISBURSED"] = (
    const_group["TOTAL_FUND_DISBURSED_AMT"]
    .transform("sum")
)


df["CONSTITUENCY_AVG_SANCTION"] = (
    const_group["SANCTION_AMOUNT"]
    .transform("mean")
)


# ============================================================
# SECTION 10
# PEER GROUP
# ============================================================

print("Creating peer-group statistics...")


peer_columns = [
    "STATE_NAME",
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
]


for col in peer_columns:

    df[col] = (
        df[col]
        .fillna("UNKNOWN")
        .astype(str)
        .str.strip()
    )


peer_group = df.groupby(
    peer_columns,
    dropna=False
)


df["PEER_COUNT"] = (
    peer_group["WORK_ID"]
    .transform("count")
)


df["PEER_MEDIAN_SANCTION"] = (
    peer_group["SANCTION_AMOUNT"]
    .transform("median")
)


df["PEER_MEAN_SANCTION"] = (
    peer_group["SANCTION_AMOUNT"]
    .transform("mean")
)


df["PEER_STD_SANCTION"] = (
    peer_group["SANCTION_AMOUNT"]
    .transform("std")
)


df["PEER_MEDIAN_DISBURSED"] = (
    peer_group["TOTAL_FUND_DISBURSED_AMT"]
    .transform("median")
)


# ============================================================
# SECTION 11
# PEER COST FEATURES
# ============================================================

print("Creating peer cost features...")


df["SANCTION_TO_PEER_MEDIAN"] = safe_ratio(
    df["SANCTION_AMOUNT"],
    df["PEER_MEDIAN_SANCTION"]
)


df["DISBURSED_TO_PEER_MEDIAN"] = safe_ratio(
    df["TOTAL_FUND_DISBURSED_AMT"],
    df["PEER_MEDIAN_DISBURSED"]
)


# Peer Z-score

df["SANCTION_PEER_Z_SCORE"] = np.where(
    (
        df["SANCTION_AMOUNT"].notna()
        &
        df["PEER_MEAN_SANCTION"].notna()
        &
        df["PEER_STD_SANCTION"].notna()
        &
        df["PEER_STD_SANCTION"].gt(0)
    ),

    (
        df["SANCTION_AMOUNT"]
        -
        df["PEER_MEAN_SANCTION"]
    )
    /
    df["PEER_STD_SANCTION"],

    np.nan
)


# ============================================================
# SECTION 12
# CATEGORY / ACTIVITY FREQUENCY
# ============================================================

print("Creating category/activity frequencies...")


df["CATEGORY_WORK_COUNT"] = (
    df.groupby("WORK_CATEGORY")["WORK_ID"]
    .transform("count")
)


df["ACTIVITY_WORK_COUNT"] = (
    df.groupby("ACTIVITY_NAME")["WORK_ID"]
    .transform("count")
)


# ============================================================
# SECTION 13
# PAYMENT FLAGS
# ============================================================

print("Creating payment flags...")


df["NO_PAYMENT_RECORD"] = (
    ~df["HAS_PAYMENT_RECORD"]
).astype(int)


df["MULTIPLE_PAYMENTS"] = (
    df["PAYMENT_COUNT"]
    .fillna(0)
    .gt(1)
    .astype(int)
)


df["MULTIPLE_VENDORS"] = (
    df["UNIQUE_VENDOR_COUNT"]
    .fillna(0)
    .gt(1)
    .astype(int)
)


# ============================================================
# SECTION 14
# PAYMENT COUNT FLAGS
# ============================================================

df["PAYMENT_COUNT_GE_5"] = (
    df["PAYMENT_COUNT"]
    .fillna(0)
    .ge(5)
    .astype(int)
)


df["PAYMENT_COUNT_GE_10"] = (
    df["PAYMENT_COUNT"]
    .fillna(0)
    .ge(10)
    .astype(int)
)


# ============================================================
# SECTION 15
# VENDOR COUNT FLAGS
# ============================================================

df["VENDOR_COUNT_GE_5"] = (
    df["UNIQUE_VENDOR_COUNT"]
    .fillna(0)
    .ge(5)
    .astype(int)
)


df["VENDOR_COUNT_GE_10"] = (
    df["UNIQUE_VENDOR_COUNT"]
    .fillna(0)
    .ge(10)
    .astype(int)
)


# ============================================================
# SECTION 16
# DATA COMPLETENESS
# ============================================================

print("Creating data-quality features...")


quality_columns = [
    "WORK_DESCRIPTION",
    "WORK_STAGE",
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "TOTAL_FUND_DISBURSED_AMT",
    "FIRST_EXPENDITURE_DATE",
    "LAST_EXPENDITURE_DATE",
    "ACTUAL_AMOUNT",
    "ACTUAL_END_DATE",
]


existing_quality_columns = [
    c for c in quality_columns
    if c in df.columns
]


df["MISSING_FIELD_COUNT"] = (
    df[existing_quality_columns]
    .isna()
    .sum(axis=1)
)


df["DATA_COMPLETENESS_RATIO"] = (
    1
    -
    (
        df["MISSING_FIELD_COUNT"]
        /
        len(existing_quality_columns)
    )
)


# ============================================================
# SECTION 17
# TIMELINE CONSISTENCY FLAGS
# ============================================================

print("Creating timeline consistency flags...")


# These two are genuine chronological relationships.

df["NEGATIVE_RECOMMENDATION_TO_SANCTION"] = (
    df["RECOMMENDATION_TO_SANCTION_DAYS"]
    .notna()
    &
    df["RECOMMENDATION_TO_SANCTION_DAYS"].lt(0)
).astype(int)


df["NEGATIVE_SANCTION_TO_PAYMENT"] = (
    df["SANCTION_TO_FIRST_PAYMENT_DAYS"]
    .notna()
    &
    df["SANCTION_TO_FIRST_PAYMENT_DAYS"].lt(0)
).astype(int)


# Completion before last payment is retained separately.
#
# We do NOT automatically interpret this as fraud.
# It is a timeline/data consistency indicator.

df["COMPLETION_BEFORE_LAST_PAYMENT"] = (
    df["LAST_PAYMENT_TO_COMPLETION_DAYS"]
    .notna()
    &
    df["LAST_PAYMENT_TO_COMPLETION_DAYS"].lt(0)
).astype(int)


# Positive version for easier interpretation

df["PAYMENT_AFTER_REPORTED_COMPLETION_DAYS"] = np.where(
    (
        df["LAST_PAYMENT_TO_COMPLETION_DAYS"].notna()
        &
        df["LAST_PAYMENT_TO_COMPLETION_DAYS"].lt(0)
    ),

    -df["LAST_PAYMENT_TO_COMPLETION_DAYS"],

    np.nan
)


# ============================================================
# SECTION 18
# AMOUNT SANITY FLAGS
# ============================================================

print("Creating amount sanity flags...")


df["ACTUAL_ABOVE_SANCTION"] = (
    df["ACTUAL_AMOUNT"].notna()
    &
    df["SANCTION_AMOUNT"].notna()
    &
    df["ACTUAL_AMOUNT"].gt(
        df["SANCTION_AMOUNT"]
    )
).astype(int)


df["DISBURSED_ABOVE_SANCTION"] = (
    df["TOTAL_FUND_DISBURSED_AMT"].notna()
    &
    df["SANCTION_AMOUNT"].notna()
    &
    df["TOTAL_FUND_DISBURSED_AMT"].gt(
        df["SANCTION_AMOUNT"]
    )
).astype(int)


# ============================================================
# SECTION 19
# DATE PARTS
# ============================================================

print("Creating date features...")


df["RECOMMENDATION_YEAR"] = (
    df["RECOMMENDATION_DATE"].dt.year
)


df["RECOMMENDATION_MONTH"] = (
    df["RECOMMENDATION_DATE"].dt.month
)


df["SANCTION_YEAR"] = (
    df["SANCTION_DATE"].dt.year
)


df["FIRST_PAYMENT_YEAR"] = (
    df["FIRST_EXPENDITURE_DATE"].dt.year
)


df["COMPLETION_YEAR"] = (
    df["ACTUAL_END_DATE"].dt.year
)


# ============================================================
# SECTION 20
# ADDITIONAL HIGH-VALUE FEATURES
# ============================================================

print("Creating additional analytical features...")


# ------------------------------------------------------------
# Disbursement completion relationship
# ------------------------------------------------------------

df["DISBURSED_MINUS_ACTUAL"] = np.where(
    (
        df["TOTAL_FUND_DISBURSED_AMT"].notna()
        &
        df["ACTUAL_AMOUNT"].notna()
    ),

    df["TOTAL_FUND_DISBURSED_AMT"]
    -
    df["ACTUAL_AMOUNT"],

    np.nan
)


# ------------------------------------------------------------
# Absolute peer deviation
# ------------------------------------------------------------

df["ABS_PEER_COST_Z_SCORE"] = (
    df["SANCTION_PEER_Z_SCORE"]
    .abs()
)


# ------------------------------------------------------------
# High peer-cost flags
# ------------------------------------------------------------

df["SANCTION_ABOVE_2X_PEER_MEDIAN"] = (
    df["SANCTION_TO_PEER_MEDIAN"]
    .gt(2)
    .astype(int)
)


df["SANCTION_ABOVE_5X_PEER_MEDIAN"] = (
    df["SANCTION_TO_PEER_MEDIAN"]
    .gt(5)
    .astype(int)
)


# ------------------------------------------------------------
# High disbursement peer flags
# ------------------------------------------------------------

df["DISBURSED_ABOVE_2X_PEER_MEDIAN"] = (
    df["DISBURSED_TO_PEER_MEDIAN"]
    .gt(2)
    .astype(int)
)


# ------------------------------------------------------------
# Large transaction flags
# ------------------------------------------------------------

df["AVERAGE_PAYMENT_ABOVE_1M"] = (
    df["AVERAGE_PAYMENT_AMOUNT"]
    .gt(1_000_000)
    .astype(int)
)


df["TOTAL_DISBURSED_ABOVE_5M"] = (
    df["TOTAL_FUND_DISBURSED_AMT"]
    .gt(5_000_000)
    .astype(int)
)


# ============================================================
# SECTION 21
# DATE FORMAT
# ============================================================

for col in date_columns:

    df[col] = df[col].dt.strftime(
        "%Y-%m-%d"
    )


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("FEATURE DATASET VALIDATION")
print("=" * 70)


print(
    f"\nRows: {len(df):,}"
)

print(
    f"Columns: {len(df.columns):,}"
)

print(
    "Unique WORK_ID:",
    df["WORK_ID"].nunique()
)

print(
    "Missing WORK_ID:",
    df["WORK_ID"].isna().sum()
)

print(
    "Duplicate WORK_ID:",
    df["WORK_ID"].duplicated().sum()
)


# ============================================================
# NUMERIC QUALITY
# ============================================================

feature_numeric = df.select_dtypes(
    include=[np.number]
)


print(
    "\nNumeric feature columns:",
    len(feature_numeric.columns)
)


infinite_count = np.isinf(
    feature_numeric.to_numpy()
).sum()


print(
    "Infinite values:",
    infinite_count
)


# ============================================================
# TIMELINE CHECK
# ============================================================

print("\nTimeline consistency:")

print(
    "Negative recommendation -> sanction:",
    df["NEGATIVE_RECOMMENDATION_TO_SANCTION"].sum()
)

print(
    "Negative sanction -> payment:",
    df["NEGATIVE_SANCTION_TO_PAYMENT"].sum()
)

print(
    "Completion before last payment:",
    df["COMPLETION_BEFORE_LAST_PAYMENT"].sum()
)


# ============================================================
# PEER COVERAGE
# ============================================================

print("\nPeer statistics:")


print(
    "Works with peer median:",
    df["PEER_MEDIAN_SANCTION"].notna().sum()
)


print(
    "Works with peer count >= 10:",
    df["PEER_COUNT"].ge(10).sum()
)


print(
    "Works with peer count >= 30:",
    df["PEER_COUNT"].ge(30).sum()
)


# ============================================================
# FINANCIAL SANITY
# ============================================================

print("\nFinancial sanity:")


print(
    "Actual above sanction:",
    df["ACTUAL_ABOVE_SANCTION"].sum()
)


print(
    "Disbursed above sanction:",
    df["DISBURSED_ABOVE_SANCTION"].sum()
)


# ============================================================
# PAYMENT FEATURES
# ============================================================

print("\nPayment features:")


print(
    "Multiple-payment works:",
    df["MULTIPLE_PAYMENTS"].sum()
)


print(
    "Works with >=5 payments:",
    df["PAYMENT_COUNT_GE_5"].sum()
)


print(
    "Works with >=10 payments:",
    df["PAYMENT_COUNT_GE_10"].sum()
)


print(
    "Works with >=5 vendors:",
    df["VENDOR_COUNT_GE_5"].sum()
)


print(
    "Works with >=10 vendors:",
    df["VENDOR_COUNT_GE_10"].sum()
)


# ============================================================
# PEER COST FLAGS
# ============================================================

print("\nPeer cost flags:")


print(
    "Sanction >2x peer median:",
    df["SANCTION_ABOVE_2X_PEER_MEDIAN"].sum()
)


print(
    "Sanction >5x peer median:",
    df["SANCTION_ABOVE_5X_PEER_MEDIAN"].sum()
)


print(
    "Disbursed >2x peer median:",
    df["DISBURSED_ABOVE_2X_PEER_MEDIAN"].sum()
)


# ============================================================
# DATA COMPLETENESS
# ============================================================

print("\nData completeness:")


print(
    "Average completeness:",
    f"{df['DATA_COMPLETENESS_RATIO'].mean() * 100:.2f}%"
)


print(
    "Minimum completeness:",
    f"{df['DATA_COMPLETENESS_RATIO'].min() * 100:.2f}%"
)


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\n" + "=" * 70)

print(
    "Saved India feature dataset:"
)

print(OUTPUT_FILE)

print("=" * 70)