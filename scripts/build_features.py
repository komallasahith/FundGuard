import pandas as pd
import numpy as np
from pathlib import Path


# =========================================================
# CONFIGURATION
# =========================================================

WORK_FILE = Path("data/processed/mplads_work_master.csv")
EXP_FILE = Path("data/processed/mplads_expenditure_transactions.csv")
OUTPUT_FILE = Path("data/processed/mplads_features.csv")

WORK_KEY = "WORK_RECOMMENDATION_DTL_ID"

# Minimum number of OTHER works required for a reliable peer group.
MIN_PEERS = 10


# =========================================================
# HEADER
# =========================================================

print("=" * 75)
print("FUNDGUARD AI — PHASE 2.4")
print("FEATURE ENGINEERING")
print("=" * 75)


# =========================================================
# 1. LOAD DATA
# =========================================================

if not WORK_FILE.exists():
    raise FileNotFoundError(
        f"Work master not found: {WORK_FILE}"
    )

if not EXP_FILE.exists():
    raise FileNotFoundError(
        f"Expenditure dataset not found: {EXP_FILE}"
    )


work = pd.read_csv(WORK_FILE)
exp = pd.read_csv(EXP_FILE)

print(f"\nWork master records: {len(work):,}")
print(f"Expenditure records: {len(exp):,}")


# =========================================================
# 2. BASIC COLUMN CHECK
# =========================================================

required_work_columns = [
    WORK_KEY,
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "ACTUAL_END_DATE",
    "STATE_NAME",
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
]

required_exp_columns = [
    WORK_KEY,
    "FUND_DISBURSED_AMT",
    "VENDOR_ID",
    "EXPENDITURE_DATE",
]


missing_work = [
    c for c in required_work_columns
    if c not in work.columns
]

missing_exp = [
    c for c in required_exp_columns
    if c not in exp.columns
]

if missing_work:
    raise ValueError(
        f"Missing columns in work master: {missing_work}"
    )

if missing_exp:
    raise ValueError(
        f"Missing columns in expenditure data: {missing_exp}"
    )


# =========================================================
# 3. NUMERIC CONVERSION
# =========================================================

for column in [
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
]:
    work[column] = pd.to_numeric(
        work[column],
        errors="coerce"
    )


exp["FUND_DISBURSED_AMT"] = pd.to_numeric(
    exp["FUND_DISBURSED_AMT"],
    errors="coerce"
)


# =========================================================
# 4. VALIDATED EXPENDITURE DUPLICATE REMOVAL
# =========================================================
#
# We found one exact duplicated expenditure transaction
# during validation:
#
# WORK = 250877
# VENDOR = 79135
# AMOUNT = 2841850
#
# Keep the raw source unchanged.
# Remove only the extra copy for financial aggregation.
# =========================================================

duplicate_mask = (
    (exp[WORK_KEY] == 250877)
    & (exp["VENDOR_ID"] == 79135)
    & (exp["FUND_DISBURSED_AMT"] == 2841850)
)

duplicate_indices = exp.index[duplicate_mask].tolist()

removed_duplicates = 0

if len(duplicate_indices) > 1:

    exp = exp.drop(
        duplicate_indices[1:]
    )

    removed_duplicates = len(duplicate_indices) - 1

print(
    f"\nValidated expenditure duplicates removed: "
    f"{removed_duplicates}"
)


# =========================================================
# 5. EXPENDITURE AGGREGATION
# =========================================================

exp_summary = (
    exp.groupby(WORK_KEY)
    .agg(
        TOTAL_DISBURSED=(
            "FUND_DISBURSED_AMT",
            "sum"
        ),

        TRANSACTION_COUNT=(
            "FUND_DISBURSED_AMT",
            "count"
        ),

        AVERAGE_TRANSACTION_AMOUNT=(
            "FUND_DISBURSED_AMT",
            "mean"
        ),

        MAX_TRANSACTION_AMOUNT=(
            "FUND_DISBURSED_AMT",
            "max"
        ),

        MIN_TRANSACTION_AMOUNT=(
            "FUND_DISBURSED_AMT",
            "min"
        ),

        VENDOR_COUNT=(
            "VENDOR_ID",
            "nunique"
        ),

        EXPENDITURE_DATE_COUNT=(
            "EXPENDITURE_DATE",
            "nunique"
        ),
    )
    .reset_index()
)

