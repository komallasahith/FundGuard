import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# FUNDGUARD
# INDIA-WIDE STATISTICAL ANOMALY DETECTOR
# ============================================================
#
# Purpose:
#   Detect statistically unusual MPLADS works.
#
# IMPORTANT:
#   Statistical anomaly != fraud.
#   Results are investigation candidates only.
#
# Input:
#   data/processed/mplads_india_features.csv
#
# Outputs:
#   data/outputs/india_statistical_anomalies.csv
#   data/outputs/india_statistical_summary.csv
#   data/outputs/india_statistical_distribution.csv
#
# Evidence categories:
#
#   1. Financial
#   2. Payment Behavior
#   3. Timeline
#
# Payment count, vendor diversity and payment frequency
# are correlated signals and therefore count as ONE
# independent evidence category.
#
# Data completeness is verification-only.
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
    / "india_statistical_anomalies.csv"
)

SUMMARY_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_statistical_summary.csv"
)

DISTRIBUTION_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_statistical_distribution.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

MIN_PEER_SIZE = 10

# Financial peer thresholds
PEER_RATIO_MODERATE = 2.0
PEER_RATIO_STRONG = 5.0

# Payment distribution thresholds
PAYMENT_PERCENTILE_MODERATE = 0.99
PAYMENT_PERCENTILE_STRONG = 0.995

# Vendor distribution thresholds
VENDOR_PERCENTILE_MODERATE = 0.99
VENDOR_PERCENTILE_STRONG = 0.995

# Payment frequency thresholds
FREQUENCY_PERCENTILE_MODERATE = 0.99
FREQUENCY_PERCENTILE_STRONG = 0.995

# Completion duration
DURATION_IQR_MODERATE = 1.5
DURATION_IQR_STRONG = 3.0


# ============================================================
# START
# ============================================================

print("=" * 75)
print("FUNDGUARD INDIA-WIDE STATISTICAL ANOMALY DETECTOR")
print("PEER-AWARE + CORRELATED-EVIDENCE CORRECTION")
print("=" * 75)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading feature dataset...")

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print(f"Rows    : {len(df):,}")
print(f"Columns : {len(df.columns):,}")


# ============================================================
# VALIDATE INPUT
# ============================================================

print("\nValidating input...")

