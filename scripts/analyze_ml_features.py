from pathlib import Path
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

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "outputs"
)

FEATURE_OUTPUT = (
    OUTPUT_DIR
    / "ml_feature_anomaly_comparison.csv"
)

STATE_FEATURE_OUTPUT = (
    OUTPUT_DIR
    / "ml_state_feature_analysis.csv"
)

AVAILABILITY_OUTPUT = (
    OUTPUT_DIR
    / "ml_feature_availability.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

MIN_STATE_WORKS = 100


# Administrative identifiers.
EXCLUDED_FEATURES = {
    "WORK_ID",
    "STATE_ID",
    "CONSTITUENCY_ID",
    "MP_ID",
}


# ============================================================
# HELPER
# ============================================================

def section(title):

    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# ============================================================
# 1. LOAD DATA
# ============================================================

section("1. LOADING DATA")

if not FEATURE_FILE.exists():

    print(f"ERROR: Feature file not found:")
    print(FEATURE_FILE)
    raise SystemExit(1)


if not ML_FILE.exists():

    print(f"ERROR: ML output file not found:")
    print(ML_FILE)
    raise SystemExit(1)


features = pd.read_csv(
    FEATURE_FILE,
    low_memory=False
)

ml = pd.read_csv(
    ML_FILE,
    low_memory=False
)

print(
    f"Feature rows : {len(features):,}"
)

print(
    f"ML rows      : {len(ml):,}"
)


# ============================================================
# 2. PREPARE DATA
# ============================================================

section("2. PREPARING DATA")

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


# Make sure ML anomaly column is numeric.
ml["ML_ANOMALY"] = pd.to_numeric(
    ml["ML_ANOMALY"],
    errors="coerce"
).fillna(0).astype(int)


# Only bring the columns we need from ML output.
ml_columns = [
    "WORK_ID",
    "ML_ANOMALY",
    "IF_RAW_SCORE",
    "IF_DECISION_SCORE",
    "ML_PERCENTILE",
]

available_ml_columns = [
    c for c in ml_columns
    if c in ml.columns
]


analysis = features.merge(
    ml[available_ml_columns],
    on="WORK_ID",
    how="inner"
)


# Create this in one operation instead of repeated inserts.
analysis = analysis.assign(
    IS_ML_ANOMALY=(
        analysis["ML_ANOMALY"] == 1
    )
)


print(
    f"Analysis rows       : {len(analysis):,}"
)

ml_anomaly_count = int(
    analysis["IS_ML_ANOMALY"].sum()
)

print(
    f"ML anomalies        : {ml_anomaly_count:,}"
)

print(
    f"ML anomaly rate     : "
    f"{ml_anomaly_count / len(analysis) * 100:.2f}%"
)


# ============================================================
# 3. IDENTIFY ACTUAL NUMERIC FEATURES
# ============================================================

section("3. IDENTIFYING NUMERIC FEATURES")


numeric_features = []


for column in features.columns:

    if column in EXCLUDED_FEATURES:
        continue

    series = features[column]

    # --------------------------------------------------------
    # Exclude real boolean dtype
    # --------------------------------------------------------

    if pd.api.types.is_bool_dtype(series):
        continue


    # --------------------------------------------------------
    # Try numeric conversion
    # --------------------------------------------------------

    converted = pd.to_numeric(
        series,
        errors="coerce"
    )


    if converted.notna().sum() == 0:
        continue


    # --------------------------------------------------------
    # Exclude columns that are actually True/False stored
    # as strings or objects.
    # --------------------------------------------------------

    non_null = series.dropna()

    if len(non_null) > 0:

        string_values = (
            non_null
            .astype(str)
            .str.strip()
            .str.lower()
        )

        boolean_like = string_values.isin(
            ["true", "false"]
        ).all()

        if boolean_like:
            continue


    numeric_features.append(column)


print(
    f"Numeric feature candidates: "
    f"{len(numeric_features):,}"
)


# ============================================================
# 4. ANOMALY VS NORMAL FEATURE ANALYSIS
# ============================================================

section("4. ANOMALY VS NORMAL FEATURE ANALYSIS")


anomaly_mask = (
    analysis["IS_ML_ANOMALY"]
)

normal_mask = (
    ~analysis["IS_ML_ANOMALY"]
)


comparison_rows = []


for feature in numeric_features:

    values = pd.to_numeric(
        analysis[feature],
        errors="coerce"
    )


    anomaly = values[
        anomaly_mask
    ].dropna()

    normal = values[
        normal_mask
    ].dropna()


    # Need enough observations to make the comparison useful.
    if len(anomaly) < 20:
        continue

    if len(normal) < 20:
        continue


    # --------------------------------------------------------
    # Basic statistics
    # --------------------------------------------------------

    anomaly_median = anomaly.median()
    normal_median = normal.median()

    anomaly_mean = anomaly.mean()
    normal_mean = normal.mean()

    anomaly_p95 = anomaly.quantile(
        0.95
    )

    normal_p95 = normal.quantile(
        0.95
    )

    anomaly_p99 = anomaly.quantile(
        0.99
    )

    normal_p99 = normal.quantile(
        0.99
    )


    # --------------------------------------------------------
    # Median ratio
    # --------------------------------------------------------

    if abs(normal_median) > 1e-12:

        median_ratio = (
            anomaly_median
            / normal_median
        )

        median_difference_percent = (
            (
                anomaly_median
                - normal_median
            )
            / abs(normal_median)
            * 100
        )

    else:

        median_ratio = np.nan

        median_difference_percent = np.nan


    # --------------------------------------------------------
    # Standardized difference
    # --------------------------------------------------------

    normal_std = normal.std()

    if (
        pd.notna(normal_std)
        and normal_std > 1e-12
    ):

        standardized_difference = (
            anomaly_median
            - normal_median
        ) / normal_std

    else:

        standardized_difference = np.nan


    comparison_rows.append(
        {
            "FEATURE": feature,

            "ANOMALY_COUNT":
                len(anomaly),

            "NORMAL_COUNT":
                len(normal),

            "ANOMALY_MEDIAN":
                anomaly_median,

            "NORMAL_MEDIAN":
                normal_median,

            "MEDIAN_RATIO":
                median_ratio,

            "MEDIAN_DIFFERENCE_PERCENT":
                median_difference_percent,

            "ANOMALY_MEAN":
                anomaly_mean,

            "NORMAL_MEAN":
                normal_mean,

            "ANOMALY_P95":
                anomaly_p95,

            "NORMAL_P95":
                normal_p95,

            "ANOMALY_P99":
                anomaly_p99,

            "NORMAL_P99":
                normal_p99,

            "NORMAL_STD":
                normal_std,

            "STANDARDIZED_DIFFERENCE":
                standardized_difference,
        }
    )


comparison = pd.DataFrame(
    comparison_rows
)


if comparison.empty:

    print(
        "ERROR: No comparable numeric features found."
    )

    raise SystemExit(1)


comparison[
    "ABS_STANDARDIZED_DIFFERENCE"
] = (
    comparison[
        "STANDARDIZED_DIFFERENCE"
    ]
    .abs()
)


comparison = comparison.sort_values(
    "ABS_STANDARDIZED_DIFFERENCE",
    ascending=False
)


print()

print(
    comparison[
        [
            "FEATURE",
            "ANOMALY_MEDIAN",
            "NORMAL_MEDIAN",
            "MEDIAN_RATIO",
            "STANDARDIZED_DIFFERENCE",
        ]
    ]
    .head(50)
    .to_string(index=False)
)


comparison.to_csv(
    FEATURE_OUTPUT,
    index=False
)


print()

print(
    f"Saved: {FEATURE_OUTPUT}"
)


# ============================================================
# 5. STRONGEST FEATURE DIFFERENCES
# ============================================================

section("5. STRONGEST FEATURE DIFFERENCES")


strong = comparison[
    comparison[
        "ABS_STANDARDIZED_DIFFERENCE"
    ] >= 1.0
]


print(
    "Features with "
    "|standardized difference| >= 1:"
    f" {len(strong)}"
)


print()

if len(strong) > 0:

    print(
        strong[
            [
                "FEATURE",
                "ANOMALY_MEDIAN",
                "NORMAL_MEDIAN",
                "MEDIAN_RATIO",
                "STANDARDIZED_DIFFERENCE",
            ]
        ]
        .head(50)
        .to_string(index=False)
    )

else:

    print(
        "No feature has a standardized "
        "difference >= 1."
    )


# ============================================================
# 6. FEATURE AVAILABILITY
# ============================================================

section("6. FEATURE AVAILABILITY")


availability_rows = []


for feature in numeric_features:

    values = pd.to_numeric(
        analysis[feature],
        errors="coerce"
    )


    anomaly_values = values[
        anomaly_mask
    ]

    normal_values = values[
        normal_mask
    ]


    anomaly_available = (
        anomaly_values.notna().mean()
        * 100
    )

    normal_available = (
        normal_values.notna().mean()
        * 100
    )


    availability_rows.append(
        {
            "FEATURE":
                feature,

            "ANOMALY_AVAILABLE_PERCENT":
                anomaly_available,

            "NORMAL_AVAILABLE_PERCENT":
                normal_available,

            "AVAILABILITY_GAP_PERCENT":
                anomaly_available
                - normal_available,
        }
    )


availability = pd.DataFrame(
    availability_rows
)


availability = availability.sort_values(
    "AVAILABILITY_GAP_PERCENT"
)


availability.to_csv(
    AVAILABILITY_OUTPUT,
    index=False
)


print(
    availability
    .head(30)
    .to_string(index=False)
)


print()

print(
    f"Saved: {AVAILABILITY_OUTPUT}"
)


# ============================================================
# 7. STATE-SPECIFIC ANALYSIS
# ============================================================

section("7. STATE-SPECIFIC FEATURE ANALYSIS")


if "STATE_NAME" not in analysis.columns:

    print(
        "ERROR: STATE_NAME not found."
    )

    raise SystemExit(1)


state_counts = (
    analysis
    .groupby("STATE_NAME")
    .size()
    .sort_values(
        ascending=False
    )
)


major_states = state_counts[
    state_counts >= MIN_STATE_WORKS
].index.tolist()


print(
    f"States with >= "
    f"{MIN_STATE_WORKS} works: "
    f"{len(major_states)}"
)


state_rows = []


for state in major_states:

    state_df = analysis[
        analysis["STATE_NAME"] == state
    ]


    state_anomaly_mask = (
        state_df["IS_ML_ANOMALY"]
    )


    anomaly_count = int(
        state_anomaly_mask.sum()
    )


    normal_count = int(
        (~state_anomaly_mask).sum()
    )


    if anomaly_count < 5:
        continue


    for feature in numeric_features:

        values = pd.to_numeric(
            state_df[feature],
            errors="coerce"
        )


        anomaly_values = values[
            state_anomaly_mask
        ].dropna()

        normal_values = values[
            ~state_anomaly_mask
        ].dropna()


        if len(anomaly_values) < 5:
            continue

        if len(normal_values) < 20:
            continue


        anomaly_median = (
            anomaly_values.median()
        )

        normal_median = (
            normal_values.median()
        )


        normal_std = (
            normal_values.std()
        )


        if (
            pd.notna(normal_std)
            and normal_std > 1e-12
        ):

            standardized_difference = (
                anomaly_median
                - normal_median
            ) / normal_std

        else:

            standardized_difference = np.nan


        state_rows.append(
            {
                "STATE_NAME":
                    state,

                "TOTAL_WORKS":
                    len(state_df),

                "ML_ANOMALIES":
                    anomaly_count,

                "ML_ANOMALY_RATE_PERCENT":
                    anomaly_count
                    / len(state_df)
                    * 100,

                "FEATURE":
                    feature,

                "ANOMALY_MEDIAN":
                    anomaly_median,

                "NORMAL_MEDIAN":
                    normal_median,

                "NORMAL_STD":
                    normal_std,

                "STANDARDIZED_DIFFERENCE":
                    standardized_difference,
            }
        )


state_feature = pd.DataFrame(
    state_rows
)


if state_feature.empty:

    print(
        "No state-level feature comparisons "
        "could be calculated."
    )

else:

    state_feature[
        "ABS_STANDARDIZED_DIFFERENCE"
    ] = (
        state_feature[
            "STANDARDIZED_DIFFERENCE"
        ]
        .abs()
    )


    state_feature = (
        state_feature
        .sort_values(
            [
                "STATE_NAME",
                "ABS_STANDARDIZED_DIFFERENCE",
            ],
            ascending=[
                True,
                False,
            ]
        )
    )


    state_feature.to_csv(
        STATE_FEATURE_OUTPUT,
        index=False
    )


    print(
        f"Saved: {STATE_FEATURE_OUTPUT}"
    )


# ============================================================
# 8. PUNJAB
# ============================================================

section("8. PUNJAB FEATURE ANALYSIS")


if (
    not state_feature.empty
    and "Punjab" in major_states
):

    punjab = state_feature[
        state_feature["STATE_NAME"]
        == "Punjab"
    ]


    print(
        punjab[
            [
                "FEATURE",
                "ANOMALY_MEDIAN",
                "NORMAL_MEDIAN",
                "STANDARDIZED_DIFFERENCE",
            ]
        ]
        .head(30)
        .to_string(index=False)
    )

else:

    print(
        "Punjab does not have enough "
        "data for this analysis."
    )


# ============================================================
# 9. RAJASTHAN
# ============================================================

section("9. RAJASTHAN FEATURE ANALYSIS")


if (
    not state_feature.empty
    and "Rajasthan" in major_states
):

    rajasthan = state_feature[
        state_feature["STATE_NAME"]
        == "Rajasthan"
    ]


    print(
        rajasthan[
            [
                "FEATURE",
                "ANOMALY_MEDIAN",
                "NORMAL_MEDIAN",
                "STANDARDIZED_DIFFERENCE",
            ]
        ]
        .head(30)
        .to_string(index=False)
    )

else:

    print(
        "Rajasthan does not have enough "
        "data for this analysis."
    )


# ============================================================
# 10. TOP STATES BY ML ANOMALY RATE
# ============================================================

section("10. TOP STATES BY ML ANOMALY RATE")


state_summary = (
    analysis
    .groupby("STATE_NAME")
    .agg(
        TOTAL_WORKS=(
            "WORK_ID",
            "size"
        ),

        ML_ANOMALIES=(
            "IS_ML_ANOMALY",
            "sum"
        )
    )
    .reset_index()
)


state_summary[
    "ML_ANOMALY_RATE_PERCENT"
] = (
    state_summary["ML_ANOMALIES"]
    / state_summary["TOTAL_WORKS"]
    * 100
)


state_summary = state_summary.sort_values(
    "ML_ANOMALY_RATE_PERCENT",
    ascending=False
)


print(
    state_summary
    .head(20)
    .to_string(index=False)
)


# ============================================================
# 11. PEER GROUP ANALYSIS
# ============================================================

section("11. PEER GROUP ANALYSIS")


if "PEER_COUNT" in analysis.columns:

    peer_numeric = pd.to_numeric(
        analysis["PEER_COUNT"],
        errors="coerce"
    )


    analysis["_PEER_GROUP"] = np.select(
        [
            peer_numeric < 10,
            peer_numeric < 30,
            peer_numeric >= 30,
        ],
        [
            "0-9",
            "10-29",
            "30+",
        ],
        default="UNKNOWN"
    )


    peer_summary = (
        analysis
        .groupby("_PEER_GROUP")
        .agg(
            WORKS=(
                "WORK_ID",
                "size"
            ),

            ML_ANOMALIES=(
                "IS_ML_ANOMALY",
                "sum"
            )
        )
        .reset_index()
    )


    peer_summary[
        "ANOMALY_RATE_PERCENT"
    ] = (
        peer_summary["ML_ANOMALIES"]
        / peer_summary["WORKS"]
        * 100
    )


    print(
        peer_summary
        .to_string(index=False)
    )

else:

    print(
        "PEER_COUNT not found."
    )


# ============================================================
# 12. FINAL SUMMARY
# ============================================================

section("12. FINAL SUMMARY")


print(
    f"Total works             : "
    f"{len(analysis):,}"
)

print(
    f"ML anomalies            : "
    f"{ml_anomaly_count:,}"
)

print(
    f"ML anomaly rate         : "
    f"{ml_anomaly_count / len(analysis) * 100:.2f}%"
)

print(
    f"Numeric features tested : "
    f"{len(numeric_features):,}"
)

print()

print(
    "No ML model was changed."
)

print(
    "No anomaly labels were changed."
)

print(
    "This script only analyzes the existing "
    "ML detector output."
)

print()

print(
    "Diagnostic complete."
)