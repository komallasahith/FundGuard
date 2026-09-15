import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# FUNDGUARD
# INDIA-WIDE RULE-BASED ANOMALY DETECTOR
# ============================================================
#
# Purpose:
#   Detect rule-based anomaly signals in MPLADS works.
#
# Important:
#   These rules identify works that may deserve investigation.
#   They DO NOT establish fraud or misconduct.
#
# Input:
#   data/processed/mplads_india_features.csv
#
# Output:
#   data/outputs/india_rule_anomalies.csv
#   data/outputs/india_rule_summary.csv
#   data/outputs/india_rule_distribution.csv
#
# ============================================================


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_features.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_rule_anomalies.csv"
)

SUMMARY_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_rule_summary.csv"
)

DISTRIBUTION_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_rule_distribution.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# Peer population
# ------------------------------------------------------------

MIN_PEERS = 10


# ------------------------------------------------------------
# Peer cost thresholds
# ------------------------------------------------------------

PEER_RATIO_MODERATE = 2.0
PEER_RATIO_STRONG = 5.0

PEER_Z_MODERATE = 3.0
PEER_Z_STRONG = 5.0


# ------------------------------------------------------------
# Payment thresholds
# ------------------------------------------------------------

PAYMENT_COUNT_MODERATE = 5
PAYMENT_COUNT_STRONG = 10

VENDOR_COUNT_MODERATE = 5
VENDOR_COUNT_STRONG = 10


# ------------------------------------------------------------
# Payment frequency
# ------------------------------------------------------------

PAYMENTS_PER_30_MODERATE = 3.0
PAYMENTS_PER_30_STRONG = 6.0


# ------------------------------------------------------------
# Investigation severity thresholds
# ------------------------------------------------------------

LOW_THRESHOLD = 1
MEDIUM_THRESHOLD = 30
HIGH_THRESHOLD = 60


# ============================================================
# START
# ============================================================

print("=" * 75)
print("FUNDGUARD INDIA-WIDE RULE-BASED ANOMALY DETECTOR")
print("=" * 75)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading feature dataset...")

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print(
    f"Rows    : {len(df):,}"
)

print(
    f"Columns : {len(df.columns):,}"
)


# ============================================================
# BASIC VALIDATION
# ============================================================

print("\nValidating input...")

if "WORK_ID" not in df.columns:
    raise ValueError(
        "WORK_ID column is missing from feature dataset."
    )


df["WORK_ID"] = pd.to_numeric(
    df["WORK_ID"],
    errors="coerce"
)


if df["WORK_ID"].isna().any():

    raise ValueError(
        "WORK_ID contains missing or invalid values."
    )


if df["WORK_ID"].duplicated().any():

    duplicate_count = int(
        df["WORK_ID"].duplicated().sum()
    )

    raise ValueError(
        f"Duplicate WORK_ID values found: {duplicate_count}"
    )


print("Input validation passed.")


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# HELPER
# ============================================================

def numeric_column(
    dataframe,
    column_name
):

    if column_name not in dataframe.columns:

        return pd.Series(
            np.nan,
            index=dataframe.index,
            dtype="float64"
        )

    return pd.to_numeric(
        dataframe[column_name],
        errors="coerce"
    )


def make_flag(condition):

    return (
        condition
        .fillna(False)
        .astype("int8")
    )


# ============================================================
# READ FEATURES
# ============================================================

sanction = numeric_column(
    df,
    "SANCTION_AMOUNT"
)

recommended = numeric_column(
    df,
    "RECOMMENDED_AMOUNT"
)

disbursed = numeric_column(
    df,
    "TOTAL_FUND_DISBURSED_AMT"
)

actual = numeric_column(
    df,
    "ACTUAL_AMOUNT"
)

peer_count = numeric_column(
    df,
    "PEER_COUNT"
)

peer_median = numeric_column(
    df,
    "PEER_MEDIAN_SANCTION"
)

peer_mean = numeric_column(
    df,
    "PEER_MEAN_SANCTION"
)

peer_std = numeric_column(
    df,
    "PEER_STD_SANCTION"
)

