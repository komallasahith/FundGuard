import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = BASE_DIR / "data" / "processed" / "mplads_works_raw_combined.csv"

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_expenditure.csv"
)

TRANSACTION_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_payment_transactions.csv"
)


# ============================================================
# HELPERS
# ============================================================

def clean_numeric(series):
    """
    Convert values to numeric safely.
    Invalid values become NaN.
    """
    return pd.to_numeric(series, errors="coerce")


def clean_date(series):
    """
    Convert dates safely.
    """
    return pd.to_datetime(series, errors="coerce", dayfirst=True)


def sum_preserve_nan(series):
    """
    Sum values while preserving NaN when the entire group is missing.
    """
    if series.notna().any():
        return series.sum()
    return np.nan


def first_non_null(series):
    """
    Return first non-null value.
    """
    values = series.dropna()

    if len(values) == 0:
        return np.nan

    return values.iloc[0]


# ============================================================
# LOAD RAW DATA
# ============================================================

print("=" * 70)
print("FUNDGUARD INDIA EXPENDITURE DATASET BUILDER")
print("=" * 70)

print("\nLoading raw data...")

df = pd.read_csv(RAW_FILE, low_memory=False)

print(f"Raw records: {len(df):,}")


# ============================================================
# BASIC VALIDATION
# ============================================================

required_columns = [
    "WORK_RECOMMENDATION_DTL_ID",
    "WORK_ID",
    "FUND_DISBURSED_AMT",
    "EXPENDITURE_DATE",
    "VENDOR_ID",
    "VENDOR_NAME",
    "WORK_STATUS",
    "STATE_NAME",
    "MP_NAME",
    "CONSTITUENCY",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ============================================================
# CANONICAL WORK ID
# ============================================================

df["WORK_RECOMMENDATION_DTL_ID"] = clean_numeric(
    df["WORK_RECOMMENDATION_DTL_ID"]
)

print(
    "Valid canonical work IDs:",
    df["WORK_RECOMMENDATION_DTL_ID"].notna().sum()
)


# ============================================================
# PAYMENT RECORDS
# ============================================================

payment_mask = df["FUND_DISBURSED_AMT"].notna()

payments = df.loc[payment_mask].copy()

print(f"\nPayment records: {len(payments):,}")


if len(payments) == 0:
    raise ValueError("No payment records found.")


# ============================================================
# CLEAN PAYMENT FIELDS
# ============================================================

payments["FUND_DISBURSED_AMT"] = clean_numeric(
    payments["FUND_DISBURSED_AMT"]
)

payments["EXPENDITURE_DATE"] = clean_date(
    payments["EXPENDITURE_DATE"]
)


# ============================================================
# PAYMENT TRANSACTION DATASET
# ============================================================

print("\nBuilding payment transaction dataset...")

transaction_columns = [
    "WORK_RECOMMENDATION_DTL_ID",
    "WORK_ID",
    "STATE_NAME",
    "MP_NAME",
    "CONSTITUENCY",
    "ACTIVITY_NAME",
    "LETTER_NO",
    "FUND_DISBURSED_AMT",
    "EXPENDITURE_DATE",
    "VENDOR_ID",
    "VENDOR_NAME",
    "IA_NAME",
    "IDA_NAME",
    "WORK_STATUS",
    "HOUSE_OF_PARLIAMENT",
    "TENURE",
    "_STATE_ID",
    "_MP_ID",
    "_CONSTITUENCY_ID",
    "_SOURCE_KEY",
]

transaction_columns = [
    col for col in transaction_columns
    if col in payments.columns
]

transactions = payments[transaction_columns].copy()

transactions = transactions.sort_values(
    by=[
        "WORK_RECOMMENDATION_DTL_ID",
        "EXPENDITURE_DATE"
    ],
    na_position="last"
)

transactions.to_csv(
    TRANSACTION_FILE,
    index=False
)

print(
    f"Payment transactions saved: "
    f"{TRANSACTION_FILE}"
)

print(
    f"Transaction rows: {len(transactions):,}"
)


# ============================================================
# AGGREGATE PAYMENTS PER WORK
# ============================================================

print("\nAggregating payments by canonical WORK ID...")

payment_group = payments.groupby(
    "WORK_RECOMMENDATION_DTL_ID",
    dropna=False
)


payment_agg = payment_group.agg(

    # --------------------------------------------------------
    # Financial
    # --------------------------------------------------------

    TOTAL_FUND_DISBURSED_AMT=(
        "FUND_DISBURSED_AMT",
        sum_preserve_nan
    ),

    PAYMENT_COUNT=(
        "FUND_DISBURSED_AMT",
        "count"
    ),

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    FIRST_EXPENDITURE_DATE=(
        "EXPENDITURE_DATE",
        "min"
    ),

    LAST_EXPENDITURE_DATE=(
        "EXPENDITURE_DATE",
        "max"
    ),

    # --------------------------------------------------------
    # Vendors
    # --------------------------------------------------------

    UNIQUE_VENDOR_COUNT=(
        "VENDOR_ID",
        lambda x: x.dropna().nunique()
    ),

    UNIQUE_VENDOR_NAME_COUNT=(
        "VENDOR_NAME",
        lambda x: x.dropna().nunique()
    ),

    # --------------------------------------------------------
    # Payment statuses
    # --------------------------------------------------------

    PAYMENT_SUCCESS_COUNT=(
        "WORK_STATUS",
        lambda x: (
            x.astype(str)
            .str.strip()
            .str.lower()
            .eq("payment success")
            .sum()
        )
    ),

    PAYMENT_IN_PROGRESS_COUNT=(
        "WORK_STATUS",
        lambda x: (
            x.astype(str)
            .str.strip()
            .str.lower()
            .eq("payment in-progress")
            .sum()
        )
    ),

    # --------------------------------------------------------
    # Reference information
    # --------------------------------------------------------

    PAYMENT_WORK_ID=(
        "WORK_ID",
        first_non_null
    ),

    PAYMENT_STATE_NAME=(
        "STATE_NAME",
        first_non_null
    ),

    PAYMENT_MP_NAME=(
        "MP_NAME",
        first_non_null
    ),

    PAYMENT_CONSTITUENCY=(
        "CONSTITUENCY",
        first_non_null
    ),

    PAYMENT_ACTIVITY_NAME=(
        "ACTIVITY_NAME",
        first_non_null
    ),

    PAYMENT_LETTER_NO=(
        "LETTER_NO",
        first_non_null
    ),

    PAYMENT_IA_NAME=(
        "IA_NAME",
        first_non_null
    ),

    PAYMENT_IDA_NAME=(
        "IDA_NAME",
        first_non_null
    ),

    PAYMENT_WORK_STATUS=(
        "WORK_STATUS",
        first_non_null
    ),
).reset_index()


# ============================================================
# LOAD WORK MASTER
# ============================================================

WORK_MASTER_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_work_master.csv"
)

