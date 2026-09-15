"""
FUNDGUARD — INDIA-WIDE ML DIAGNOSTIC

Purpose
-------
Diagnose whether the current Isolation Forest is being affected by:

1. State-level distribution differences
2. Weak peer groups
3. Payment behavior
4. Vendor behavior
5. Financial scale
6. Data completeness
7. State concentration

This script DOES NOT:
    - train a model
    - modify ML output
    - change detector thresholds
    - declare fraud

It only analyzes the existing ML results.

Inputs
------
data/processed/mplads_india_features.csv
data/outputs/india_ml_anomalies.csv

Outputs
-------
data/outputs/ml_diagnostic_state.csv
data/outputs/ml_diagnostic_peer.csv
data/outputs/ml_diagnostic_features.csv
"""


from pathlib import Path
import sys
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_features.csv"
)

ML_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_ml_anomalies.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "outputs"
)


STATE_OUTPUT = (
    OUTPUT_DIR
    / "ml_diagnostic_state.csv"
)

PEER_OUTPUT = (
    OUTPUT_DIR
    / "ml_diagnostic_peer.csv"
)

FEATURE_OUTPUT = (
    OUTPUT_DIR
    / "ml_diagnostic_features.csv"
)


# ============================================================
# HELPERS
# ============================================================

def section(title):

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def load_csv(path, name):

    if not path.exists():

        print()
        print(f"ERROR: {name} not found:")
        print(path)

        sys.exit(1)

    print(
        f"Loading {name}: {path}"
    )

    df = pd.read_csv(
        path,
        low_memory=False
    )

    print(
        f"  Rows    : {len(df):,}"
    )

    print(
        f"  Columns : {len(df.columns):,}"
    )

    return df


def numeric(df, column):

    if column not in df.columns:

        return pd.Series(
            np.nan,
            index=df.index
        )

    return pd.to_numeric(
        df[column],
        errors="coerce"
    )


def median_value(series):

    series = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if len(series) == 0:
        return np.nan

    return series.median()


def mean_value(series):

    series = pd.to_numeric(
        series,
        errors="coerce"
    ).dropna()

    if len(series) == 0:
        return np.nan

    return series.mean()


# ============================================================
# LOAD
# ============================================================

section("1. LOADING DATA")

features = load_csv(
    FEATURE_FILE,
    "India Feature Dataset"
)

ml = load_csv(
    ML_FILE,
    "ML Output"
)


# ============================================================
# BASIC VALIDATION
# ============================================================

section("2. BASIC VALIDATION")

if "WORK_ID" not in features.columns:
    print("ERROR: WORK_ID missing from feature dataset.")
    sys.exit(1)

if "WORK_ID" not in ml.columns:
    print("ERROR: WORK_ID missing from ML output.")
    sys.exit(1)

if "ML_ANOMALY" not in ml.columns:
    print("ERROR: ML_ANOMALY missing from ML output.")
    sys.exit(1)

features["WORK_ID"] = (
    features["WORK_ID"]
    .astype(str)
    .str.strip()
)

ml["WORK_ID"] = (
    ml["WORK_ID"]
    .astype(str)
    .str.strip()
)

ml["ML_ANOMALY"] = pd.to_numeric(
    ml["ML_ANOMALY"],
    errors="coerce"
).fillna(0).astype(int)

ml_anomaly_count = int(
    (ml["ML_ANOMALY"] == 1).sum()
)

print(
    f"Feature rows       : {len(features):,}"
)

print(
    f"ML rows            : {len(ml):,}"
)

print(
    f"ML anomalies       : {ml_anomaly_count:,}"
)

print(
    f"ML anomaly rate    : "
    f"{ml_anomaly_count / len(ml) * 100:.2f}%"
)


# ============================================================
# MERGE ML FLAG WITH ORIGINAL FEATURES
# ============================================================

section("3. MERGING ML RESULTS WITH FEATURES")