peer_ratio = numeric_column(
    df,
    "SANCTION_TO_PEER_MEDIAN"
)

disbursed_peer_ratio = numeric_column(
    df,
    "DISBURSED_TO_PEER_MEDIAN"
)

peer_z = numeric_column(
    df,
    "SANCTION_PEER_Z_SCORE"
)

payment_count = numeric_column(
    df,
    "PAYMENT_COUNT"
)

vendor_count = numeric_column(
    df,
    "UNIQUE_VENDOR_COUNT"
)

payments_per_30 = numeric_column(
    df,
    "PAYMENTS_PER_30_DAYS"
)

payment_in_progress_ratio = numeric_column(
    df,
    "PAYMENT_IN_PROGRESS_RATIO"
)

recommendation_to_sanction = numeric_column(
    df,
    "RECOMMENDATION_TO_SANCTION_DAYS"
)

sanction_to_payment = numeric_column(
    df,
    "SANCTION_TO_FIRST_PAYMENT_DAYS"
)

completion_before_payment = numeric_column(
    df,
    "COMPLETION_BEFORE_LAST_PAYMENT"
)

data_completeness = numeric_column(
    df,
    "DATA_COMPLETENESS_RATIO"
)


# ============================================================
# RULE STORAGE
# ============================================================

rules = []


def register_rule(
    name,
    condition,
    category,
    strength,
    score,
    description,
    verification_only=False
):

    rules.append(
        {
            "name": name,
            "condition": make_flag(condition),
            "category": category,
            "strength": strength,
            "score": score,
            "description": description,
            "verification_only": verification_only
        }
    )


# ============================================================
# 1. FINANCIAL / PEER RULES
# ============================================================

print("\nEvaluating financial peer rules...")


# ------------------------------------------------------------
# 2x peer median
# ------------------------------------------------------------

register_rule(
    name="RULE_SANCTION_ABOVE_2X_PEER",
    condition=(
        peer_count.ge(MIN_PEERS)
        &
        peer_ratio.gt(PEER_RATIO_MODERATE)
    ),
    category="Financial",
    strength="MODERATE",
    score=20,
    description=(
        "Sanction amount is more than 2x the median "
        "sanction amount of comparable peer works."
    )
)


# ------------------------------------------------------------
# 5x peer median
# ------------------------------------------------------------

register_rule(
    name="RULE_SANCTION_ABOVE_5X_PEER",
    condition=(
        peer_count.ge(MIN_PEERS)
        &
        peer_ratio.gt(PEER_RATIO_STRONG)
    ),
    category="Financial",
    strength="STRONG",
    score=35,
    description=(
        "Sanction amount is more than 5x the median "
        "sanction amount of comparable peer works."
    )
)


# ------------------------------------------------------------
# Peer Z > 3
# ------------------------------------------------------------

register_rule(
    name="RULE_PEER_Z_ABOVE_3",
    condition=(
        peer_count.ge(MIN_PEERS)
        &
        peer_z.gt(PEER_Z_MODERATE)
    ),
    category="Financial",
    strength="MODERATE",
    score=20,
    description=(
        "Sanction amount is more than 3 standard deviations "
        "above the comparable peer mean."
    )
)


# ------------------------------------------------------------
# Peer Z > 5
# ------------------------------------------------------------

register_rule(
    name="RULE_PEER_Z_ABOVE_5",
    condition=(
        peer_count.ge(MIN_PEERS)
        &
        peer_z.gt(PEER_Z_STRONG)
    ),
    category="Financial",
    strength="STRONG",
    score=35,
    description=(
        "Sanction amount is more than 5 standard deviations "
        "above the comparable peer mean."
    )
)


# ------------------------------------------------------------
# Actual > sanction
# ------------------------------------------------------------

register_rule(
    name="RULE_ACTUAL_ABOVE_SANCTION",
    condition=(
        actual.notna()
        &
        sanction.notna()
        &
        actual.gt(sanction)
    ),
    category="Financial",
    strength="STRONG",
    score=35,
    description=(
        "Reported actual expenditure exceeds the sanctioned amount."
    )
)


# ------------------------------------------------------------
# Disbursed > sanction
# ------------------------------------------------------------