print("\nLoading India work master...")

master = pd.read_csv(
    WORK_MASTER_FILE,
    low_memory=False
)

master["WORK_ID"] = clean_numeric(
    master["WORK_ID"]
)

print(
    f"Work master rows: {len(master):,}"
)


# ============================================================
# VALIDATE MASTER IDs
# ============================================================

if master["WORK_ID"].duplicated().any():

    duplicates = master[
        master["WORK_ID"].duplicated(keep=False)
    ]

    raise ValueError(
        "Duplicate WORK_ID values found in work master.\n"
        f"Duplicates: {len(duplicates):,}"
    )


# ============================================================
# MERGE PAYMENT DATA
# ============================================================

print("\nMerging payment information into work master...")

expenditure = master.merge(
    payment_agg,
    how="left",
    left_on="WORK_ID",
    right_on="WORK_RECOMMENDATION_DTL_ID",
    validate="one_to_one"
)


# ============================================================
# REMOVE REDUNDANT JOIN COLUMN
# ============================================================

expenditure.drop(
    columns=["WORK_RECOMMENDATION_DTL_ID"],
    inplace=True
)


# ============================================================
# FINANCIAL DERIVED FEATURES
# ============================================================

print("\nCalculating financial indicators...")


# ------------------------------------------------------------
# Payment availability
# ------------------------------------------------------------

expenditure["HAS_PAYMENT_RECORD"] = (
    expenditure["PAYMENT_COUNT"]
    .fillna(0)
    .gt(0)
)