ml_flag = ml[
    [
        "WORK_ID",
        "ML_ANOMALY",
        "IF_RAW_SCORE",
        "IF_DECISION_SCORE",
        "ML_PERCENTILE",
        "ML_ANOMALY_STRENGTH",
        "ML_SEVERITY",
    ]
].copy()

analysis = features.merge(
    ml_flag,
    on="WORK_ID",
    how="left",
    suffixes=("", "_ML")
)

analysis["ML_ANOMALY"] = (
    analysis["ML_ANOMALY"]
    .fillna(0)
    .astype(int)
)

print(
    f"Merged rows : {len(analysis):,}"
)

print(
    f"Missing ML flags : "
    f"{analysis['ML_ANOMALY'].isna().sum():,}"
)


# ============================================================
# 4. STATE DIAGNOSTIC
# ============================================================

section("4. STATE-LEVEL ML DIAGNOSTIC")

if "STATE_NAME" not in analysis.columns:

    print(
        "ERROR: STATE_NAME missing."
    )

    sys.exit(1)


state = (
    analysis
    .groupby("STATE_NAME")
    .agg(
        TOTAL_WORKS=(
            "WORK_ID",
            "count"
        ),
        ML_ANOMALIES=(
            "ML_ANOMALY",
            "sum"
        ),
        MEDIAN_SANCTION=(
            "SANCTION_AMOUNT",
            median_value
        ),
        MEAN_SANCTION=(
            "SANCTION_AMOUNT",
            mean_value
        ),
        MEDIAN_PAYMENT_COUNT=(
            "PAYMENT_COUNT",
            median_value
        ),
        MEAN_PAYMENT_COUNT=(
            "PAYMENT_COUNT",
            mean_value
        ),
        MEDIAN_VENDOR_COUNT=(
            "UNIQUE_VENDOR_COUNT",
            median_value
        ),
        MEAN_VENDOR_COUNT=(
            "UNIQUE_VENDOR_COUNT",
            mean_value
        ),
        MEDIAN_COMPLETENESS=(
            "DATA_COMPLETENESS_RATIO",
            median_value
        ),
        MEDIAN_PEER_COUNT=(
            "PEER_COUNT",
            median_value
        ),
    )
    .reset_index()
)

state[
    "ML_ANOMALY_RATE_PERCENT"
] = (
    state["ML_ANOMALIES"]
    / state["TOTAL_WORKS"]
    * 100
)

state[
    "INDIA_RATE_RATIO"
] = (
    state["ML_ANOMALY_RATE_PERCENT"]
    / (
        ml_anomaly_count
        / len(analysis)
        * 100
    )
)

state = state.sort_values(
    "ML_ANOMALY_RATE_PERCENT",
    ascending=False
)

print(
    state.to_string(
        index=False
    )
)

state.to_csv(
    STATE_OUTPUT,
    index=False
)

print()
print(
    f"Saved: {STATE_OUTPUT}"
)


# ============================================================
# 5. STATE CONCENTRATION
# ============================================================

section("5. STATE CONCENTRATION")

state_sorted_by_count = state.sort_values(
    "ML_ANOMALIES",
    ascending=False
)

print(
    "Top states by number of ML anomalies:"
)

print(
    state_sorted_by_count[
        [
            "STATE_NAME",
            "TOTAL_WORKS",
            "ML_ANOMALIES",
            "ML_ANOMALY_RATE_PERCENT",
        ]
    ]
    .head(15)
    .to_string(index=False)
)

print()

print(
    "Top states by anomaly rate:"
)

print(
    state[
        [
            "STATE_NAME",
            "TOTAL_WORKS",
            "ML_ANOMALIES",
            "ML_ANOMALY_RATE_PERCENT",
            "INDIA_RATE_RATIO",
        ]
    ]
    .head(15)
    .to_string(index=False)
)