register_rule(
    name="RULE_DISBURSED_ABOVE_SANCTION",
    condition=(
        disbursed.notna()
        &
        sanction.notna()
        &
        disbursed.gt(sanction)
    ),
    category="Financial",
    strength="STRONG",
    score=35,
    description=(
        "Total recorded disbursement exceeds the sanctioned amount."
    )
)


# ============================================================
# 2. PAYMENT RULES
# ============================================================

print("Evaluating payment rules...")


# ------------------------------------------------------------
# 5+ payments
# ------------------------------------------------------------

register_rule(
    name="RULE_HIGH_PAYMENT_COUNT",
    condition=payment_count.ge(
        PAYMENT_COUNT_MODERATE
    ),
    category="Payment",
    strength="MODERATE",
    score=10,
    description=(
        "Work has at least 5 recorded payment transactions."
    )
)


# ------------------------------------------------------------
# 10+ payments
# ------------------------------------------------------------

register_rule(
    name="RULE_VERY_HIGH_PAYMENT_COUNT",
    condition=payment_count.ge(
        PAYMENT_COUNT_STRONG
    ),
    category="Payment",
    strength="STRONG",
    score=20,
    description=(
        "Work has at least 10 recorded payment transactions."
    )
)


# ------------------------------------------------------------
# 5+ vendors
# ------------------------------------------------------------

register_rule(
    name="RULE_MULTIPLE_VENDORS",
    condition=vendor_count.ge(
        VENDOR_COUNT_MODERATE
    ),
    category="Payment",
    strength="MODERATE",
    score=10,
    description=(
        "Work has payments associated with at least 5 vendors."
    )
)


# ------------------------------------------------------------
# 10+ vendors
# ------------------------------------------------------------

register_rule(
    name="RULE_MANY_VENDORS",
    condition=vendor_count.ge(
        VENDOR_COUNT_STRONG
    ),
    category="Payment",
    strength="STRONG",
    score=20,
    description=(
        "Work has payments associated with at least 10 vendors."
    )
)


# ============================================================
# 3. PAYMENT INTENSITY
# ============================================================

print("Evaluating payment intensity...")


# ------------------------------------------------------------
# More than 3 payments / 30 days
# ------------------------------------------------------------

register_rule(
    name="RULE_HIGH_PAYMENT_FREQUENCY",
    condition=(
        payment_count.gt(1)
        &
        payments_per_30.gt(
            PAYMENTS_PER_30_MODERATE
        )
    ),
    category="Payment",
    strength="MODERATE",
    score=10,
    description=(
        "Payment activity exceeds 3 recorded payments "
        "per 30 expenditure days."
    )
)


# ------------------------------------------------------------
# More than 6 payments / 30 days
# ------------------------------------------------------------

register_rule(
    name="RULE_VERY_HIGH_PAYMENT_FREQUENCY",
    condition=(
        payment_count.gt(1)
        &
        payments_per_30.gt(
            PAYMENTS_PER_30_STRONG
        )
    ),
    category="Payment",
    strength="STRONG",
    score=20,
    description=(
        "Payment activity exceeds 6 recorded payments "
        "per 30 expenditure days."
    )
)


# ============================================================
# 4. TIMELINE RULES
# ============================================================

print("Evaluating timeline rules...")


# ------------------------------------------------------------
# Recommendation -> sanction violation
# ------------------------------------------------------------

register_rule(
    name="RULE_RECOMMENDATION_BEFORE_SANCTION_VIOLATION",
    condition=recommendation_to_sanction.lt(0),
    category="Timeline",
    strength="STRONG",
    score=30,
    description=(
        "Recorded sanction date occurs before "
        "the recommendation date."
    )
)


# ------------------------------------------------------------
# Payment before sanction
# ------------------------------------------------------------

register_rule(
    name="RULE_PAYMENT_BEFORE_SANCTION",
    condition=sanction_to_payment.lt(0),
    category="Timeline",
    strength="STRONG",
    score=30,
    description=(
        "Recorded expenditure occurs before "
        "the sanction date."
    )
)