print(
    f"Works with expenditure records: "
    f"{len(exp_summary):,}"
)


# =========================================================
# 6. MERGE WORK + EXPENDITURE
# =========================================================

features = work.merge(
    exp_summary,
    on=WORK_KEY,
    how="left"
)

print(
    f"Feature rows after merge: "
    f"{len(features):,}"
)


# =========================================================
# 7. DEFAULT EXPENDITURE FEATURES
# =========================================================

count_columns = [
    "TRANSACTION_COUNT",
    "VENDOR_COUNT",
    "EXPENDITURE_DATE_COUNT",
]

for column in count_columns:

    features[column] = (
        features[column]
        .fillna(0)
        .astype(int)
    )


amount_columns = [
    "TOTAL_DISBURSED",
    "AVERAGE_TRANSACTION_AMOUNT",
    "MAX_TRANSACTION_AMOUNT",
    "MIN_TRANSACTION_AMOUNT",
]

for column in amount_columns:

    features[column] = (
        features[column]
        .fillna(0)
    )


# =========================================================
# 8. DATE CONVERSION
# =========================================================
#
# Work master already stores dates as:
#
# YYYY-MM-DD
#
# Example:
# 2025-04-17
#
# Do NOT use dayfirst=True or %d-%b-%Y here.
# =========================================================

date_columns = [
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "ACTUAL_END_DATE",
]

for column in date_columns:

    features[column] = pd.to_datetime(
        features[column],
        errors="coerce"
    )


# =========================================================
# 9. TIMELINE FEATURES
# =========================================================

features["RECOMMENDATION_TO_SANCTION_DAYS"] = (
    features["SANCTION_DATE"]
    - features["RECOMMENDATION_DATE"]
).dt.days


features["SANCTION_TO_COMPLETION_DAYS"] = (
    features["ACTUAL_END_DATE"]
    - features["SANCTION_DATE"]
).dt.days


features["RECOMMENDATION_TO_COMPLETION_DAYS"] = (
    features["ACTUAL_END_DATE"]
    - features["RECOMMENDATION_DATE"]
).dt.days


# =========================================================
# 10. CHRONOLOGY / DATA QUALITY FLAGS
# =========================================================

features["INVALID_RECOMMENDATION_SANCTION_ORDER"] = (
    (
        features["SANCTION_DATE"].notna()
    )
    &
    (
        features["RECOMMENDATION_DATE"].notna()
    )
    &
    (
        features["SANCTION_DATE"]
        < features["RECOMMENDATION_DATE"]
    )
).astype(int)


features["INVALID_SANCTION_COMPLETION_ORDER"] = (
    (
        features["SANCTION_DATE"].notna()
    )
    &
    (
        features["ACTUAL_END_DATE"].notna()
    )
    &
    (
        features["ACTUAL_END_DATE"]
        < features["SANCTION_DATE"]
    )
).astype(int)


features["INVALID_RECOMMENDATION_COMPLETION_ORDER"] = (
    (
        features["RECOMMENDATION_DATE"].notna()
    )
    &
    (
        features["ACTUAL_END_DATE"].notna()
    )
    &
    (
        features["ACTUAL_END_DATE"]
        < features["RECOMMENDATION_DATE"]
    )
).astype(int)


features["NEGATIVE_TIMELINE_FLAG"] = (
    (
        features[
            "INVALID_RECOMMENDATION_SANCTION_ORDER"
        ]
        == 1
    )
    |
    (
        features[
            "INVALID_SANCTION_COMPLETION_ORDER"
        ]
        == 1
    )
    |
    (
        features[
            "INVALID_RECOMMENDATION_COMPLETION_ORDER"
        ]
        == 1
    )
).astype(int)


# =========================================================
# 11. FINANCIAL FEATURES
# =========================================================

features["RECOMMENDATION_TO_SANCTION_RATIO"] = np.where(
    features["RECOMMENDED_AMOUNT"] > 0,
    features["SANCTION_AMOUNT"]
    / features["RECOMMENDED_AMOUNT"],
    np.nan
)


features["ACTUAL_TO_SANCTION_RATIO"] = np.where(
    features["SANCTION_AMOUNT"] > 0,
    features["ACTUAL_AMOUNT"]
    / features["SANCTION_AMOUNT"],
    np.nan
)


