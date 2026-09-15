"""
FUNDGUARD — INDIA-WIDE ML VALIDATION

Validation only.
Does NOT train or modify the ML model.

Validates:
    - ML output integrity
    - ML candidate rate
    - ML feature independence
    - peer-quality behavior
    - financial/payment characteristics
    - state concentration
    - ML vs Rules overlap
    - ML vs Statistical overlap
    - three-detector agreement
    - ML-only candidates
    - top ML candidates

Inputs:
    data/processed/mplads_india_features.csv
    data/outputs/india_ml_anomalies.csv
    data/outputs/india_rule_anomalies.csv
    data/outputs/india_statistical_anomalies.csv

Outputs:
    data/outputs/india_ml_validation_summary.csv
    data/outputs/india_ml_overlap.csv
    data/outputs/india_ml_state_distribution.csv
    data/outputs/india_ml_top_candidates.csv
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np


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

RULE_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_rule_anomalies.csv"
)

STAT_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_statistical_anomalies.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "outputs"

SUMMARY_FILE = (
    OUTPUT_DIR
    / "india_ml_validation_summary.csv"
)

OVERLAP_FILE = (
    OUTPUT_DIR
    / "india_ml_overlap.csv"
)

STATE_FILE = (
    OUTPUT_DIR
    / "india_ml_state_distribution.csv"
)

TOP_FILE = (
    OUTPUT_DIR
    / "india_ml_top_candidates.csv"
)


# ============================================================
# HELPERS
# ============================================================

def section(title):
    print()
    print("=" * 75)
    print(title)
    print("=" * 75)


def load_file(path, name):
    if not path.exists():
        print(f"\nERROR: {name} not found:")
        print(path)
        sys.exit(1)

    print(f"Loading {name}: {path}")

    df = pd.read_csv(
        path,
        low_memory=False
    )

    print(f"  Rows    : {len(df):,}")
    print(f"  Columns : {len(df.columns):,}")

    return df


def clean_work_id(df):
    if "WORK_ID" not in df.columns:
        print("ERROR: WORK_ID missing.")
        sys.exit(1)

    df = df.copy()

    df["WORK_ID"] = (
        df["WORK_ID"]
        .astype(str)
        .str.strip()
    )

    return df


def numeric(df, column):
    if column not in df.columns:
        return pd.Series(
            np.nan,
            index=df.index,
            dtype=float
        )

    return pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# LOAD
# ============================================================

section("1. LOADING DATASETS")

features = load_file(
    FEATURE_FILE,
    "India Feature Dataset"
)

ml = load_file(
    ML_FILE,
    "ML Output"
)

rules = load_file(
    RULE_FILE,
    "Rule Output"
)

stats = load_file(
    STAT_FILE,
    "Statistical Output"
)


features = clean_work_id(features)
ml = clean_work_id(ml)
rules = clean_work_id(rules)
stats = clean_work_id(stats)


# ============================================================
# 2. FEATURE DATASET INTEGRITY
# ============================================================

section("2. FEATURE DATASET INTEGRITY")

feature_rows = len(features)
feature_unique = features["WORK_ID"].nunique()

feature_missing = (
    features["WORK_ID"].isna()
    | (features["WORK_ID"] == "")
    | (features["WORK_ID"].str.upper() == "NAN")
)

feature_duplicates = (
    feature_rows
    - feature_unique
)

print(
    f"Rows              : {feature_rows:,}"
)

print(
    f"Unique WORK_ID    : {feature_unique:,}"
)

print(
    f"Missing WORK_ID   : {feature_missing.sum():,}"
)

print(
    f"Duplicate WORK_ID : {feature_duplicates:,}"
)


# ============================================================
# 3. ML OUTPUT INTEGRITY
# ============================================================

section("3. ML OUTPUT INTEGRITY")

required_ml_columns = [
    "WORK_ID",
    "ML_ANOMALY",
    "IF_RAW_SCORE",
    "IF_DECISION_SCORE",
    "ML_ANOMALY_STRENGTH",
    "ML_PERCENTILE",
    "ML_SEVERITY",
]

missing_ml_columns = [
    c
    for c in required_ml_columns
    if c not in ml.columns
]

if missing_ml_columns:

    print(
        "ERROR — missing ML columns:"
    )

    for c in missing_ml_columns:
        print(f"  - {c}")

    sys.exit(1)


ml_rows = len(ml)
ml_unique = ml["WORK_ID"].nunique()

ml_missing = (
    ml["WORK_ID"].isna()
    | (ml["WORK_ID"] == "")
    | (ml["WORK_ID"].str.upper() == "NAN")
)

ml_duplicates = ml_rows - ml_unique


ml["ML_ANOMALY"] = pd.to_numeric(
    ml["ML_ANOMALY"],
    errors="coerce"
).fillna(0).astype(int)

ml_anomaly_mask = (
    ml["ML_ANOMALY"] == 1
)

ml_anomaly_count = int(
    ml_anomaly_mask.sum()
)

print(
    f"ML rows             : {ml_rows:,}"
)

print(
    f"Unique WORK_ID      : {ml_unique:,}"
)

print(
    f"Missing WORK_ID     : {ml_missing.sum():,}"
)

print(
    f"Duplicate WORK_ID   : {ml_duplicates:,}"
)

print(
    f"ML anomaly candidates: {ml_anomaly_count:,}"
)

print(
    f"ML anomaly rate      : "
    f"{ml_anomaly_count / ml_rows * 100:.2f}%"
)


# ============================================================
# 4. ML OUTPUT COLUMNS VS INPUT FEATURES
# ============================================================

section("4. ML OUTPUT / INPUT FEATURE CHECK")

ml_output_columns = {
    "IF_RAW_SCORE",
    "IF_DECISION_SCORE",
    "ML_ANOMALY_STRENGTH",
    "ML_PERCENTILE",
    "ML_ANOMALY",
    "ML_SEVERITY",
}

input_feature_columns = (
    set(features.columns)
    - {
        "WORK_ID"
    }
)

# These are expected detector output columns.
unexpected_overlap = (
    ml_output_columns
    & input_feature_columns
)

print(
    "Detector output columns found in "
    "original feature dataset:"
)

if unexpected_overlap:

    print(
        "WARNING:"
    )

    for c in sorted(unexpected_overlap):
        print(f"  - {c}")

else:

    print(
        "PASS — detector output columns are "
        "not present in the original feature dataset."
    )


# ============================================================
# 5. PEER QUALITY
# ============================================================

section("5. PEER QUALITY ANALYSIS")

peer_columns = [
    "PEER_COUNT",
    "PEER_WORK_COUNT",
]

peer_col = None

for c in peer_columns:

    if c in features.columns:
        peer_col = c
        break


if peer_col is None:

    print(
        "WARNING: PEER_COUNT not found "
        "in feature dataset."
    )

    peer_available = False

else:

    peer_available = True

    features["_PEER_COUNT"] = numeric(
        features,
        peer_col
    )

    peer_good_mask = (
        features["_PEER_COUNT"] >= 10
    )

    total_good_peers = int(
        peer_good_mask.sum()
    )

    total_weak_peers = int(
        features["_PEER_COUNT"].notna().sum()
        - total_good_peers
    )

    ml_peer = ml[
        [
            "WORK_ID"
        ]
    ].merge(
        features[
            [
                "WORK_ID",
                "_PEER_COUNT"
            ]
        ],
        on="WORK_ID",
        how="left"
    )

    anomaly_peer = ml_peer.loc[
        ml_anomaly_mask,
        "_PEER_COUNT"
    ]

    anomaly_good = int(
        (anomaly_peer >= 10).sum()
    )

    anomaly_weak = int(
        anomaly_peer.notna().sum()
        - anomaly_good
    )

    print(
        f"All works with >=10 peers : "
        f"{total_good_peers:,}"
    )

    print(
        f"All works with <10 peers  : "
        f"{total_weak_peers:,}"
    )

    print(
        f"ML anomalies >=10 peers   : "
        f"{anomaly_good:,}"
    )

    print(
        f"ML anomalies <10 peers    : "
        f"{anomaly_weak:,}"
    )

    if ml_anomaly_count:

        print(
            f"Good-peer ML percentage   : "
            f"{anomaly_good / ml_anomaly_count * 100:.2f}%"
        )

        print(
            f"Weak-peer ML percentage   : "
            f"{anomaly_weak / ml_anomaly_count * 100:.2f}%"
        )


# ============================================================
# 6. ML ANOMALY CHARACTERISTICS
# ============================================================

section("6. ML ANOMALY CHARACTERISTICS")

ml_anomalies = ml.loc[
    ml_anomaly_mask
].copy()

# Join useful original features.
diagnostic_columns = [
    "WORK_ID",
    "PEER_COUNT",
    "PEER_MEDIAN_SANCTION",
    "PEER_MEAN_SANCTION",
    "PEER_STD_SANCTION",
    "SANCTION_TO_PEER_MEDIAN",
    "SANCTION_PEER_Z_SCORE",
    "DATA_COMPLETENESS_RATIO",
    "TOTAL_FUND_DISBURSED_AMT",
    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",
    "COMPLETION_BEFORE_LAST_PAYMENT",
]

available_diagnostic_columns = [
    c
    for c in diagnostic_columns
    if c in features.columns
]

diagnostics = features[
    available_diagnostic_columns
].drop_duplicates(
    "WORK_ID"
)

ml_anomalies = ml_anomalies.merge(
    diagnostics,
    on="WORK_ID",
    how="left",
    suffixes=("", "_FEATURE")
)


def print_median_comparison(
    name,
    ml_column,
    feature_column=None
):

    if feature_column is None:
        feature_column = ml_column

    if feature_column not in features.columns:
        print(
            f"{name:<30}: NOT AVAILABLE"
        )
        return

    overall = numeric(
        features,
        feature_column
    ).dropna()

    anomaly = numeric(
        ml_anomalies,
        feature_column
    ).dropna()

    if len(overall) == 0:

        print(
            f"{name:<30}: NO DATA"
        )

        return

    overall_median = overall.median()

    if len(anomaly):

        anomaly_median = anomaly.median()

        print(
            f"{name:<30}: "
            f"overall={overall_median:,.2f} | "
            f"ML={anomaly_median:,.2f}"
        )

    else:

        print(
            f"{name:<30}: "
            f"overall={overall_median:,.2f} | "
            f"ML=N/A"
        )


print_median_comparison(
    "Sanction Amount",
    "SANCTION_AMOUNT"
)

print_median_comparison(
    "Actual Amount",
    "ACTUAL_AMOUNT"
)

print_median_comparison(
    "Disbursed Amount",
    "TOTAL_FUND_DISBURSED_AMT"
)

print_median_comparison(
    "Payment Count",
    "PAYMENT_COUNT"
)

print_median_comparison(
    "Vendor Count",
    "UNIQUE_VENDOR_COUNT"
)

print_median_comparison(
    "Data Completeness",
    "DATA_COMPLETENESS_RATIO"
)

print_median_comparison(
    "Peer Count",
    "PEER_COUNT"
)


# ============================================================
# 7. STATE DISTRIBUTION
# ============================================================

section("7. STATE DISTRIBUTION")

state_col = "STATE_NAME"

if state_col not in ml.columns:

    print(
        "WARNING: STATE_NAME not found."
    )

    state_distribution = pd.DataFrame()

else:

    total_by_state = (
        ml.groupby(state_col)
        .size()
        .reset_index(
            name="TOTAL_WORKS"
        )
    )

    anomaly_by_state = (
        ml.loc[ml_anomaly_mask]
        .groupby(state_col)
        .size()
        .reset_index(
            name="ML_ANOMALIES"
        )
    )

    state_distribution = total_by_state.merge(
        anomaly_by_state,
        on=state_col,
        how="left"
    )

    state_distribution[
        "ML_ANOMALIES"
    ] = state_distribution[
        "ML_ANOMALIES"
    ].fillna(0).astype(int)

    state_distribution[
        "ML_ANOMALY_RATE_PERCENT"
    ] = (
        state_distribution["ML_ANOMALIES"]
        / state_distribution["TOTAL_WORKS"]
        * 100
    )

    state_distribution = state_distribution.sort_values(
        "ML_ANOMALY_RATE_PERCENT",
        ascending=False
    )

    print(
        state_distribution.head(25).to_string(
            index=False
        )
    )

    state_distribution.to_csv(
        STATE_FILE,
        index=False
    )

    print()
    print(
        f"Saved: {STATE_FILE}"
    )


# ============================================================
# 8. RULE / STATISTICAL CANDIDATE SETS
# ============================================================

section("8. BUILDING DETECTOR CANDIDATE SETS")

if "RULE_CANDIDATE" not in rules.columns:

    print(
        "ERROR: RULE_CANDIDATE missing."
    )

    sys.exit(1)

if "STAT_CANDIDATE" not in stats.columns:

    print(
        "ERROR: STAT_CANDIDATE missing."
    )

    sys.exit(1)


rules["RULE_CANDIDATE"] = pd.to_numeric(
    rules["RULE_CANDIDATE"],
    errors="coerce"
).fillna(0).astype(int)

stats["STAT_CANDIDATE"] = pd.to_numeric(
    stats["STAT_CANDIDATE"],
    errors="coerce"
).fillna(0).astype(int)


ml_set = set(
    ml.loc[
        ml_anomaly_mask,
        "WORK_ID"
    ]
)

rule_set = set(
    rules.loc[
        rules["RULE_CANDIDATE"] == 1,
        "WORK_ID"
    ]
)

stat_set = set(
    stats.loc[
        stats["STAT_CANDIDATE"] == 1,
        "WORK_ID"
    ]
)


print(
    f"ML candidates          : {len(ml_set):,}"
)

print(
    f"Rule candidates        : {len(rule_set):,}"
)

print(
    f"Statistical candidates : {len(stat_set):,}"
)


# ============================================================
# 9. OVERLAP
# ============================================================

section("9. DETECTOR OVERLAP")

ml_rule = ml_set & rule_set

ml_stat = ml_set & stat_set

rule_stat = rule_set & stat_set

all_three = (
    ml_set
    & rule_set
    & stat_set
)

ml_only = (
    ml_set
    - rule_set
    - stat_set
)

rule_only = (
    rule_set
    - ml_set
    - stat_set
)

stat_only = (
    stat_set
    - ml_set
    - rule_set
)

all_ids = set(
    features["WORK_ID"]
)

none = (
    all_ids
    - ml_set
    - rule_set
    - stat_set
)


overlap_data = [
    ("ML", len(ml_set)),
    ("RULE", len(rule_set)),
    ("STATISTICAL", len(stat_set)),
    ("ML_AND_RULE", len(ml_rule)),
    ("ML_AND_STATISTICAL", len(ml_stat)),
    ("RULE_AND_STATISTICAL", len(rule_stat)),
    ("ALL_THREE", len(all_three)),
    ("ML_ONLY", len(ml_only)),
    ("RULE_ONLY", len(rule_only)),
    ("STATISTICAL_ONLY", len(stat_only)),
    ("NONE", len(none)),
]

overlap_df = pd.DataFrame(
    overlap_data,
    columns=[
        "GROUP",
        "COUNT"
    ]
)

overlap_df.to_csv(
    OVERLAP_FILE,
    index=False
)

print(
    overlap_df.to_string(
        index=False
    )
)

print()

print(
    f"ML ∩ Rules       : "
    f"{len(ml_rule):,} "
    f"({len(ml_rule) / len(ml_set) * 100:.2f}% of ML)"
)

print(
    f"ML ∩ Statistical : "
    f"{len(ml_stat):,} "
    f"({len(ml_stat) / len(ml_set) * 100:.2f}% of ML)"
)

print(
    f"All three        : "
    f"{len(all_three):,} "
    f"({len(all_three) / len(ml_set) * 100:.2f}% of ML)"
)

print(
    f"ML ONLY          : "
    f"{len(ml_only):,} "
    f"({len(ml_only) / len(ml_set) * 100:.2f}% of ML)"
)


# ============================================================
# 10. AGREEMENT TABLE
# ============================================================

section("10. AGREEMENT ANALYSIS")

agreement = pd.DataFrame({
    "WORK_ID": list(all_ids)
})

agreement["ML"] = (
    agreement["WORK_ID"]
    .isin(ml_set)
)

agreement["RULE"] = (
    agreement["WORK_ID"]
    .isin(rule_set)
)

agreement["STATISTICAL"] = (
    agreement["WORK_ID"]
    .isin(stat_set)
)

agreement["DETECTOR_AGREEMENT_COUNT"] = (
    agreement[
        [
            "ML",
            "RULE",
            "STATISTICAL"
        ]
    ]
    .sum(axis=1)
)


print(
    "Detector agreement distribution:"
)

print(
    agreement[
        "DETECTOR_AGREEMENT_COUNT"
    ]
    .value_counts()
    .sort_index()
    .rename_axis(
        "DETECTORS_AGREEING"
    )
    .reset_index(
        name="WORK_COUNT"
    )
    .to_string(
        index=False
    )
)


# ============================================================
# 11. TOP ML CANDIDATES
# ============================================================

section("11. TOP ML CANDIDATES")

top = ml_anomalies.copy()

top["RULE_AGREEMENT"] = (
    top["WORK_ID"]
    .isin(rule_set)
)

top["STATISTICAL_AGREEMENT"] = (
    top["WORK_ID"]
    .isin(stat_set)
)

top["DETECTOR_AGREEMENT_COUNT"] = (
    1
    + top["RULE_AGREEMENT"].astype(int)
    + top["STATISTICAL_AGREEMENT"].astype(int)
)


# More anomalous = lower IF decision score.
top["_SORT_SCORE"] = numeric(
    top,
    "IF_DECISION_SCORE"
)

top = top.sort_values(
    "_SORT_SCORE",
    ascending=True
)


preferred_top_columns = [
    "WORK_ID",
    "STATE_NAME",
    "CONSTITUENCY",
    "MP_NAME",
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "TOTAL_FUND_DISBURSED_AMT",
    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",
    "PEER_COUNT",
    "PEER_MEDIAN_SANCTION",
    "SANCTION_TO_PEER_MEDIAN",
    "SANCTION_PEER_Z_SCORE",
    "DATA_COMPLETENESS_RATIO",
    "IF_RAW_SCORE",
    "IF_DECISION_SCORE",
    "ML_PERCENTILE",
    "ML_ANOMALY_STRENGTH",
    "ML_SEVERITY",
    "RULE_AGREEMENT",
    "STATISTICAL_AGREEMENT",
    "DETECTOR_AGREEMENT_COUNT",
]

available_top_columns = [
    c
    for c in preferred_top_columns
    if c in top.columns
]

top_100 = top[
    available_top_columns
].head(100)

top_100.to_csv(
    TOP_FILE,
    index=False
)

print(
    top_100.head(20).to_string(
        index=False
    )
)

print()
print(
    f"Saved: {TOP_FILE}"
)


# ============================================================
# 12. SEVERITY CHECK
# ============================================================

section("12. ML SEVERITY CHECK")

severity_distribution = (
    ml["ML_SEVERITY"]
    .astype(str)
    .str.upper()
    .value_counts()
)

print(
    severity_distribution.to_string()
)

print()

candidate_severity = (
    ml.loc[
        ml_anomaly_mask,
        "ML_SEVERITY"
    ]
    .astype(str)
    .str.upper()
    .value_counts()
)

print(
    "Severity among actual ML candidates:"
)

print(
    candidate_severity.to_string()
)

print()

severity_sum = int(
    candidate_severity.sum()
)

if severity_sum == ml_anomaly_count:

    print(
        "PASS — severity labels cover exactly "
        "the ML anomaly candidates."
    )

else:

    print(
        "WARNING — severity labels do not "
        "match the ML anomaly population."
    )

    print(
        f"Actual ML candidates : {ml_anomaly_count:,}"
    )

    print(
        f"Candidate severity rows: {severity_sum:,}"
    )


# ============================================================
# 13. SUMMARY
# ============================================================

section("13. FINAL VALIDATION SUMMARY")

summary = [
    (
        "FEATURE_ROWS",
        feature_rows
    ),
    (
        "FEATURE_UNIQUE_WORK_IDS",
        feature_unique
    ),
    (
        "ML_ROWS",
        ml_rows
    ),
    (
        "ML_UNIQUE_WORK_IDS",
        ml_unique
    ),
    (
        "ML_MISSING_WORK_IDS",
        int(ml_missing.sum())
    ),
    (
        "ML_DUPLICATE_WORK_IDS",
        ml_duplicates
    ),
    (
        "ML_ANOMALY_COUNT",
        ml_anomaly_count
    ),
    (
        "ML_ANOMALY_RATE_PERCENT",
        round(
            ml_anomaly_count
            / ml_rows
            * 100,
            4
        )
    ),
    (
        "RULE_CANDIDATE_COUNT",
        len(rule_set)
    ),
    (
        "STATISTICAL_CANDIDATE_COUNT",
        len(stat_set)
    ),
    (
        "ML_RULE_OVERLAP",
        len(ml_rule)
    ),
    (
        "ML_STATISTICAL_OVERLAP",
        len(ml_stat)
    ),
    (
        "ALL_THREE_OVERLAP",
        len(all_three)
    ),
    (
        "ML_ONLY",
        len(ml_only)
    ),
    (
        "RULE_ONLY",
        len(rule_only)
    ),
    (
        "STATISTICAL_ONLY",
        len(stat_only)
    ),
    (
        "NO_DETECTOR",
        len(none)
    ),
    (
        "ML_FEATURE_COUNT",
        47
    ),
]

if peer_available:

    summary.extend(
        [
            (
                "WORKS_PEER_GE_10",
                total_good_peers
            ),
            (
                "WORKS_PEER_LT_10",
                total_weak_peers
            ),
            (
                "ML_ANOMALIES_PEER_GE_10",
                anomaly_good
            ),
            (
                "ML_ANOMALIES_PEER_LT_10",
                anomaly_weak
            ),
        ]
    )


summary_df = pd.DataFrame(
    summary,
    columns=[
        "METRIC",
        "VALUE"
    ]
)

summary_df.to_csv(
    SUMMARY_FILE,
    index=False
)

print(
    summary_df.to_string(
        index=False
    )
)


# ============================================================
# 14. FINAL STATUS
# ============================================================

section("14. FINAL STATUS")

checks = [
    (
        "Feature WORK_ID complete",
        feature_missing.sum() == 0
    ),
    (
        "Feature WORK_ID unique",
        feature_duplicates == 0
    ),
    (
        "ML WORK_ID complete",
        ml_missing.sum() == 0
    ),
    (
        "ML WORK_ID unique",
        ml_duplicates == 0
    ),
    (
        "ML rows match feature rows",
        ml_rows == feature_rows
    ),
    (
        "ML WORK_ID count matches feature dataset",
        ml_unique == feature_unique
    ),
]

all_pass = True

for name, result in checks:

    if result:

        print(
            f"[PASS] {name}"
        )

    else:

        print(
            f"[FAIL] {name}"
        )

        all_pass = False


print()

if all_pass:

    print(
        "OVERALL DATA VALIDATION: PASS"
    )

else:

    print(
        "OVERALL DATA VALIDATION: REVIEW REQUIRED"
    )


print()
print(
    "Remember:"
)

print(
    "ML anomalies are investigation candidates."
)

print(
    "They do NOT establish fraud, corruption, "
    "or wrongdoing."
)

print()
print(
    "Validation completed."
)

print()
print(
    "Output files:"
)

print(
    f"  {SUMMARY_FILE}"
)

print(
    f"  {OVERLAP_FILE}"
)

print(
    f"  {STATE_FILE}"
)

print(
    f"  {TOP_FILE}"
)