# ------------------------------------------------------------
# Completion before last payment
# ------------------------------------------------------------
#
# IMPORTANT:
# This is NOT treated as a strong anomaly.
#
# The India-wide dataset contains many cases where financial
# activity appears after the reported completion date.
# This may represent administrative settlement/update timing.
#
# Therefore:
#   - retain as verification evidence
#   - do not contribute to anomaly score
# ------------------------------------------------------------

register_rule(
    name="RULE_COMPLETION_BEFORE_LAST_PAYMENT",
    condition=completion_before_payment.eq(1),
    category="Timeline",
    strength="VERIFY",
    score=0,
    description=(
        "Reported completion date precedes the last recorded "
        "payment; verify because the dates may represent "
        "different administrative events."
    ),
    verification_only=True
)


# ============================================================
# 5. PAYMENT STATUS
# ============================================================

print("Evaluating payment status...")


# This is a weak signal only.
# It is NOT enough by itself to make a work a serious candidate.

register_rule(
    name="RULE_HIGH_IN_PROGRESS_RATIO",
    condition=payment_in_progress_ratio.gt(0.50),
    category="Payment Status",
    strength="WEAK",
    score=5,
    description=(
        "More than half of the recorded payment transactions "
        "are currently marked as in progress."
    )
)


# ============================================================
# 6. DATA QUALITY
# ============================================================

print("Evaluating data quality...")


# ------------------------------------------------------------
# IMPORTANT:
#
# Low completeness is NOT an anomaly score.
#
# The previous version produced 27,347 candidates because of
# this rule. Missing fields can be caused by API structure,
# work stage, or unavailable fields.
#
# We therefore store it only as verification evidence.
# ------------------------------------------------------------

register_rule(
    name="RULE_LOW_DATA_COMPLETENESS",
    condition=(
        data_completeness.notna()
        &
        data_completeness.lt(0.50)
    ),
    category="Data Quality",
    strength="VERIFY",
    score=0,
    description=(
        "More than half of the selected analytical fields "
        "are missing; verify the underlying record."
    ),
    verification_only=True
)


# ============================================================
# ADD RULE FLAGS TO DATAFRAME
# ============================================================

print("\nCreating rule flags...")


rule_flag_data = {}

for rule in rules:

    rule_flag_data[
        rule["name"]
    ] = rule["condition"]


rule_flags_df = pd.DataFrame(
    rule_flag_data,
    index=df.index
)


# Add all rule flags in one operation.
# This avoids the pandas fragmentation warnings from the
# previous implementation.

df = pd.concat(
    [
        df,
        rule_flags_df
    ],
    axis=1
)


# ============================================================
# SCORE CALCULATION
# ============================================================

print("Calculating calibrated rule score...")


# ============================================================
# CATEGORY SCORES
# ============================================================

financial_score = np.zeros(
    len(df),
    dtype=float
)

payment_score = np.zeros(
    len(df),
    dtype=float
)

timeline_score = np.zeros(
    len(df),
    dtype=float
)

payment_status_score = np.zeros(
    len(df),
    dtype=float
)


# ------------------------------------------------------------
# Financial category
# ------------------------------------------------------------

financial_rules = [
    r for r in rules
    if r["category"] == "Financial"
    and not r["verification_only"]
]


# We use the strongest financial evidence rather than blindly
# adding correlated peer rules.
#
# Example:
# 5x peer median + Z > 5 should not become 70 points.
# They are measuring similar cost abnormality.

for rule in financial_rules:

    condition = (
        df[rule["name"]]
        .eq(1)
    )

    financial_score = np.maximum(
        financial_score,
        np.where(
            condition,
            rule["score"],
            0
        )
    )


# ------------------------------------------------------------
# Payment category
# ------------------------------------------------------------

payment_rules = [
    r for r in rules
    if r["category"] == "Payment"
    and not r["verification_only"]
]


payment_rule_scores = []

for rule in payment_rules:

    payment_rule_scores.append(
        np.where(
            df[rule["name"]].eq(1),
            rule["score"],
            0
        )
    )


if payment_rule_scores:

    payment_score = np.sum(
        payment_rule_scores,
        axis=0
    )


# Cap payment evidence.