# ------------------------------------------------------------
# Total disbursed / sanctioned ratio
# ------------------------------------------------------------

expenditure["DISBURSED_TO_SANCTION_RATIO"] = np.where(
    expenditure["SANCTION_AMOUNT"].notna()
    & expenditure["SANCTION_AMOUNT"].gt(0)
    & expenditure["TOTAL_FUND_DISBURSED_AMT"].notna(),

    expenditure["TOTAL_FUND_DISBURSED_AMT"]
    / expenditure["SANCTION_AMOUNT"],

    np.nan
)


# ------------------------------------------------------------
# Remaining sanctioned amount
# ------------------------------------------------------------

expenditure["REMAINING_SANCTION_AMOUNT"] = np.where(
    expenditure["SANCTION_AMOUNT"].notna()
    & expenditure["TOTAL_FUND_DISBURSED_AMT"].notna(),

    expenditure["SANCTION_AMOUNT"]
    - expenditure["TOTAL_FUND_DISBURSED_AMT"],

    np.nan
)


# ------------------------------------------------------------
# Payment duration
# ------------------------------------------------------------

expenditure["EXPENDITURE_DURATION_DAYS"] = (
    expenditure["LAST_EXPENDITURE_DATE"]
    - expenditure["FIRST_EXPENDITURE_DATE"]
).dt.days


# ------------------------------------------------------------
# Payment frequency
# ------------------------------------------------------------

expenditure["PAYMENTS_PER_100_DAYS"] = np.where(
    expenditure["EXPENDITURE_DURATION_DAYS"].notna()
    & expenditure["EXPENDITURE_DURATION_DAYS"].gt(0),

    expenditure["PAYMENT_COUNT"]
    / expenditure["EXPENDITURE_DURATION_DAYS"]
    * 100,

    np.nan
)


# ============================================================
# DATE FORMATTING
# ============================================================

date_columns = [
    "FIRST_EXPENDITURE_DATE",
    "LAST_EXPENDITURE_DATE",
]

for col in date_columns:

    if col in expenditure.columns:

        expenditure[col] = expenditure[col].dt.strftime(
            "%Y-%m-%d"
        )


# ============================================================
# COLUMN ORDER
# ============================================================

preferred_columns = [
    # Identity
    "WORK_ID",

    # Geography
    "STATE_ID",
    "STATE_NAME",
    "CONSTITUENCY_ID",
    "CONSTITUENCY",
    "MP_ID",
    "MP_NAME",

    # Work
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
    "WORK_DESCRIPTION",
    "WORK_STAGE",
    "SOURCE_KEY",

    # Recommended / sanctioned
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",

    # Payment
    "HAS_PAYMENT_RECORD",
    "PAYMENT_WORK_ID",
    "TOTAL_FUND_DISBURSED_AMT",
    "PAYMENT_COUNT",

    # Payment dates
    "FIRST_EXPENDITURE_DATE",
    "LAST_EXPENDITURE_DATE",
    "EXPENDITURE_DURATION_DAYS",

    # Financial ratios
    "DISBURSED_TO_SANCTION_RATIO",
    "REMAINING_SANCTION_AMOUNT",

    # Vendors
    "UNIQUE_VENDOR_COUNT",
    "UNIQUE_VENDOR_NAME_COUNT",

    # Payment status
    "PAYMENT_SUCCESS_COUNT",
    "PAYMENT_IN_PROGRESS_COUNT",
    "PAYMENT_WORK_STATUS",

    # Payment metadata
    "PAYMENT_IA_NAME",
    "PAYMENT_IDA_NAME",
    "PAYMENT_LETTER_NO",
    "PAYMENT_ACTIVITY_NAME",

    # Existing completed-work fields if present
    "ATTACH_ID",
    "FILE_STATUS",
    "FLAG",
    "HOUSE_OF_PARLIAMENT",
    "IDA_NAME",
    "LETTER_NO",
    "TENURE",
    "TENURE_START_DATE",
    "TENURE_END_DATE",
]


preferred_columns = [
    col for col in preferred_columns
    if col in expenditure.columns
]

remaining_columns = [
    col for col in expenditure.columns
    if col not in preferred_columns
]

expenditure = expenditure[
    preferred_columns + remaining_columns
]