# ============================================================
# 6. PEER QUALITY DIAGNOSTIC
# ============================================================

section("6. PEER QUALITY DIAGNOSTIC")

if "PEER_COUNT" not in analysis.columns:

    print(
        "ERROR: PEER_COUNT missing."
    )

    sys.exit(1)


analysis["_PEER_GROUP"] = np.where(
    analysis["PEER_COUNT"] >= 30,
    "30+",
    np.where(
        analysis["PEER_COUNT"] >= 10,
        "10-29",
        "0-9"
    )
)


peer = (
    analysis
    .groupby("_PEER_GROUP")
    .agg(
        TOTAL_WORKS=(
            "WORK_ID",
            "count"
        ),
        ML_ANOMALIES=(
            "ML_ANOMALY",
            "sum"
        ),
        MEDIAN_SANCTION=(
            "SANCTION_AMOUNT",
            median_value
        ),
        MEDIAN_PAYMENT_COUNT=(
            "PAYMENT_COUNT",
            median_value
        ),
        MEDIAN_VENDOR_COUNT=(
            "UNIQUE_VENDOR_COUNT",
            median_value
        ),
        MEDIAN_COMPLETENESS=(
            "DATA_COMPLETENESS_RATIO",
            median_value
        ),
    )
    .reset_index()
)

peer[
    "ML_ANOMALY_RATE_PERCENT"
] = (
    peer["ML_ANOMALIES"]
    / peer["TOTAL_WORKS"]
    * 100
)

print(
    peer.to_string(
        index=False
    )
)

peer.to_csv(
    PEER_OUTPUT,
    index=False
)

print()
print(
    f"Saved: {PEER_OUTPUT}"
)


# ============================================================
# 7. ANOMALY VS NORMAL FEATURE COMPARISON
# ============================================================

section("7. ML ANOMALY VS NORMAL COMPARISON")

candidate_mask = (
    analysis["ML_ANOMALY"] == 1
)

normal_mask = (
    analysis["ML_ANOMALY"] == 0
)


diagnostic_features = [
    "SANCTION_AMOUNT",
    "RECOMMENDED_AMOUNT",
    "ACTUAL_AMOUNT",
    "TOTAL_FUND_DISBURSED_AMT",
    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",
    "DATA_COMPLETENESS_RATIO",
    "PEER_COUNT",
    "SANCTION_TO_PEER_MEDIAN",
    "SANCTION_PEER_Z_SCORE",
    "COMPLETION_DURATION_DAYS",
    "PAYMENT_AFTER_REPORTED_COMPLETION_DAYS",
]


rows = []

for feature in diagnostic_features:

    if feature not in analysis.columns:
        continue

    overall = numeric(
        analysis,
        feature
    )

    anomaly = overall[
        candidate_mask
    ].dropna()

    normal = overall[
        normal_mask
    ].dropna()

    if len(anomaly) == 0 or len(normal) == 0:
        continue

    anomaly_median = anomaly.median()
    normal_median = normal.median()

    anomaly_mean = anomaly.mean()
    normal_mean = normal.mean()

    if normal_median != 0:

        median_ratio = (
            anomaly_median
            / normal_median
        )

    else:

        median_ratio = np.nan

    rows.append(
        {
            "FEATURE": feature,
            "ANOMALY_COUNT": len(anomaly),
            "NORMAL_COUNT": len(normal),
            "ANOMALY_MEDIAN": anomaly_median,
            "NORMAL_MEDIAN": normal_median,
            "MEDIAN_RATIO": median_ratio,
            "ANOMALY_MEAN": anomaly_mean,
            "NORMAL_MEAN": normal_mean,
        }
    )


feature_comparison = pd.DataFrame(
    rows
)