features["DISBURSEMENT_TO_SANCTION_RATIO"] = np.where(
    features["SANCTION_AMOUNT"] > 0,
    features["TOTAL_DISBURSED"]
    / features["SANCTION_AMOUNT"],
    np.nan
)


features["UNSPENT_AMOUNT"] = (
    features["SANCTION_AMOUNT"]
    - features["TOTAL_DISBURSED"]
)


features["SANCTION_DEVIATION"] = (
    features["SANCTION_AMOUNT"]
    - features["RECOMMENDED_AMOUNT"]
)


features["ACTUAL_DEVIATION"] = (
    features["ACTUAL_AMOUNT"]
    - features["SANCTION_AMOUNT"]
)


features["SANCTION_MINUS_RECOMMENDED"] = (
    features["SANCTION_AMOUNT"]
    - features["RECOMMENDED_AMOUNT"]
)


features["SANCTION_MINUS_ACTUAL"] = (
    features["SANCTION_AMOUNT"]
    - features["ACTUAL_AMOUNT"]
)


# =========================================================
# 12. DATA AVAILABILITY FLAGS
# =========================================================

features["MISSING_RECOMMENDATION_DATE"] = (
    features["RECOMMENDATION_DATE"]
    .isna()
    .astype(int)
)


features["MISSING_SANCTION_DATE"] = (
    features["SANCTION_DATE"]
    .isna()
    .astype(int)
)


features["MISSING_COMPLETION_DATE"] = (
    features["ACTUAL_END_DATE"]
    .isna()
    .astype(int)
)


features["MISSING_RECOMMENDED_AMOUNT"] = (
    features["RECOMMENDED_AMOUNT"]
    .isna()
    .astype(int)
)


features["MISSING_SANCTION_AMOUNT"] = (
    features["SANCTION_AMOUNT"]
    .isna()
    .astype(int)
)


features["MISSING_ACTUAL_AMOUNT"] = (
    features["ACTUAL_AMOUNT"]
    .isna()
    .astype(int)
)


# =========================================================
# 13. LOG TRANSFORMATIONS
# =========================================================

log_columns = [
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "TOTAL_DISBURSED",
]

for column in log_columns:

    features[f"LOG_{column}"] = np.log1p(
        features[column].clip(lower=0)
    )


# =========================================================
# 14. ROBUST PEER BENCHMARKING
# =========================================================
#
# Hierarchy:
#
# Level 1:
# STATE + WORK_CATEGORY + ACTIVITY_NAME
#
# If insufficient peers:
#
# Level 2:
# STATE + WORK_CATEGORY
#
# If still insufficient:
#
# Level 3:
# WORK_CATEGORY
#
# Minimum peers = 10
#
# The current work is excluded from the peer count.
#
# =========================================================


features["PEER_MEDIAN_SANCTION"] = np.nan
features["PEER_MEAN_SANCTION"] = np.nan
features["PEER_STD_SANCTION"] = np.nan
features["PEER_COUNT"] = 0
features["PEER_LEVEL"] = "NONE"


def calculate_peer_stats(df, group_columns):

    grouped = (
        df.groupby(
            group_columns,
            dropna=False
        )["SANCTION_AMOUNT"]
        .agg(
            PEER_MEDIAN_SANCTION="median",
            PEER_MEAN_SANCTION="mean",
            PEER_STD_SANCTION="std",
            PEER_COUNT="count",
        )
    )

    stats = df[
        group_columns
    ].merge(
        grouped,
        left_on=group_columns,
        right_index=True,
        how="left",
        sort=False
    )

    stats.index = df.index

    return stats


valid_sanction = (
    features["SANCTION_AMOUNT"].notna()
)


# ---------------------------------------------------------
# LEVEL 1
# ---------------------------------------------------------

level1 = [
    "STATE_NAME",
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
]

stats1 = calculate_peer_stats(
    features,
    level1
)


mask1 = (
    valid_sanction
    &
    (
        stats1["PEER_COUNT"]
        - 1
        >= MIN_PEERS
    )
)


features.loc[mask1, "PEER_MEDIAN_SANCTION"] = (
    stats1.loc[
        mask1,
        "PEER_MEDIAN_SANCTION"
    ]
)