payment_score = np.minimum(
    payment_score,
    30
)


# ------------------------------------------------------------
# Timeline category
# ------------------------------------------------------------

timeline_rules = [
    r for r in rules
    if r["category"] == "Timeline"
    and not r["verification_only"]
]


for rule in timeline_rules:

    condition = (
        df[rule["name"]]
        .eq(1)
    )

    timeline_score = np.maximum(
        timeline_score,
        np.where(
            condition,
            rule["score"],
            0
        )
    )


# ------------------------------------------------------------
# Payment status
# ------------------------------------------------------------

status_rules = [
    r for r in rules
    if r["category"] == "Payment Status"
]


for rule in status_rules:

    condition = (
        df[rule["name"]]
        .eq(1)
    )

    payment_status_score = np.maximum(
        payment_status_score,
        np.where(
            condition,
            rule["score"],
            0
        )
    )


# ============================================================
# CATEGORY SCORE COLUMNS
# ============================================================

category_scores = pd.DataFrame(
    {
        "RULE_FINANCIAL_SCORE": financial_score,
        "RULE_PAYMENT_SCORE": payment_score,
        "RULE_TIMELINE_SCORE": timeline_score,
        "RULE_PAYMENT_STATUS_SCORE": payment_status_score,
    },
    index=df.index
)


df = pd.concat(
    [
        df,
        category_scores
    ],
    axis=1
)


# ============================================================
# BASE SCORE
# ============================================================

df["RULE_SCORE"] = (
    df["RULE_FINANCIAL_SCORE"]
    +
    df["RULE_PAYMENT_SCORE"]
    +
    df["RULE_TIMELINE_SCORE"]
    +
    df["RULE_PAYMENT_STATUS_SCORE"]
)


# ============================================================
# EVIDENCE DIVERSITY BONUS
# ============================================================
#
# Multiple independent categories are more informative than
# many rules from the same category.
#
# Example:
#
#   Financial only -> no bonus
#   Financial + Payment -> +5
#   Financial + Payment + Timeline -> +10
#
# Maximum score remains 100.
# ============================================================

df["RULE_FINANCIAL_PRESENT"] = (
    df["RULE_FINANCIAL_SCORE"] > 0
).astype("int8")

df["RULE_PAYMENT_PRESENT"] = (
    df["RULE_PAYMENT_SCORE"] > 0
).astype("int8")

df["RULE_TIMELINE_PRESENT"] = (
    df["RULE_TIMELINE_SCORE"] > 0
).astype("int8")


df["RULE_CATEGORY_COUNT"] = (
    df[
        [
            "RULE_FINANCIAL_PRESENT",
            "RULE_PAYMENT_PRESENT",
            "RULE_TIMELINE_PRESENT"
        ]
    ]
    .sum(axis=1)
)


df["RULE_DIVERSITY_BONUS"] = np.select(
    [
        df["RULE_CATEGORY_COUNT"].ge(3),
        df["RULE_CATEGORY_COUNT"].ge(2),
    ],
    [
        10,
        5
    ],
    default=0
)


df["RULE_SCORE"] = (
    df["RULE_SCORE"]
    +
    df["RULE_DIVERSITY_BONUS"]
)


# Final cap.

df["RULE_SCORE"] = np.minimum(
    df["RULE_SCORE"],
    100
)


# ============================================================
# RULE TRIGGER COUNT
# ============================================================

all_rule_names = [
    r["name"]
    for r in rules
]


df["RULE_TRIGGER_COUNT"] = (
    df[
        all_rule_names
    ]
    .sum(axis=1)
)


# ============================================================
# STRONG RULE COUNT
# ============================================================

strong_rule_names = [
    r["name"]
    for r in rules
    if r["strength"] == "STRONG"
]


if strong_rule_names:

    df["STRONG_RULE_COUNT"] = (
        df[
            strong_rule_names
        ]
        .sum(axis=1)
    )

else:

    df["STRONG_RULE_COUNT"] = 0


# ============================================================
# VERIFICATION FLAGS
# ============================================================

verification_rule_names = [
    r["name"]
    for r in rules
    if r["verification_only"]
]