# ============================================================
# SAVE
# ============================================================

expenditure.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# VALIDATION / SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("EXPENDITURE DATASET VALIDATION")
print("=" * 70)

print(
    f"\nFinal rows: {len(expenditure):,}"
)

print(
    f"Final columns: {len(expenditure.columns):,}"
)

print(
    f"Unique WORK_ID: "
    f"{expenditure['WORK_ID'].nunique():,}"
)

print(
    f"Missing WORK_ID: "
    f"{expenditure['WORK_ID'].isna().sum():,}"
)

print(
    f"Duplicate WORK_ID: "
    f"{expenditure['WORK_ID'].duplicated().sum():,}"
)


# ------------------------------------------------------------
# Payment coverage
# ------------------------------------------------------------

payment_works = expenditure[
    expenditure["HAS_PAYMENT_RECORD"]
]

no_payment_works = expenditure[
    ~expenditure["HAS_PAYMENT_RECORD"]
]

print("\nPayment coverage:")

print(
    f"Works with payment records: "
    f"{len(payment_works):,}"
)

print(
    f"Works without payment records: "
    f"{len(no_payment_works):,}"
)

print(
    f"Payment coverage: "
    f"{len(payment_works) / len(expenditure) * 100:.2f}%"
)


# ------------------------------------------------------------
# Payment totals
# ------------------------------------------------------------

print("\nPayment statistics:")

print(
    f"Payment transactions: "
    f"{len(transactions):,}"
)

print(
    f"Unique payment works: "
    f"{payments['WORK_RECOMMENDATION_DTL_ID'].nunique():,}"
)

print(
    f"Total disbursed amount: "
    f"{payment_agg['TOTAL_FUND_DISBURSED_AMT'].sum():,.2f}"
)

print(
    f"Maximum payments for one work: "
    f"{payment_agg['PAYMENT_COUNT'].max():,}"
)

print(
    f"Average payments per paid work: "
    f"{payment_agg['PAYMENT_COUNT'].mean():.2f}"
)

print(
    f"Median payments per paid work: "
    f"{payment_agg['PAYMENT_COUNT'].median():.0f}"
)


# ------------------------------------------------------------
# Payment count distribution
# ------------------------------------------------------------

print("\nPayment count distribution:")

print(
    payment_agg["PAYMENT_COUNT"]
    .value_counts()
    .sort_index()
    .head(20)
    .to_string()
)


# ------------------------------------------------------------
# Date coverage
# ------------------------------------------------------------

print("\nExpenditure dates:")

print(
    "First expenditure date:",
    expenditure["FIRST_EXPENDITURE_DATE"].min()
)

print(
    "Last expenditure date:",
    expenditure["LAST_EXPENDITURE_DATE"].max()
)


# ------------------------------------------------------------
# Vendor coverage
# ------------------------------------------------------------

print("\nVendor information:")

print(
    "Works with vendor information:",
    (expenditure["UNIQUE_VENDOR_COUNT"] > 0).sum()
)

print(
    "Maximum vendors for one work:",
    expenditure["UNIQUE_VENDOR_COUNT"].max()
)


# ------------------------------------------------------------
# Status
# ------------------------------------------------------------

print("\nPayment status:")

print(
    "Successful payments:",
    int(
        expenditure["PAYMENT_SUCCESS_COUNT"]
        .fillna(0)
        .sum()
    )
)

print(
    "In-progress payments:",
    int(
        expenditure["PAYMENT_IN_PROGRESS_COUNT"]
        .fillna(0)
        .sum()
    )
)


# ------------------------------------------------------------
# Ratio sanity checks
# ------------------------------------------------------------

ratio = expenditure[
    "DISBURSED_TO_SANCTION_RATIO"
]

print("\nDisbursement / sanction ratio:")

print(
    "Available:",
    ratio.notna().sum()
)

print(
    "Min:",
    ratio.min()
)

print(
    "Median:",
    ratio.median()
)

print(
    "Max:",
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
# FINAL
# ============================================================

print("\n" + "=" * 70)

print(
    f"Saved work-level expenditure dataset:\n"
    f"{OUTPUT_FILE}"
)

print(
    f"\nSaved payment transaction dataset:\n"
    f"{TRANSACTION_FILE}"
)

print("=" * 70)