if len(feature_comparison):

    feature_comparison[
        "ABS_MEDIAN_RATIO_DISTANCE"
    ] = (
        feature_comparison[
            "MEDIAN_RATIO"
        ]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .sub(1)
        .abs()
    )

    feature_comparison = (
        feature_comparison
        .sort_values(
            "ABS_MEDIAN_RATIO_DISTANCE",
            ascending=False
        )
    )

    print(
        feature_comparison.to_string(
            index=False
        )
    )

    feature_comparison.to_csv(
        FEATURE_OUTPUT,
        index=False
    )

    print()
    print(
        f"Saved: {FEATURE_OUTPUT}"
    )

else:

    print(
        "No diagnostic features available."
    )


# ============================================================
# 8. PAYMENT BEHAVIOR
# ============================================================

section("8. PAYMENT BEHAVIOR ANALYSIS")

if "PAYMENT_COUNT" in analysis.columns:

    payment = numeric(
        analysis,
        "PAYMENT_COUNT"
    )

    print(
        "Payment count distribution:"
    )

    print(
        pd.DataFrame(
            {
                "GROUP": [
                    "NORMAL",
                    "ML_ANOMALY",
                ],
                "MEDIAN": [
                    payment[
                        normal_mask
                    ].median(),
                    payment[
                        candidate_mask
                    ].median(),
                ],
                "MEAN": [
                    payment[
                        normal_mask
                    ].mean(),
                    payment[
                        candidate_mask
                    ].mean(),
                ],
                "P95": [
                    payment[
                        normal_mask
                    ].quantile(0.95),
                    payment[
                        candidate_mask
                    ].quantile(0.95),
                ],
                "P99": [
                    payment[
                        normal_mask
                    ].quantile(0.99),
                    payment[
                        candidate_mask
                    ].quantile(0.99),
                ],
            }
        ).to_string(
            index=False
        )
    )


# ============================================================
# 9. VENDOR BEHAVIOR
# ============================================================

section("9. VENDOR BEHAVIOR ANALYSIS")

if "UNIQUE_VENDOR_COUNT" in analysis.columns:

    vendor = numeric(
        analysis,
        "UNIQUE_VENDOR_COUNT"
    )

    print(
        pd.DataFrame(
            {
                "GROUP": [
                    "NORMAL",
                    "ML_ANOMALY",
                ],
                "MEDIAN": [
                    vendor[
                        normal_mask
                    ].median(),
                    vendor[
                        candidate_mask
                    ].median(),
                ],
                "MEAN": [
                    vendor[
                        normal_mask
                    ].mean(),
                    vendor[
                        candidate_mask
                    ].mean(),
                ],
                "P95": [
                    vendor[
                        normal_mask
                    ].quantile(0.95),
                    vendor[
                        candidate_mask
                    ].quantile(0.95),
                ],
                "P99": [
                    vendor[
                        normal_mask
                    ].quantile(0.99),
                    vendor[
                        candidate_mask
                    ].quantile(0.99),
                ],
            }
        ).to_string(
            index=False
        )
    )


# ============================================================
# 10. FINANCIAL SCALE
# ============================================================

section("10. FINANCIAL SCALE ANALYSIS")

if "SANCTION_AMOUNT" in analysis.columns:

    sanction = numeric(
        analysis,
        "SANCTION_AMOUNT"
    )

    anomaly_sanction = sanction[
        candidate_mask
    ].dropna()

    normal_sanction = sanction[
        normal_mask
    ].dropna()

    print(
        f"Normal median sanction : "
        f"{normal_sanction.median():,.2f}"
    )

    print(
        f"ML median sanction     : "
        f"{anomaly_sanction.median():,.2f}"
    )

    print(
        f"Normal P95 sanction    : "
        f"{normal_sanction.quantile(.95):,.2f}"
    )

    print(
        f"ML P95 sanction        : "
        f"{anomaly_sanction.quantile(.95):,.2f}"
    )

    print(
        f"Normal P99 sanction    : "
        f"{normal_sanction.quantile(.99):,.2f}"
    )

    print(
        f"ML P99 sanction        : "
        f"{anomaly_sanction.quantile(.99):,.2f}"
    )