if "WORK_ID" not in df.columns:
    raise ValueError(
        "WORK_ID column not found."
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


print("Input validation passed.")


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# HELPERS
# ============================================================

def numeric_column(dataframe, column_name):

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
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "STATE_NAME",
    "WORK_CATEGORY",
    "ACTIVITY_NAME"
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:

    raise ValueError(
        "Missing required columns: "
        +
        ", ".join(missing_columns)
    )


# ============================================================
# NUMERIC FEATURES
# ============================================================

sanction = numeric_column(
    df,
    "SANCTION_AMOUNT"
)

disbursed = numeric_column(
    df,
    "TOTAL_FUND_DISBURSED_AMT"
)

actual = numeric_column(
    df,
    "ACTUAL_AMOUNT"
)

payment_count = numeric_column(
    df,
    "PAYMENT_COUNT"
)

vendor_count = numeric_column(
    df,
    "UNIQUE_VENDOR_COUNT"
)

payment_frequency = numeric_column(
    df,
    "PAYMENTS_PER_30_DAYS"
)

completion_duration = numeric_column(
    df,
    "COMPLETION_DURATION_DAYS"
)

data_completeness = numeric_column(
    df,
    "DATA_COMPLETENESS_RATIO"
)


# ============================================================
# NORMALIZE PEER FIELDS
# ============================================================

print("\nCreating peer groups...")


for column in required_columns:

    df[column] = (
        df[column]
        .fillna("UNKNOWN")
        .astype(str)
    )


# ============================================================
# PEER GROUP
# ============================================================
#
# Comparable work:
#
#   State
#   Work Category
#   Activity
#
# ============================================================

df["STAT_PEER_GROUP"] = (
    df["STATE_NAME"]
    + " | "
    + df["WORK_CATEGORY"]
    + " | "
    + df["ACTIVITY_NAME"]
)


# ============================================================
# PEER COUNT
# ============================================================

df["STAT_PEER_COUNT"] = (
    df.groupby(
        "STAT_PEER_GROUP"
    )["WORK_ID"]
    .transform("count")
)


# ============================================================
# LEAVE-ONE-OUT PEER MEAN
# ============================================================

print(
    "\nCalculating leave-one-out peer statistics..."
)


peer_count_all = (
    df.groupby(
        "STAT_PEER_GROUP"
    )["SANCTION_AMOUNT"]
    .transform("count")
)

peer_sum_all = (
    df.groupby(
        "STAT_PEER_GROUP"
    )["SANCTION_AMOUNT"]
    .transform("sum")
)


has_sanction = (
    sanction.notna()
    .astype(int)
)


loo_count = (
    peer_count_all
    -
    has_sanction
)


loo_sum = (
    peer_sum_all
    -
    sanction.fillna(0)
)


stat_loo_mean = np.where(
    loo_count >= MIN_PEER_SIZE,
    loo_sum / loo_count,
    np.nan
)


# ============================================================
# LEAVE-ONE-OUT QUARTILES
# ============================================================

print(
    "Calculating leave-one-out quartiles..."
)


def calculate_loo_quantiles(group):

    values = pd.to_numeric(
        group["SANCTION_AMOUNT"],
        errors="coerce"
    ).to_numpy()

    result = np.full(
        (len(group), 4),
        np.nan,
        dtype=float
    )

    for position in range(len(values)):

        current = values[position]

        if np.isnan(current):
            continue

        others = np.delete(
            values,
            position
        )

        others = others[
            ~np.isnan(others)
        ]

        if len(others) < MIN_PEER_SIZE:
            continue

        q1 = np.percentile(
            others,
            25
        )

        median = np.percentile(
            others,
            50
        )

        q3 = np.percentile(
            others,
            75
        )

        iqr = q3 - q1

        result[position] = [
            q1,
            median,
            q3,
            iqr
        ]

    return pd.DataFrame(
        result,
        index=group.index,
        columns=[
            "Q1",
            "MEDIAN",
            "Q3",
            "IQR"
        ]
    )


loo_quantiles = (
    df[
        [
            "STAT_PEER_GROUP",
            "SANCTION_AMOUNT"
        ]
    ]
    .groupby(
        "STAT_PEER_GROUP",
        group_keys=False
    )
    .apply(
        calculate_loo_quantiles,
        include_groups=False
    )
)


loo_quantiles = (
    loo_quantiles
    .reindex(df.index)
)


# ============================================================
# ADD PEER FEATURES TO DATAFRAME
# ============================================================

peer_features = pd.DataFrame(
    {
        "STAT_LOO_PEER_MEAN_SANCTION":
            stat_loo_mean,

        "STAT_PEER_Q1":
            loo_quantiles["Q1"].to_numpy(),

        "STAT_PEER_MEDIAN":
            loo_quantiles["MEDIAN"].to_numpy(),

        "STAT_PEER_Q3":
            loo_quantiles["Q3"].to_numpy(),

        "STAT_PEER_IQR":
            loo_quantiles["IQR"].to_numpy()
    },
    index=df.index
)


df = pd.concat(
    [
        df,
        peer_features
    ],
    axis=1
)


# ============================================================
# PEER SANCTION RATIO
# ============================================================

df["STAT_SANCTION_TO_PEER_MEDIAN"] = np.where(
    df["STAT_PEER_MEDIAN"].gt(0),
    sanction / df["STAT_PEER_MEDIAN"],
    np.nan
)


# ============================================================
# PEER IQR BOUNDARIES
# ============================================================

peer_upper_moderate = (
    df["STAT_PEER_Q3"]
    +
    1.5
    *
    df["STAT_PEER_IQR"]
)


peer_upper_strong = (
    df["STAT_PEER_Q3"]
    +
    3.0
    *
    df["STAT_PEER_IQR"]
)


# ============================================================
# RULE REGISTRY
# ============================================================

rules = []


def register_rule(
    name,
    condition,
    score,
    category,
    strength,
    description,
    verification_only=False
):

    rules.append(
        {
            "name": name,

            "condition":
                make_flag(condition),

            "score":
                score,

            "category":
                category,

            "strength":
                strength,

            "description":
                description,

            "verification_only":
                verification_only
        }
    )


# ============================================================
# FINANCIAL STATISTICAL RULES
# ============================================================

print(
    "\nEvaluating peer financial anomalies..."
)


# ------------------------------------------------------------
# Robust 1.5 IQR outlier
# ------------------------------------------------------------

register_rule(
    name="STAT_SANCTION_ABOVE_PEER_IQR",

    condition=(
        df["STAT_PEER_COUNT"].ge(
            MIN_PEER_SIZE
        )
        &
        sanction.gt(
            peer_upper_moderate
        )
        &
        df["STAT_PEER_IQR"].gt(0)
    ),

    score=20,

    category="Financial",

    strength="MODERATE",

    description=(
        "Sanction amount exceeds the robust "
        "1.5×IQR upper boundary of comparable works."
    )
)


# ------------------------------------------------------------
# Extreme 3 IQR outlier
# ------------------------------------------------------------

register_rule(
    name="STAT_SANCTION_EXTREME_PEER_IQR",

    condition=(
        df["STAT_PEER_COUNT"].ge(
            MIN_PEER_SIZE
        )
        &
        sanction.gt(
            peer_upper_strong
        )
        &
        df["STAT_PEER_IQR"].gt(0)
    ),

    score=35,

    category="Financial",

    strength="STRONG",

    description=(
        "Sanction amount exceeds the robust "
        "3×IQR upper boundary of comparable works."
    )
)


# ------------------------------------------------------------
# >5x peer median
# ------------------------------------------------------------

register_rule(
    name="STAT_SANCTION_ABOVE_5X_PEER_MEDIAN",

    condition=(
        df["STAT_PEER_COUNT"].ge(
            MIN_PEER_SIZE
        )
        &
        df["STAT_SANCTION_TO_PEER_MEDIAN"].gt(
            PEER_RATIO_STRONG
        )
    ),

    score=35,

    category="Financial",

    strength="STRONG",

    description=(
        "Sanction amount is more than 5x the "
        "leave-one-out peer median."
    )
)


# ============================================================
# PAYMENT DISTRIBUTION
# ============================================================

print(
    "\nCalculating payment distribution thresholds..."
)


payment_positive = payment_count[
    payment_count.notna()
    &
    payment_count.gt(0)
]


if len(payment_positive) > 0:

    payment_p99 = (
        payment_positive
        .quantile(
            PAYMENT_PERCENTILE_MODERATE
        )
    )

    payment_p995 = (
        payment_positive
        .quantile(
            PAYMENT_PERCENTILE_STRONG
        )
    )

else:

    payment_p99 = np.nan
    payment_p995 = np.nan


print(
    f"Payment P99   : {payment_p99}"
)

print(
    f"Payment P99.5 : {payment_p995}"
)


# ============================================================
# PAYMENT COUNT
# ============================================================

register_rule(
    name="STAT_PAYMENT_COUNT_OUTLIER",

    condition=(
        payment_count.gt(
            payment_p99
        )
        &
        payment_count.gt(1)
    ),

    score=10,

    category="Payment Behavior",

    strength="MODERATE",

    description=(
        "Payment transaction count is in the extreme "
        "upper tail of the observed distribution."
    )
)


register_rule(
    name="STAT_PAYMENT_COUNT_EXTREME",

    condition=(
        payment_count.gt(
            payment_p995
        )
        &
        payment_count.gt(1)
    ),

    score=20,

    category="Payment Behavior",

    strength="STRONG",

    description=(
        "Payment transaction count is beyond the "
        "99.5th percentile of the observed distribution."
    )
)


# ============================================================
# VENDOR DISTRIBUTION
# ============================================================

print(
    "\nCalculating vendor distribution thresholds..."
)


vendor_positive = vendor_count[
    vendor_count.notna()
    &
    vendor_count.gt(0)
]


if len(vendor_positive) > 0:

    vendor_p99 = (
        vendor_positive
        .quantile(
            VENDOR_PERCENTILE_MODERATE
        )
    )

    vendor_p995 = (
        vendor_positive
        .quantile(
            VENDOR_PERCENTILE_STRONG
        )
    )

else:

    vendor_p99 = np.nan
    vendor_p995 = np.nan


print(
    f"Vendor P99   : {vendor_p99}"
)

print(
    f"Vendor P99.5 : {vendor_p995}"
)


# ============================================================
# VENDOR COUNT
# ============================================================

register_rule(
    name="STAT_VENDOR_COUNT_OUTLIER",

    condition=(
        vendor_count.gt(
            vendor_p99
        )
        &
        vendor_count.gt(1)
    ),

    score=10,

    category="Payment Behavior",

    strength="MODERATE",

    description=(
        "Unique vendor count is in the extreme "
        "upper tail of the observed distribution."
    )
)


register_rule(
    name="STAT_VENDOR_COUNT_EXTREME",

    condition=(
        vendor_count.gt(
            vendor_p995
        )
        &
        vendor_count.gt(1)
    ),

    score=20,

    category="Payment Behavior",

    strength="STRONG",

    description=(
        "Unique vendor count is beyond the "
        "99.5th percentile of the observed distribution."
    )
)


# ============================================================
# PAYMENT FREQUENCY
# ============================================================

print(
    "\nCalculating payment-frequency thresholds..."
)


frequency_positive = payment_frequency[
    payment_frequency.notna()
    &
    payment_frequency.gt(0)
]


if len(frequency_positive) > 0:

    frequency_p99 = (
        frequency_positive
        .quantile(
            FREQUENCY_PERCENTILE_MODERATE
        )
    )

    frequency_p995 = (
        frequency_positive
        .quantile(
            FREQUENCY_PERCENTILE_STRONG
        )
    )

else:

    frequency_p99 = np.nan
    frequency_p995 = np.nan


print(
    f"Frequency P99   : {frequency_p99}"
)

print(
    f"Frequency P99.5 : {frequency_p995}"
)


# ============================================================
# PAYMENT FREQUENCY RULES
# ============================================================

register_rule(
    name="STAT_PAYMENT_FREQUENCY_OUTLIER",

    condition=(
        payment_frequency.gt(
            frequency_p99
        )
        &
        payment_count.gt(1)
    ),

    score=10,

    category="Payment Behavior",

    strength="MODERATE",

    description=(
        "Payment frequency is in the extreme "
        "upper tail of the observed distribution."
    )
)


register_rule(
    name="STAT_PAYMENT_FREQUENCY_EXTREME",

    condition=(
        payment_frequency.gt(
            frequency_p995
        )
        &
        payment_count.gt(1)
    ),

    score=20,

    category="Payment Behavior",

    strength="STRONG",

    description=(
        "Payment frequency is beyond the "
        "99.5th percentile of the observed distribution."
    )
)


# ============================================================
# COMPLETION DURATION
# ============================================================

print(
    "\nCalculating completion-duration statistics..."
)


duration_positive = completion_duration[
    completion_duration.notna()
    &
    completion_duration.ge(0)
]


if len(duration_positive) > 0:

    duration_q1 = (
        duration_positive
        .quantile(0.25)
    )

    duration_q3 = (
        duration_positive
        .quantile(0.75)
    )

    duration_iqr = (
        duration_q3
        -
        duration_q1
    )

    duration_upper_moderate = (
        duration_q3
        +
        DURATION_IQR_MODERATE
        *
        duration_iqr
    )

    duration_upper_strong = (
        duration_q3
        +
        DURATION_IQR_STRONG
        *
        duration_iqr
    )

else:

    duration_upper_moderate = np.nan
    duration_upper_strong = np.nan


# ============================================================
# DURATION RULES
# ============================================================

register_rule(
    name="STAT_COMPLETION_DURATION_OUTLIER",

    condition=completion_duration.gt(
        duration_upper_moderate
    ),

    score=10,

    category="Timeline",

    strength="MODERATE",

    description=(
        "Completion duration is above the robust "
        "1.5×IQR upper boundary."
    )
)


register_rule(
    name="STAT_COMPLETION_DURATION_EXTREME",

    condition=completion_duration.gt(
        duration_upper_strong
    ),

    score=20,

    category="Timeline",

    strength="STRONG",

    description=(
        "Completion duration is above the robust "
        "3×IQR upper boundary."
    )
)


# ============================================================
# DATA COMPLETENESS
# ============================================================
#
# Verification only.
# Does NOT increase statistical score.
#
# ============================================================

print(
    "\nEvaluating data completeness..."
)


completeness_p10 = (
    data_completeness
    .quantile(0.10)
)


register_rule(
    name="STAT_LOW_DATA_COMPLETENESS",

    condition=(
        data_completeness.le(
            completeness_p10
        )
    ),

    score=0,

    category="Data Quality",

    strength="VERIFY",

    description=(
        "Data completeness is within the lowest 10% "
        "of the observed dataset; verify source completeness."
    ),

    verification_only=True
)


# ============================================================
# CREATE RULE FLAGS
# ============================================================

print(
    "\nCreating statistical rule flags..."
)


flag_data = {
    rule["name"]:
        rule["condition"]
    for rule in rules
}


flag_dataframe = pd.DataFrame(
    flag_data,
    index=df.index
)


df = pd.concat(
    [
        df,
        flag_dataframe
    ],
    axis=1
)


# ============================================================
# FINANCIAL SCORE
# ============================================================

financial_rule_names = [
    "STAT_SANCTION_ABOVE_PEER_IQR",
    "STAT_SANCTION_EXTREME_PEER_IQR",
    "STAT_SANCTION_ABOVE_5X_PEER_MEDIAN"
]


financial_components = []


for name in financial_rule_names:

    if name not in df.columns:
        continue

    rule_score = next(
        rule["score"]
        for rule in rules
        if rule["name"] == name
    )

    financial_components.append(
        np.where(
            df[name].eq(1),
            rule_score,
            0
        )
    )


if financial_components:

    financial_score = np.max(
        financial_components,
        axis=0
    )

else:

    financial_score = np.zeros(
        len(df),
        dtype=float
    )


# ============================================================
# PAYMENT BEHAVIOR SCORE
# ============================================================
#
# Important:
#
# Payment count
# Vendor count
# Payment frequency
#
# are correlated.
#
# Strongest signal = base score.
#
# Additional corroborating signal:
#
# 2 sub-signals -> +3
# 3 sub-signals -> +5
#
# Maximum payment behavior score = 35.
#
# ============================================================

print(
    "Calculating payment behavior evidence..."
)


payment_count_flags = [
    name
    for name in [
        "STAT_PAYMENT_COUNT_OUTLIER",
        "STAT_PAYMENT_COUNT_EXTREME"
    ]
    if name in df.columns
]


vendor_flags = [
    name
    for name in [
        "STAT_VENDOR_COUNT_OUTLIER",
        "STAT_VENDOR_COUNT_EXTREME"
    ]
    if name in df.columns
]


frequency_flags = [
    name
    for name in [
        "STAT_PAYMENT_FREQUENCY_OUTLIER",
        "STAT_PAYMENT_FREQUENCY_EXTREME"
    ]
    if name in df.columns
]


def max_flag_group(
    dataframe,
    names
):

    if not names:

        return np.zeros(
            len(dataframe),
            dtype=float
        )

    values = []

    for name in names:

        rule_score = next(
            rule["score"]
            for rule in rules
            if rule["name"] == name
        )

        values.append(
            np.where(
                dataframe[name].eq(1),
                rule_score,
                0
            )
        )

    return np.max(
        values,
        axis=0
    )


payment_count_score = max_flag_group(
    df,
    payment_count_flags
)


vendor_score = max_flag_group(
    df,
    vendor_flags
)


frequency_score = max_flag_group(
    df,
    frequency_flags
)


payment_base_score = np.maximum.reduce(
    [
        payment_count_score,
        vendor_score,
        frequency_score
    ]
)


# ============================================================
# PAYMENT SUB-SIGNAL COUNT
# ============================================================

payment_subsignal_count = (
    pd.DataFrame(
        {
            "PAYMENT_COUNT":
                payment_count_score,

            "VENDOR_DIVERSITY":
                vendor_score,

            "PAYMENT_FREQUENCY":
                frequency_score
        },
        index=df.index
    )
    .gt(0)
    .sum(axis=1)
)


# ============================================================
# CORROBORATION BONUS
# ============================================================

payment_corroboration_bonus = np.select(
    [
        payment_subsignal_count.ge(3),

        payment_subsignal_count.ge(2)
    ],

    [
        5,

        3
    ],

    default=0
)


payment_behavior_score = np.minimum(
    payment_base_score
    +
    payment_corroboration_bonus,
    35
)


# ============================================================
# TIMELINE SCORE
# ============================================================

timeline_rule_names = [
    "STAT_COMPLETION_DURATION_OUTLIER",
    "STAT_COMPLETION_DURATION_EXTREME"
]


timeline_components = []


for name in timeline_rule_names:

    if name not in df.columns:
        continue

    rule_score = next(
        rule["score"]
        for rule in rules
        if rule["name"] == name
    )

    timeline_components.append(
        np.where(
            df[name].eq(1),
            rule_score,
            0
        )
    )


if timeline_components:

    timeline_score = np.max(
        timeline_components,
        axis=0
    )

else:

    timeline_score = np.zeros(
        len(df),
        dtype=float
    )


# ============================================================
# ADD CATEGORY SCORES TOGETHER
# ============================================================

category_scores = pd.DataFrame(
    {
        "STAT_FINANCIAL_SCORE":
            financial_score,

        "STAT_PAYMENT_BEHAVIOR_SCORE":
            payment_behavior_score,

        "STAT_TIMELINE_SCORE":
            timeline_score,

        "STAT_PAYMENT_SUBSIGNAL_COUNT":
            payment_subsignal_count,

        "STAT_PAYMENT_CORROBORATION_BONUS":
            payment_corroboration_bonus
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
# INDEPENDENT CATEGORY COUNT
# ============================================================
#
# Exactly THREE independent categories:
#
#   Financial
#   Payment Behavior
#   Timeline
#
# ============================================================

df["STAT_CATEGORY_COUNT"] = (
    (
        df["STAT_FINANCIAL_SCORE"]
        > 0
    ).astype(int)

    +

    (
        df["STAT_PAYMENT_BEHAVIOR_SCORE"]
        > 0
    ).astype(int)

    +

    (
        df["STAT_TIMELINE_SCORE"]
        > 0
    ).astype(int)
)


# ============================================================
# DIVERSITY BONUS
# ============================================================

df["STAT_DIVERSITY_BONUS"] = np.select(
    [
        df["STAT_CATEGORY_COUNT"].ge(3),

        df["STAT_CATEGORY_COUNT"].ge(2)
    ],

    [
        10,

        5
    ],

    default=0
)


# ============================================================
# FINAL STATISTICAL SCORE
# ============================================================

df["STAT_SCORE"] = (
    df["STAT_FINANCIAL_SCORE"]
    +
    df["STAT_PAYMENT_BEHAVIOR_SCORE"]
    +
    df["STAT_TIMELINE_SCORE"]
    +
    df["STAT_DIVERSITY_BONUS"]
)


df["STAT_SCORE"] = np.minimum(
    df["STAT_SCORE"],
    100
)


# ============================================================
# STRONG INDEPENDENT EVIDENCE COUNT
# ============================================================
#
# Strong evidence categories:
#
# Financial >=20
# Payment Behavior >=20
# Timeline >=20
#
# Correlated payment rules are NOT counted individually.
#
# ============================================================

df["STAT_STRONG_RULE_COUNT"] = (
    (
        df["STAT_FINANCIAL_SCORE"]
        >= 20
    ).astype(int)

    +

    (
        df["STAT_PAYMENT_BEHAVIOR_SCORE"]
        >= 20
    ).astype(int)

    +

    (
        df["STAT_TIMELINE_SCORE"]
        >= 20
    ).astype(int)
)


# ============================================================
# TOTAL TRIGGER COUNT
# ============================================================

all_rule_names = [
    rule["name"]
    for rule in rules
]


df["STAT_TRIGGER_COUNT"] = (
    df[
        all_rule_names
    ]
    .sum(axis=1)
)


# ============================================================
# VERIFICATION FLAG COUNT
# ============================================================

verification_rule_names = [
    rule["name"]
    for rule in rules
    if rule["verification_only"]
]


if verification_rule_names:

    df["STAT_VERIFICATION_FLAG_COUNT"] = (
        df[
            verification_rule_names
        ]
        .sum(axis=1)
    )

else:

    df["STAT_VERIFICATION_FLAG_COUNT"] = 0


# ============================================================
# SEVERITY
# ============================================================

df["STAT_SEVERITY"] = "NONE"


df.loc[
    df["STAT_SCORE"] > 0,
    "STAT_SEVERITY"
] = "LOW"


df.loc[
    df["STAT_SCORE"] >= 30,
    "STAT_SEVERITY"
] = "MEDIUM"


df.loc[
    df["STAT_SCORE"] >= 60,
    "STAT_SEVERITY"
] = "HIGH"


# ============================================================
# CANDIDATE
# ============================================================

df["STAT_CANDIDATE"] = (
    df["STAT_SCORE"] > 0
).astype("int8")


# ============================================================
# BUILD EXPLANATIONS
# ============================================================

print(
    "Building statistical evidence..."
)


def build_reasons(row):

    reasons = []

    for rule in rules:

        if (
            row[rule["name"]] == 1
            and
            not rule["verification_only"]
        ):

            reasons.append(
                rule["description"]
            )

    return " | ".join(reasons)


def build_verification(row):

    reasons = []

    for rule in rules:

        if (
            row[rule["name"]] == 1
            and
            rule["verification_only"]
        ):

            reasons.append(
                rule["description"]
            )

    return " | ".join(reasons)


def build_flags(row):

    flags = []

    for rule in rules:

        if row[rule["name"]] == 1:

            flags.append(
                rule["name"]
            )

    return " | ".join(flags)


df["STAT_REASONS"] = df.apply(
    build_reasons,
    axis=1
)


df["STAT_VERIFICATION_NOTES"] = df.apply(
    build_verification,
    axis=1
)


df["STAT_FLAGS"] = df.apply(
    build_flags,
    axis=1
)


# ============================================================
# OUTPUT COLUMNS
# ============================================================

output_columns = [

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

    "STAT_PEER_GROUP",
    "STAT_PEER_COUNT",

    "STAT_PEER_Q1",
    "STAT_PEER_MEDIAN",
    "STAT_PEER_Q3",
    "STAT_PEER_IQR",

    "STAT_LOO_PEER_MEAN_SANCTION",

    "STAT_SANCTION_TO_PEER_MEDIAN",

    "STAT_FINANCIAL_SCORE",

    "STAT_PAYMENT_BEHAVIOR_SCORE",

    "STAT_PAYMENT_SUBSIGNAL_COUNT",

    "STAT_PAYMENT_CORROBORATION_BONUS",

    "STAT_TIMELINE_SCORE",

    "STAT_CATEGORY_COUNT",

    "STAT_DIVERSITY_BONUS",

    "STAT_SCORE",

    "STAT_SEVERITY",

    "STAT_TRIGGER_COUNT",

    "STAT_STRONG_RULE_COUNT",

    "STAT_VERIFICATION_FLAG_COUNT",

    "STAT_CANDIDATE",

    "STAT_FLAGS",

    "STAT_REASONS",

    "STAT_VERIFICATION_NOTES"
]


# Add individual rule flags.

output_columns += all_rule_names


# Remove unavailable columns.

output_columns = [
    column
    for column in output_columns
    if column in df.columns
]


# Remove accidental duplicates.

output_columns = list(
    dict.fromkeys(
        output_columns
    )
)


results = df[
    output_columns
].copy()


# ============================================================
# CANDIDATES
# ============================================================

candidates = results[
    results["STAT_CANDIDATE"] == 1
].copy()


# ============================================================
# SORT
# ============================================================

candidates = candidates.sort_values(
    [
        "STAT_SCORE",
        "STAT_CATEGORY_COUNT",
        "STAT_STRONG_RULE_COUNT",
        "STAT_TRIGGER_COUNT"
    ],

    ascending=[
        False,
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
        df[
            rule["name"]
        ].sum()
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
            "RULE":
                rule["name"],

            "CATEGORY":
                rule["category"],

            "STRENGTH":
                rule["strength"],

            "SCORE":
                rule["score"],

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
# VALIDATION
# ============================================================

print(
    "\n" + "=" * 75
)

print(
    "STATISTICAL DETECTOR VALIDATION"
)

print("=" * 75)


# ============================================================
# BASIC COUNTS
# ============================================================

print(
    f"\nTotal works           : {len(df):,}"
)

print(
    f"Statistical candidates: {len(candidates):,}"
)

print(
    f"Candidate percentage  : "
    f"{len(candidates) / len(df) * 100:.2f}%"
)


# ============================================================
# SEVERITY
# ============================================================

print(
    "\nWorks by severity:"
)

print(
    df[
        "STAT_SEVERITY"
    ]
    .value_counts()
    .to_string()
)


print(
    "\nCandidate severity:"
)

if len(candidates) > 0:

    print(
        candidates[
            "STAT_SEVERITY"
        ]
        .value_counts()
        .to_string()
    )

else:

    print(
        "No candidates."
    )


# ============================================================
# SCORE STATISTICS
# ============================================================

print(
    "\nStatistical score statistics:"
)

print(
    f"Minimum : {df['STAT_SCORE'].min():.2f}"
)

print(
    f"Median  : {df['STAT_SCORE'].median():.2f}"
)

print(
    f"Mean    : {df['STAT_SCORE'].mean():.2f}"
)

print(
    f"Maximum : {df['STAT_SCORE'].max():.2f}"
)


# ============================================================
# SCORE DISTRIBUTION
# ============================================================

score_bins = pd.cut(
    df["STAT_SCORE"],

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
    "\nStatistical score distribution:"
)

print(
    score_bins
    .value_counts(
        sort=False
    )
    .to_string()
)


# ============================================================
# PEER POPULATION
# ============================================================

print(
    "\nPeer population:"
)


print(
    "Works with >=10 peers:",
    int(
        (
            df["STAT_PEER_COUNT"]
            >= MIN_PEER_SIZE
        ).sum()
    )
)


print(
    "Works with <10 peers:",
    int(
        (
            df["STAT_PEER_COUNT"]
            < MIN_PEER_SIZE
        ).sum()
    )
)


# ============================================================
# INDEPENDENT EVIDENCE
# ============================================================

print(
    "\nIndependent statistical evidence:"
)


print(
    "2+ statistical categories:",
    int(
        (
            df["STAT_CATEGORY_COUNT"]
            >= 2
        ).sum()
    )
)


print(
    "3 statistical categories:",
    int(
        (
            df["STAT_CATEGORY_COUNT"]
            >= 3
        ).sum()
    )
)


# ============================================================
# STRONG EVIDENCE
# ============================================================

print(
    "\nStrong statistical evidence:"
)


print(
    "1+ strong evidence category:",
    int(
        (
            df["STAT_STRONG_RULE_COUNT"]
            >= 1
        ).sum()
    )
)


print(
    "2+ strong evidence categories:",
    int(
        (
            df["STAT_STRONG_RULE_COUNT"]
            >= 2
        ).sum()
    )
)


print(
    "3 strong evidence categories:",
    int(
        (
            df["STAT_STRONG_RULE_COUNT"]
            >= 3
        ).sum()
    )
)


# ============================================================
# PAYMENT BEHAVIOR
# ============================================================

print(
    "\nPayment behavior evidence:"
)


print(
    "Works with payment behavior:",
    int(
        (
            df["STAT_PAYMENT_BEHAVIOR_SCORE"]
            > 0
        ).sum()
    )
)


print(
    "Works with 2+ payment sub-signals:",
    int(
        (
            df["STAT_PAYMENT_SUBSIGNAL_COUNT"]
            >= 2
        ).sum()
    )
)


print(
    "Works with 3 payment sub-signals:",
    int(
        (
            df["STAT_PAYMENT_SUBSIGNAL_COUNT"]
            >= 3
        ).sum()
    )
)


# ============================================================
# RULE TRIGGER SUMMARY
# ============================================================

print(
    "\nStatistical rule trigger summary:"
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


# ============================================================
# TOP 20
# ============================================================

print(
    "\n" + "=" * 75
)

print(
    "TOP 20 STATISTICAL INVESTIGATION CANDIDATES"
)

print("=" * 75)


top_columns = [

    "WORK_ID",

    "STATE_NAME",
    "CONSTITUENCY",
    "MP_NAME",

    "SANCTION_AMOUNT",

    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",

    "STAT_PEER_COUNT",
    "STAT_PEER_MEDIAN",

    "STAT_SANCTION_TO_PEER_MEDIAN",

    "STAT_FINANCIAL_SCORE",
    "STAT_PAYMENT_BEHAVIOR_SCORE",
    "STAT_TIMELINE_SCORE",

    "STAT_PAYMENT_SUBSIGNAL_COUNT",

    "STAT_SCORE",
    "STAT_SEVERITY",

    "STAT_CATEGORY_COUNT",
    "STAT_STRONG_RULE_COUNT"
]


top_columns = [
    column
    for column in top_columns
    if column in candidates.columns
]


if len(candidates) > 0:

    print(
        candidates[
            top_columns
        ]
        .head(20)
        .to_string(
            index=False
        )
    )

else:

    print(
        "No statistical candidates."
    )


# ============================================================
# SCORE DISTRIBUTION OUTPUT
# ============================================================

distribution = (
    df[
        [
            "STAT_SCORE",
            "STAT_SEVERITY",
            "STAT_CANDIDATE",
            "STAT_CATEGORY_COUNT",
            "STAT_STRONG_RULE_COUNT"
        ]
    ]
    .groupby(
        [
            "STAT_SCORE",
            "STAT_SEVERITY"
        ],
        dropna=False
    )
    .size()
    .reset_index(
        name="WORK_COUNT"
    )
    .sort_values(
        "STAT_SCORE",
        ascending=False
    )
)


distribution.to_csv(
    DISTRIBUTION_FILE,
    index=False
)


# ============================================================
# FINAL
# ============================================================

print(
    "\n" + "=" * 75
)

print(
    "OUTPUT FILES"
)

print("=" * 75)


print(
    "\nStatistical candidates:"
)

print(
    OUTPUT_FILE
)


print(
    "\nStatistical summary:"
)

print(
    SUMMARY_FILE
)


print(
    "\nStatistical distribution:"
)

print(
    DISTRIBUTION_FILE
)


print(
    "\nStatistical detector completed successfully."
)

print("=" * 75)