df["VERIFICATION_FLAG_COUNT"] = (
    df[
        verification_rule_names
    ]
    .sum(axis=1)
)


# ============================================================
# SEVERITY
# ============================================================

print("Assigning severity...")


df["RULE_SEVERITY"] = "NONE"


# Any scored anomaly signal

df.loc[
    df["RULE_SCORE"] > 0,
    "RULE_SEVERITY"
] = "LOW"


# Medium

df.loc[
    df["RULE_SCORE"] >= MEDIUM_THRESHOLD,
    "RULE_SEVERITY"
] = "MEDIUM"


# High

df.loc[
    df["RULE_SCORE"] >= HIGH_THRESHOLD,
    "RULE_SEVERITY"
] = "HIGH"


# ============================================================
# HUMAN-READABLE EVIDENCE
# ============================================================

print("Building rule evidence...")


# ------------------------------------------------------------
# Reason builder
# ------------------------------------------------------------

reason_map = {
    r["name"]: r["description"]
    for r in rules
}


def build_reasons(row):

    reasons = []

    for rule in rules:

        if row[rule["name"]] == 1:

            reasons.append(
                reason_map[rule["name"]]
            )

    return " | ".join(reasons)


# ------------------------------------------------------------
# Separate verification evidence
# ------------------------------------------------------------

def build_verification(row):

    reasons = []

    for rule in rules:

        if (
            rule["verification_only"]
            and
            row[rule["name"]] == 1
        ):

            reasons.append(
                rule["description"]
            )

    return " | ".join(reasons)


df["RULE_REASONS"] = df.apply(
    build_reasons,
    axis=1
)


df["RULE_VERIFICATION_NOTES"] = df.apply(
    build_verification,
    axis=1
)


# ============================================================
# RULE FLAGS TEXT
# ============================================================

def build_rule_flags(row):

    triggered = []

    for rule in rules:

        if row[rule["name"]] == 1:

            triggered.append(
                rule["name"]
            )

    return " | ".join(triggered)


df["RULE_FLAGS"] = df.apply(
    build_rule_flags,
    axis=1
)


# ============================================================
# CANDIDATE DEFINITION
# ============================================================
#
# A verification-only signal does NOT make a work an anomaly
# candidate.
#
# Candidate requires:
#
#   RULE_SCORE > 0
#
# This is the key difference from the previous version.
# ============================================================

df["RULE_CANDIDATE"] = (
    df["RULE_SCORE"] > 0
).astype("int8")


# ============================================================
# OUTPUT COLUMNS
# ============================================================

base_output_columns = [
    "WORK_ID",

    "STATE_ID",
    "STATE_NAME",

    "CONSTITUENCY_ID",
    "CONSTITUENCY",

    "MP_ID",
    "MP_NAME",

    "WORK_CATEGORY",
    "ACTIVITY_NAME",
    "WORK_DESCRIPTION",
    "WORK_STAGE",

    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",

    "TOTAL_FUND_DISBURSED_AMT",
    "ACTUAL_AMOUNT",

    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",

    "FIRST_EXPENDITURE_DATE",
    "LAST_EXPENDITURE_DATE",
    "ACTUAL_END_DATE",

    "PEER_COUNT",
    "PEER_MEDIAN_SANCTION",
    "PEER_MEAN_SANCTION",
    "PEER_STD_SANCTION",

    "SANCTION_TO_PEER_MEDIAN",
    "SANCTION_PEER_Z_SCORE",

    "RECOMMENDATION_TO_SANCTION_DAYS",
    "SANCTION_TO_FIRST_PAYMENT_DAYS",
    "COMPLETION_BEFORE_LAST_PAYMENT",

    "DATA_COMPLETENESS_RATIO",

    "RULE_FINANCIAL_SCORE",
    "RULE_PAYMENT_SCORE",
    "RULE_TIMELINE_SCORE",
    "RULE_PAYMENT_STATUS_SCORE",

    "RULE_DIVERSITY_BONUS",
    "RULE_CATEGORY_COUNT",

    "RULE_SCORE",
    "RULE_SEVERITY",

    "RULE_TRIGGER_COUNT",
    "STRONG_RULE_COUNT",

    "VERIFICATION_FLAG_COUNT",

    "RULE_CANDIDATE",

    "RULE_FLAGS",
    "RULE_REASONS",
    "RULE_VERIFICATION_NOTES",
]