features.loc[mask1, "PEER_MEAN_SANCTION"] = (
    stats1.loc[
        mask1,
        "PEER_MEAN_SANCTION"
    ]
)


features.loc[mask1, "PEER_STD_SANCTION"] = (
    stats1.loc[
        mask1,
        "PEER_STD_SANCTION"
    ]
)


features.loc[mask1, "PEER_COUNT"] = (
    stats1.loc[
        mask1,
        "PEER_COUNT"
    ]
    - 1
)


features.loc[mask1, "PEER_LEVEL"] = (
    "STATE_CATEGORY_ACTIVITY"
)


# ---------------------------------------------------------
# LEVEL 2 FALLBACK
# ---------------------------------------------------------

remaining = (
    valid_sanction
    &
    features["PEER_MEDIAN_SANCTION"].isna()
)


level2 = [
    "STATE_NAME",
    "WORK_CATEGORY",
]


stats2 = calculate_peer_stats(
    features,
    level2
)


mask2 = (
    remaining
    &
    (
        stats2["PEER_COUNT"]
        - 1
        >= MIN_PEERS
    )
)


features.loc[mask2, "PEER_MEDIAN_SANCTION"] = (
    stats2.loc[
        mask2,
        "PEER_MEDIAN_SANCTION"
    ]
)


features.loc[mask2, "PEER_MEAN_SANCTION"] = (
    stats2.loc[
        mask2,
        "PEER_MEAN_SANCTION"
    ]
)


features.loc[mask2, "PEER_STD_SANCTION"] = (
    stats2.loc[
        mask2,
        "PEER_STD_SANCTION"
    ]
)


features.loc[mask2, "PEER_COUNT"] = (
    stats2.loc[
        mask2,
        "PEER_COUNT"
    ]
    - 1
)


features.loc[mask2, "PEER_LEVEL"] = (
    "STATE_CATEGORY"
)


# ---------------------------------------------------------
# LEVEL 3 FALLBACK
# ---------------------------------------------------------

remaining = (
    valid_sanction
    &
    features["PEER_MEDIAN_SANCTION"].isna()
)


level3 = [
    "WORK_CATEGORY",
]


stats3 = calculate_peer_stats(
    features,
    level3
)


mask3 = (
    remaining
    &
    (
        stats3["PEER_COUNT"]
        - 1
        >= MIN_PEERS
    )
)


features.loc[mask3, "PEER_MEDIAN_SANCTION"] = (
    stats3.loc[
        mask3,
        "PEER_MEDIAN_SANCTION"
    ]
)


features.loc[mask3, "PEER_MEAN_SANCTION"] = (
    stats3.loc[
        mask3,
        "PEER_MEAN_SANCTION"
    ]
)


features.loc[mask3, "PEER_STD_SANCTION"] = (
    stats3.loc[
        mask3,
        "PEER_STD_SANCTION"
    ]
)


features.loc[mask3, "PEER_COUNT"] = (
    stats3.loc[
        mask3,
        "PEER_COUNT"
    ]
    - 1
)


features.loc[mask3, "PEER_LEVEL"] = (
    "CATEGORY"
)


# =========================================================
# 15. PEER COST FEATURES
# =========================================================

features["COST_VS_PEER_MEDIAN"] = np.where(
    features["PEER_MEDIAN_SANCTION"] > 0,

    features["SANCTION_AMOUNT"]
    / features["PEER_MEDIAN_SANCTION"],

    np.nan
)


features["COST_Z_SCORE"] = np.where(
    features["PEER_STD_SANCTION"] > 0,

    (
        features["SANCTION_AMOUNT"]
        - features["PEER_MEAN_SANCTION"]
    )
    / features["PEER_STD_SANCTION"],

    np.nan
)


features["PEER_GROUP_RELIABLE_FLAG"] = (
    features["PEER_COUNT"] >= MIN_PEERS
).astype(int)


# =========================================================
# 16. TRANSACTION FEATURES
# =========================================================

features["TRANSACTION_AMOUNT_VARIATION"] = np.where(
    features["AVERAGE_TRANSACTION_AMOUNT"] > 0,

    features["MAX_TRANSACTION_AMOUNT"]
    / features["AVERAGE_TRANSACTION_AMOUNT"],

    np.nan
)