# ============================================================
# 11. STATE + FEATURE PATTERN
# ============================================================

section("11. STATE PATTERN INTERPRETATION")

major_states = state[
    state["TOTAL_WORKS"] >= 500
].copy()

print(
    "States with at least 500 works:"
)

print(
    major_states[
        [
            "STATE_NAME",
            "TOTAL_WORKS",
            "ML_ANOMALIES",
            "ML_ANOMALY_RATE_PERCENT",
            "MEDIAN_SANCTION",
            "MEDIAN_PAYMENT_COUNT",
            "MEDIAN_VENDOR_COUNT",
            "MEDIAN_COMPLETENESS",
            "MEDIAN_PEER_COUNT",
        ]
    ]
    .sort_values(
        "ML_ANOMALY_RATE_PERCENT",
        ascending=False
    )
    .to_string(index=False)
)


# ============================================================
# 12. HIGH-RATE STATE DEEP CHECK
# ============================================================

section("12. HIGH-RATE STATE CHECK")

high_rate_states = major_states[
    major_states[
        "ML_ANOMALY_RATE_PERCENT"
    ]
    >
    (
        ml_anomaly_count
        / len(analysis)
        * 100
        * 2
    )
]

if len(high_rate_states):

    print(
        "Major states with anomaly rate "
        "> 2x India rate:"
    )

    print(
        high_rate_states[
            [
                "STATE_NAME",
                "TOTAL_WORKS",
                "ML_ANOMALIES",
                "ML_ANOMALY_RATE_PERCENT",
                "INDIA_RATE_RATIO",
                "MEDIAN_SANCTION",
                "MEDIAN_PAYMENT_COUNT",
                "MEDIAN_VENDOR_COUNT",
            ]
        ]
        .sort_values(
            "ML_ANOMALY_RATE_PERCENT",
            ascending=False
        )
        .to_string(index=False)
    )

else:

    print(
        "No major state exceeds 2x "
        "the India-wide anomaly rate."
    )


# ============================================================
# 13. FINAL DIAGNOSTIC SUMMARY
# ============================================================

section("13. DIAGNOSTIC SUMMARY")

india_rate = (
    ml_anomaly_count
    / len(analysis)
    * 100
)

weak_peer_anomalies = int(
    (
        analysis.loc[
            candidate_mask,
            "PEER_COUNT"
        ]
        < 10
    ).sum()
)

good_peer_anomalies = int(
    (
        analysis.loc[
            candidate_mask,
            "PEER_COUNT"
        ]
        >= 10
    ).sum()
)


print(
    f"India ML anomaly rate       : "
    f"{india_rate:.2f}%"
)

print(
    f"ML anomalies                : "
    f"{ml_anomaly_count:,}"
)

print(
    f"ML anomalies with <10 peers : "
    f"{weak_peer_anomalies:,}"
)

print(
    f"ML anomalies with >=10 peers: "
    f"{good_peer_anomalies:,}"
)

print()

if ml_anomaly_count:

    print(
        f"Weak-peer anomaly share     : "
        f"{weak_peer_anomalies / ml_anomaly_count * 100:.2f}%"
    )

    print(
        f"Good-peer anomaly share     : "
        f"{good_peer_anomalies / ml_anomaly_count * 100:.2f}%"
    )


# ============================================================
# FINAL INTERPRETATION
# ============================================================

section("14. INTERPRETATION")

print(
    "This diagnostic does NOT determine whether anomalies "
    "represent fraud or corruption."
)

print()

print(
    "It is specifically checking whether the ML detector "
    "is dominated by state differences, peer quality, "
    "financial scale, payment behavior, or vendor behavior."
)

print()

print(
    "Use the results to decide whether the Isolation Forest "
    "should remain global or become state-aware/hierarchical."
)

print()

print(
    "Diagnostic completed."
)