# Only keep columns that actually exist.

base_output_columns = [
    column
    for column in base_output_columns
    if column in df.columns
]


# Add rule flag columns.

final_output_columns = (
    base_output_columns
    +
    all_rule_names
)


final_output_columns = list(
    dict.fromkeys(
        final_output_columns
    )
)


# ============================================================
# CREATE RESULT DATAFRAME
# ============================================================

results = df[
    final_output_columns
].copy()


# ============================================================
# CANDIDATES ONLY
# ============================================================

candidates = results[
    results["RULE_CANDIDATE"] == 1
].copy()


# ============================================================
# SORT
# ============================================================

candidates = candidates.sort_values(
    [
        "RULE_SCORE",
        "STRONG_RULE_COUNT",
        "RULE_TRIGGER_COUNT"
    ],
    ascending=[
        False,
        False,
        False
    ]
)


# ============================================================
# SAVE CANDIDATES
# ============================================================

candidates.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# RULE SUMMARY
# ============================================================

summary_rows = []


for rule in rules:

    triggered = int(
        df[rule["name"]]
        .sum()
    )

    percentage = (
        triggered
        /
        len(df)
        *
        100
    )

    summary_rows.append(
        {
            "RULE": rule["name"],
            "CATEGORY": rule["category"],
            "STRENGTH": rule["strength"],
            "SCORE": rule["score"],
            "VERIFICATION_ONLY":
                rule["verification_only"],
            "TRIGGERED_WORKS":
                triggered,
            "PERCENT_OF_WORKS":
                percentage,
            "DESCRIPTION":
                rule["description"]
        }
    )


summary = pd.DataFrame(
    summary_rows
)


summary = summary.sort_values(
    "TRIGGERED_WORKS",
    ascending=False
)


summary.to_csv(
    SUMMARY_FILE,
    index=False
)


# ============================================================
# SCORE DISTRIBUTION
# ============================================================

distribution = (
    df[
        [
            "RULE_SCORE",
            "RULE_SEVERITY",
            "RULE_CANDIDATE",
            "RULE_TRIGGER_COUNT",
            "STRONG_RULE_COUNT",
            "RULE_CATEGORY_COUNT"
        ]
    ]
    .groupby(
        [
            "RULE_SCORE",
            "RULE_SEVERITY"
        ],
        dropna=False
    )
    .size()
    .reset_index(
        name="WORK_COUNT"
    )
    .sort_values(
        "RULE_SCORE",
        ascending=False
    )
)


distribution.to_csv(
    DISTRIBUTION_FILE,
    index=False
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 75)
print("RULE DETECTOR VALIDATION")
print("=" * 75)


# ------------------------------------------------------------
# Basic
# ------------------------------------------------------------

print(
    f"\nTotal works             : {len(df):,}"
)

print(
    f"Rule candidates         : {len(candidates):,}"
)

print(
    f"Candidate percentage    : "
    f"{len(candidates) / len(df) * 100:.2f}%"
)


# ------------------------------------------------------------
# Severity
# ------------------------------------------------------------

print(
    "\nWorks by severity:"
)

severity_counts = (
    df["RULE_SEVERITY"]
    .value_counts()
)


print(
    severity_counts
    .to_string()
)


# ------------------------------------------------------------
# Candidate severity only
# ------------------------------------------------------------

print(
    "\nCandidate severity:"
)

candidate_severity = (
    candidates["RULE_SEVERITY"]
    .value_counts()
)


print(
    candidate_severity
    .to_string()
)


# ------------------------------------------------------------
# Rule trigger summary
# ------------------------------------------------------------

print(
    "\nRule trigger summary:"
)

print(
    summary[
        [
            "RULE",
            "CATEGORY",
            "STRENGTH",
            "TRIGGERED_WORKS",
            "PERCENT_OF_WORKS"
        ]
    ]
    .to_string(
        index=False
    )
)