features["MULTIPLE_VENDOR_FLAG"] = (
    features["VENDOR_COUNT"] > 1
).astype(int)


features["MULTIPLE_TRANSACTION_FLAG"] = (
    features["TRANSACTION_COUNT"] > 1
).astype(int)


features["SINGLE_TRANSACTION_FLAG"] = (
    features["TRANSACTION_COUNT"] == 1
).astype(int)


features["HIGH_TRANSACTION_COUNT_FLAG"] = (
    features["TRANSACTION_COUNT"] >= 3
).astype(int)


features["NO_EXPENDITURE_RECORD_FLAG"] = (
    features["TRANSACTION_COUNT"] == 0
).astype(int)


features["NO_VENDOR_INFORMATION_FLAG"] = (
    features["VENDOR_COUNT"] == 0
).astype(int)


# =========================================================
# 17. FINANCIAL CONSISTENCY FLAGS
# =========================================================

features["ACTUAL_EXCEEDS_SANCTION_FLAG"] = (
    features["ACTUAL_AMOUNT"].notna()
    &
    features["SANCTION_AMOUNT"].notna()
    &
    (
        features["ACTUAL_AMOUNT"]
        > features["SANCTION_AMOUNT"]
    )
).astype(int)


features["DISBURSEMENT_EXCEEDS_SANCTION_FLAG"] = (
    features["SANCTION_AMOUNT"].notna()
    &
    (
        features["TOTAL_DISBURSED"]
        > features["SANCTION_AMOUNT"]
    )
).astype(int)


features["SANCTION_BELOW_RECOMMENDED_FLAG"] = (
    features["SANCTION_AMOUNT"].notna()
    &
    features["RECOMMENDED_AMOUNT"].notna()
    &
    (
        features["SANCTION_AMOUNT"]
        < features["RECOMMENDED_AMOUNT"]
    )
).astype(int)


features["NEGATIVE_SANCTION_AMOUNT_FLAG"] = (
    features["SANCTION_AMOUNT"] < 0
).fillna(False).astype(int)


features["NEGATIVE_ACTUAL_AMOUNT_FLAG"] = (
    features["ACTUAL_AMOUNT"] < 0
).fillna(False).astype(int)


features["NEGATIVE_DISBURSEMENT_FLAG"] = (
    features["TOTAL_DISBURSED"] < 0
).fillna(False).astype(int)


# =========================================================
# 18. COST ANOMALY FLAGS
# =========================================================
#
# These are anomaly signals.
# They do NOT mean confirmed fraud.
# =========================================================

features["HIGH_COST_VS_PEER_FLAG"] = (
    features["COST_VS_PEER_MEDIAN"] >= 2
).fillna(False).astype(int)


features["EXTREME_COST_VS_PEER_FLAG"] = (
    features["COST_VS_PEER_MEDIAN"] >= 5
).fillna(False).astype(int)


features["HIGH_COST_Z_SCORE_FLAG"] = (
    features["COST_Z_SCORE"] >= 3
).fillna(False).astype(int)


features["EXTREME_COST_Z_SCORE_FLAG"] = (
    features["COST_Z_SCORE"] >= 5
).fillna(False).astype(int)


# =========================================================
# 19. LIFECYCLE FLAGS
# =========================================================

features["RECOMMENDED_NOT_SANCTIONED_FLAG"] = (
    (
        features["IS_RECOMMENDED"] == 1
    )
    &
    (
        features["IS_SANCTIONED"] == 0
    )
).astype(int)


features["SANCTIONED_NOT_COMPLETED_FLAG"] = (
    (
        features["IS_SANCTIONED"] == 1
    )
    &
    (
        features["IS_COMPLETED"] == 0
    )
).astype(int)


features["SANCTIONED_WITHOUT_EXPENDITURE_FLAG"] = (
    (
        features["IS_SANCTIONED"] == 1
    )
    &
    (
        features["NO_EXPENDITURE_RECORD_FLAG"] == 1
    )
).astype(int)


features["COMPLETED_WITHOUT_EXPENDITURE_FLAG"] = (
    (
        features["IS_COMPLETED"] == 1
    )
    &
    (
        features["NO_EXPENDITURE_RECORD_FLAG"] == 1
    )
).astype(int)