# ------------------------------------------------------------
# Score statistics
# ------------------------------------------------------------

print(
    "\nRule score statistics:"
)

print(
    f"Minimum : {df['RULE_SCORE'].min():.2f}"
)

print(
    f"Median  : {df['RULE_SCORE'].median():.2f}"
)

print(
    f"Mean    : {df['RULE_SCORE'].mean():.2f}"
)

print(
    f"Maximum : {df['RULE_SCORE'].max():.2f}"
)


# ------------------------------------------------------------
# Score buckets
# ------------------------------------------------------------

score_buckets = pd.cut(
    df["RULE_SCORE"],
    bins=[
        -0.01,
        0,
        19.99,
        29.99,
        39.99,
        59.99,
        100
    ],
    labels=[
        "0",
        "1-19",
        "20-29",
        "30-39",
        "40-59",
        "60-100"
    ]
)


print(
    "\nRule score distribution:"
)

print(
    score_buckets
    .value_counts(
        sort=False
    )
    .to_string()
)


# ------------------------------------------------------------
# Multiple independent rules
# ------------------------------------------------------------

print(
    "\nIndependent evidence:"
)

print(
    "Works with 2+ rule categories :",
    int(
        (
            df["RULE_CATEGORY_COUNT"]
            >= 2
        ).sum()
    )
)

print(
    "Works with 3 rule categories  :",
    int(
        (
            df["RULE_CATEGORY_COUNT"]
            >= 3
        ).sum()
    )
)


# ------------------------------------------------------------
# Strong evidence
# ------------------------------------------------------------

print(
    "\nStrong rule evidence:"
)

print(
    "1+ strong rule :",
    int(
        (
            df["STRONG_RULE_COUNT"]
            >= 1
        ).sum()
    )
)

print(
    "2+ strong rules:",
    int(
        (
            df["STRONG_RULE_COUNT"]
            >= 2
        ).sum()
    )
)


# ------------------------------------------------------------
# Verification-only signals
# ------------------------------------------------------------

print(
    "\nVerification-only signals:"
)

print(
    "Works with verification flags:",
    int(
        (
            df["VERIFICATION_FLAG_COUNT"]
            > 0
        ).sum()
    )
)


# ------------------------------------------------------------
# Known chronology consistency checks
# ------------------------------------------------------------

print(
    "\nTimeline consistency:"
)

print(
    "Recommendation before sanction violation:",
    int(
        df[
            "RULE_RECOMMENDATION_BEFORE_SANCTION_VIOLATION"
        ].sum()
    )
)

print(
    "Payment before sanction:",
    int(
        df[
            "RULE_PAYMENT_BEFORE_SANCTION"
        ].sum()
    )
)

print(
    "Completion before last payment:",
    int(
        df[
            "RULE_COMPLETION_BEFORE_LAST_PAYMENT"
        ].sum()
    )
)


# ============================================================
# TOP 20 CANDIDATES
# ============================================================

print(
    "\n" + "=" * 75
)

print(
    "TOP 20 RULE-BASED INVESTIGATION CANDIDATES"
)

print("=" * 75)


top_columns = [
    "WORK_ID",
    "STATE_NAME",
    "CONSTITUENCY",
    "MP_NAME",
    "SANCTION_AMOUNT",
    "PAYMENT_COUNT",
    "RULE_SCORE",
    "RULE_SEVERITY",
    "RULE_CATEGORY_COUNT",
    "STRONG_RULE_COUNT",
]


top_columns = [
    c
    for c in top_columns
    if c in candidates.columns
]


print(
    candidates[
        top_columns
    ]
    .head(20)
    .to_string(
        index=False
    )
)


# ============================================================
# FINAL OUTPUT
# ============================================================

print(
    "\n" + "=" * 75
)

print(
    "OUTPUT FILES"
)

print("=" * 75)

print(
    "\nRule candidates:"
)

print(
    OUTPUT_FILE
)

print(
    "\nRule summary:"
)

print(
    SUMMARY_FILE
)

print(
    "\nScore distribution:"
)

print(
    DISTRIBUTION_FILE
)

print(
    "\nRule-based detector completed successfully."
)

print("=" * 75)