# =========================================================
# 20. DATA COMPLETENESS SCORE
# =========================================================
#
# This is NOT an anomaly score.
# It measures how much important information is available.
#
# Useful because missing data should not automatically be
# treated as suspicious.
# =========================================================

completeness_columns = [
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "ACTUAL_END_DATE",
]

available_count = (
    features[completeness_columns]
    .notna()
    .sum(axis=1)
)

features["DATA_COMPLETENESS_SCORE"] = (
    available_count
    / len(completeness_columns)
)


# =========================================================
# 21. CLEAN INFINITE VALUES
# =========================================================

features = features.replace(
    [np.inf, -np.inf],
    np.nan
)


# =========================================================
# 22. SORT
# =========================================================

features = features.sort_values(
    WORK_KEY
).reset_index(drop=True)


# =========================================================
# 23. SAVE
# =========================================================

features.to_csv(
    OUTPUT_FILE,
    index=False
)


# =========================================================
# 24. REPORT
# =========================================================

print("\n" + "-" * 75)
print("FEATURE DATASET")
print("-" * 75)

print(f"Rows:                 {len(features):,}")
print(f"Columns:              {len(features.columns)}")


print("\nPeer benchmarking:")

print(
    features["PEER_LEVEL"]
    .value_counts(dropna=False)
    .to_string()
)


print("\nPeer reliability:")

print(
    "Reliable peer groups:",
    int(
        features["PEER_GROUP_RELIABLE_FLAG"].sum()
    )
)

print(
    "No reliable peer group:",
    int(
        (
            features["PEER_GROUP_RELIABLE_FLAG"]
            == 0
        ).sum()
    )
)


print("\nTimeline coverage:")

for column in [
    "RECOMMENDATION_TO_SANCTION_DAYS",
    "SANCTION_TO_COMPLETION_DAYS",
    "RECOMMENDATION_TO_COMPLETION_DAYS",
]:

    print(
        f"{column:45}"
        f"{features[column].notna().sum():,}"
    )


print("\nData-quality signals:")

for column in [
    "INVALID_RECOMMENDATION_SANCTION_ORDER",
    "INVALID_SANCTION_COMPLETION_ORDER",
    "INVALID_RECOMMENDATION_COMPLETION_ORDER",
    "NEGATIVE_TIMELINE_FLAG",
]:

    print(
        f"{column:45}"
        f"{features[column].sum():,}"
    )


print("\nFinancial consistency:")

for column in [
    "ACTUAL_EXCEEDS_SANCTION_FLAG",
    "DISBURSEMENT_EXCEEDS_SANCTION_FLAG",
    "SANCTION_BELOW_RECOMMENDED_FLAG",
    "NEGATIVE_SANCTION_AMOUNT_FLAG",
    "NEGATIVE_ACTUAL_AMOUNT_FLAG",
    "NEGATIVE_DISBURSEMENT_FLAG",
]:

    print(
        f"{column:45}"
        f"{features[column].sum():,}"
    )


print("\nCost anomaly signals:")

for column in [
    "HIGH_COST_VS_PEER_FLAG",
    "EXTREME_COST_VS_PEER_FLAG",
    "HIGH_COST_Z_SCORE_FLAG",
    "EXTREME_COST_Z_SCORE_FLAG",
]:

    print(
        f"{column:45}"
        f"{features[column].sum():,}"
    )


print("\nTransaction signals:")

for column in [
    "MULTIPLE_VENDOR_FLAG",
    "MULTIPLE_TRANSACTION_FLAG",
    "HIGH_TRANSACTION_COUNT_FLAG",
]:

    print(
        f"{column:45}"
        f"{features[column].sum():,}"
    )


print("\nLifecycle signals:")

for column in [
    "RECOMMENDED_NOT_SANCTIONED_FLAG",
    "SANCTIONED_NOT_COMPLETED_FLAG",
    "SANCTIONED_WITHOUT_EXPENDITURE_FLAG",
    "COMPLETED_WITHOUT_EXPENDITURE_FLAG",
]:

    print(
        f"{column:45}"
        f"{features[column].sum():,}"
    )


print("\n" + "-" * 75)
print("OUTPUT")
print("-" * 75)

print(f"Saved → {OUTPUT_FILE}")


print("\n" + "=" * 75)
print("PHASE 2.4 FEATURE ENGINEERING COMPLETE")
print("=" * 75)