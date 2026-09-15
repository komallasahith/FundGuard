"""
FUNDGUARD — INDIA-WIDE ML ANOMALY DETECTOR
REVISED ISOLATION FOREST

Purpose
-------
Detect unusual MPLADS works using unsupervised machine learning.

Important
---------
This model identifies unusual/anomalous works for investigation.

It does NOT:
    - determine fraud
    - determine corruption
    - determine guilt
    - use rule detector scores
    - use statistical detector scores

The ML model is intentionally kept independent from the
Rule and Statistical detectors.

Pipeline
--------
98 engineered features
        ↓
ML feature filtering
        ↓
Peer-quality correction
        ↓
Median imputation
        ↓
Isolation Forest
        ↓
ML anomaly score
        ↓
ML percentile
        ↓
ML severity
"""

from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_features.csv"
)

OUTPUT_DIR = BASE_DIR / "data" / "outputs"

OUTPUT_FILE = (
    OUTPUT_DIR
    / "india_ml_anomalies.csv"
)

SUMMARY_FILE = (
    OUTPUT_DIR
    / "india_ml_summary.csv"
)

DISTRIBUTION_FILE = (
    OUTPUT_DIR
    / "india_ml_distribution.csv"
)


# ============================================================
# ISOLATION FOREST CONFIG
# ============================================================

# Use data-driven automatic contamination estimation based on empirical feature distribution
CONTAMINATION = "auto"

N_ESTIMATORS = 300

RANDOM_STATE = 42

MAX_SAMPLES = "auto"


# ============================================================
# PEER CONFIGURATION
# ============================================================

# Peer-relative statistics are only considered trustworthy
# when enough comparable works exist.
#
# This matches the statistical detector's minimum peer
# population principle.
MIN_PEER_SIZE = 10


# ============================================================
# IDENTIFIER / DETECTOR COLUMNS
# ============================================================

IDENTIFIER_COLUMNS = {
    "WORK_ID",
    "STATE_ID",
    "CONSTITUENCY_ID",
    "MP_ID",
}


# Never allow detector outputs into ML.
DETECTOR_PREFIXES = (
    "RULE_",
    "STAT_",
    "ML_",
    "IF_",
)


DETECTOR_COLUMNS = {
    "RULE_SCORE",
    "RULE_SEVERITY",
    "RULE_CANDIDATE",

    "STAT_SCORE",
    "STAT_SEVERITY",
    "STAT_CANDIDATE",

    "ML_SCORE",
    "ML_SEVERITY",
    "ML_ANOMALY",

    "IF_SCORE",
    "IF_RAW_SCORE",
    "IF_DECISION_SCORE",
}


# ============================================================
# ADMINISTRATIVE FEATURES TO EXCLUDE
# ============================================================

"""
These describe the size of the administrative population rather
than the individual work itself.

Examples:

    STATE_WORK_COUNT
    MP_WORK_COUNT
    CONSTITUENCY_WORK_COUNT
    STATE_TOTAL_RECOMMENDED
    MP_TOTAL_RECOMMENDED

The previous model showed a strong concentration toward large
works and certain states. These contextual size variables can
make that effect stronger.

We therefore exclude them from ML.
"""

ADMINISTRATIVE_EXACT = {
    "STATE_WORK_COUNT",
    "MP_WORK_COUNT",
    "CONSTITUENCY_WORK_COUNT",
    "CATEGORY_WORK_COUNT",
    "ACTIVITY_WORK_COUNT",
}


ADMINISTRATIVE_PREFIXES = (
    "STATE_TOTAL_",
    "MP_TOTAL_",
    "CONSTITUENCY_TOTAL_",
)


# ============================================================
# RULE-DERIVED / THRESHOLD FEATURES TO EXCLUDE
# ============================================================

"""
These are deliberately excluded because they are effectively
hand-crafted anomaly rules.

The Rule/Statistical detectors already evaluate them.

ML should learn patterns from the underlying continuous
measurements instead.
"""

RULE_DERIVED_COLUMNS = {
    "SANCTION_ABOVE_2X_PEER_MEDIAN",
    "SANCTION_ABOVE_5X_PEER_MEDIAN",

    "AVERAGE_PAYMENT_ABOVE_1M",
    "TOTAL_DISBURSED_ABOVE_5M",

    "PAYMENT_COUNT_GE_5",
    "PAYMENT_COUNT_GE_10",

    "VENDOR_COUNT_GE_5",
    "VENDOR_COUNT_GE_10",
}


# ============================================================
# LOW-INFORMATION / TIME ENCODING FEATURES
# ============================================================

"""
Calendar year/month values are not inherently bad, but Isolation
Forest can split on them in ways that identify a particular
collection period rather than unusual financial behavior.

We therefore exclude raw year/month fields from this version.
"""

TIME_ENCODING_COLUMNS = {
    "RECOMMENDATION_YEAR",
    "RECOMMENDATION_MONTH",
    "SANCTION_YEAR",
    "FIRST_PAYMENT_YEAR",
    "COMPLETION_YEAR",
}


# ============================================================
# PEER FEATURES
# ============================================================

"""
These features are potentially valuable but only when the work
has enough peers.

For PEER_COUNT < 10, we neutralize the peer-relative variables
instead of letting a self-comparison become an ML signal.

The original validation showed that many top anomalies had:

    PEER_COUNT = 1

which makes their peer median essentially the work's own value.
"""

PEER_RELATIVE_COLUMNS = {
    "PEER_MEDIAN_SANCTION",
    "PEER_MEAN_SANCTION",
    "PEER_STD_SANCTION",
    "PEER_MEDIAN_DISBURSED",
    "SANCTION_TO_PEER_MEDIAN",
    "SANCTION_PEER_Z_SCORE",
    "ABS_PEER_COST_Z_SCORE",
}


# ============================================================
# FEATURES THAT WE WANT TO KEEP
# ============================================================

"""
These are the main individual-work behavioral signals.

We use an explicit allowlist so that future additions to the
feature engineering file don't silently change the ML model.
"""

CORE_FEATURES = {
    # --------------------------------------------------------
    # Financial
    # --------------------------------------------------------

    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "TOTAL_FUND_DISBURSED_AMT",
    "ACTUAL_AMOUNT",

    "DISBURSED_TO_SANCTION_RATIO",
    "REMAINING_SANCTION_AMOUNT",

    "ACTUAL_TO_SANCTION_RATIO",
    "ACTUAL_TO_RECOMMENDED_RATIO",
    "ACTUAL_VS_DISBURSED_RATIO",

    "DISBURSED_TO_RECOMMENDED_RATIO",
    "REMAINING_SANCTION_RATIO",

    "ACTUAL_MINUS_SANCTION",
    "ACTUAL_MINUS_DISBURSED",
    "DISBURSED_MINUS_ACTUAL",

    # --------------------------------------------------------
    # Payment behavior
    # --------------------------------------------------------

    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",
    "UNIQUE_VENDOR_NAME_COUNT",

    "PAYMENT_SUCCESS_COUNT",
    "PAYMENT_IN_PROGRESS_COUNT",

    "PAYMENTS_PER_100_DAYS",
    "PAYMENTS_PER_30_DAYS",

    "AVERAGE_PAYMENT_AMOUNT",
    "PAYMENT_SUCCESS_RATIO",
    "PAYMENT_IN_PROGRESS_RATIO",

    "PAYMENTS_PER_VENDOR",

    # --------------------------------------------------------
    # Timeline
    # --------------------------------------------------------

    "EXPENDITURE_DURATION_DAYS",

    "RECOMMENDATION_TO_SANCTION_DAYS",
    "SANCTION_TO_FIRST_PAYMENT_DAYS",
    "RECOMMENDATION_TO_FIRST_PAYMENT_DAYS",

    "LAST_PAYMENT_TO_COMPLETION_DAYS",

    "RECOMMENDATION_TO_COMPLETION_DAYS",
    "SANCTION_TO_COMPLETION_DAYS",

    "COMPLETION_DURATION_DAYS",

    "DISBURSED_PER_EXPENDITURE_DAY",

    "PAYMENT_AFTER_REPORTED_COMPLETION_DAYS",

    # --------------------------------------------------------
    # Completion / availability
    # --------------------------------------------------------

    "IS_COMPLETED",
    "HAS_ACTUAL_AMOUNT",
    "HAS_ACTUAL_END_DATE",

    "NO_PAYMENT_RECORD",

    # Note: MULTIPLE_PAYMENTS and MULTIPLE_VENDORS removed to eliminate
    # multicollinearity with numerical PAYMENT_COUNT and UNIQUE_VENDOR_COUNT.

    # --------------------------------------------------------
    # Data quality
    # --------------------------------------------------------

    "MISSING_FIELD_COUNT",
    "DATA_COMPLETENESS_RATIO",

    "COMPLETION_BEFORE_LAST_PAYMENT",

    # --------------------------------------------------------
    # Payment/status indicators
    # --------------------------------------------------------

    "ATTACH_ID",
    "FLAG",

    # --------------------------------------------------------
    # Peer population size
    # --------------------------------------------------------

    "PEER_COUNT",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_header(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def is_detector_column(column):
    """
    Detect rule/statistical/ML outputs.
    """

    if column in DETECTOR_COLUMNS:
        return True

    upper = str(column).upper()

    return any(
        upper.startswith(prefix)
        for prefix in DETECTOR_PREFIXES
    )


def is_administrative_column(column):
    """
    Detect state/MP/constituency aggregate features.
    """

    if column in ADMINISTRATIVE_EXACT:
        return True

    return any(
        str(column).startswith(prefix)
        for prefix in ADMINISTRATIVE_PREFIXES
    )


# ============================================================
# LOAD FEATURES
# ============================================================

print_header(
    "FUNDGUARD INDIA-WIDE REVISED ML ANOMALY DETECTOR"
)

print(f"Input file: {INPUT_FILE}")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Feature file not found:\n{INPUT_FILE}"
    )


df = pd.read_csv(INPUT_FILE)

print(
    f"Rows loaded    : {len(df):,}"
)

print(
    f"Columns loaded : {len(df.columns):,}"
)


# ============================================================
# VALIDATE WORK ID
# ============================================================

print_header(
    "VALIDATING WORK IDENTIFIERS"
)

if "WORK_ID" not in df.columns:
    raise ValueError(
        "WORK_ID column is missing."
    )


missing_work_ids = int(
    df["WORK_ID"].isna().sum()
)

duplicate_work_ids = int(
    df["WORK_ID"].duplicated().sum()
)

unique_work_ids = int(
    df["WORK_ID"].nunique()
)

print(
    f"Missing WORK_ID   : {missing_work_ids:,}"
)

print(
    f"Duplicate WORK_ID : {duplicate_work_ids:,}"
)

print(
    f"Unique WORK_ID    : {unique_work_ids:,}"
)


if missing_work_ids > 0:
    raise ValueError(
        "WORK_ID contains missing values."
    )


if duplicate_work_ids > 0:
    raise ValueError(
        "WORK_ID is not unique."
    )


# ============================================================
# NUMERIC COLUMNS
# ============================================================

print_header(
    "ANALYZING NUMERIC FEATURES"
)

numeric_columns = (
    df
    .select_dtypes(
        include=[np.number]
    )
    .columns
    .tolist()
)

print(
    f"Numeric columns found : "
    f"{len(numeric_columns):,}"
)


# ============================================================
# FILTER FEATURES
# ============================================================

selected_features = []

excluded_detector = []

excluded_admin = []

excluded_rules = []

excluded_time = []

excluded_other = []


for column in numeric_columns:

    # --------------------------------------------------------
    # Identifier
    # --------------------------------------------------------

    if column in IDENTIFIER_COLUMNS:
        excluded_other.append(column)
        continue

    # --------------------------------------------------------
    # Detector output
    # --------------------------------------------------------

    if is_detector_column(column):
        excluded_detector.append(column)
        continue

    # --------------------------------------------------------
    # Administrative aggregate
    # --------------------------------------------------------

    if is_administrative_column(column):
        excluded_admin.append(column)
        continue

    # --------------------------------------------------------
    # Rule-derived threshold
    # --------------------------------------------------------

    if column in RULE_DERIVED_COLUMNS:
        excluded_rules.append(column)
        continue

    # --------------------------------------------------------
    # Calendar encoding
    # --------------------------------------------------------

    if column in TIME_ENCODING_COLUMNS:
        excluded_time.append(column)
        continue

    # --------------------------------------------------------
    # Explicit core feature
    # --------------------------------------------------------

    if column in CORE_FEATURES:
        selected_features.append(column)
        continue

    # --------------------------------------------------------
    # Unknown numeric feature
    # --------------------------------------------------------

    excluded_other.append(column)


print()
print(
    f"Detector outputs excluded       : "
    f"{len(excluded_detector):,}"
)

print(
    f"Administrative features excluded: "
    f"{len(excluded_admin):,}"
)

print(
    f"Rule-derived features excluded  : "
    f"{len(excluded_rules):,}"
)

print(
    f"Time encoding features excluded  : "
    f"{len(excluded_time):,}"
)

print(
    f"Other numeric features excluded : "
    f"{len(excluded_other):,}"
)

print(
    f"Selected ML features            : "
    f"{len(selected_features):,}"
)


if len(selected_features) == 0:
    raise ValueError(
        "No usable ML features were selected."
    )


# ============================================================
# REMOVE CONSTANT FEATURES
# ============================================================

print_header(
    "CHECKING FEATURE VARIANCE"
)

constant_features = []

near_constant_features = []


for column in selected_features:

    unique_count = (
        df[column]
        .nunique(dropna=True)
    )

    if unique_count <= 1:

        constant_features.append(
            column
        )

    elif unique_count <= 2:

        near_constant_features.append(
            column
        )


selected_features = [
    column
    for column in selected_features
    if column not in constant_features
]


print(
    f"Constant features removed : "
    f"{len(constant_features):,}"
)

print(
    f"Near-constant features    : "
    f"{len(near_constant_features):,}"
)

print(
    f"Final feature count       : "
    f"{len(selected_features):,}"
)


# ============================================================
# PEER QUALITY CORRECTION
# ============================================================

print_header(
    "APPLYING PEER QUALITY CONTROL"
)

"""
For works with insufficient peers, peer-relative statistics
are not trustworthy.

We create a copy of the selected feature matrix and replace
weak-peer values with NaN.

The later median imputer will then use the valid population
distribution instead of allowing PEER_COUNT=1 self-comparisons
to drive the model.
"""

X_raw = df[selected_features].copy()


if "PEER_COUNT" in df.columns:

    peer_count = pd.to_numeric(
        df["PEER_COUNT"],
        errors="coerce"
    )

    weak_peer_mask = (
        peer_count < MIN_PEER_SIZE
    )

    weak_peer_count = int(
        weak_peer_mask.sum()
    )

    print(
        f"Works with <{MIN_PEER_SIZE} peers : "
        f"{weak_peer_count:,}"
    )

    print(
        f"Works with >={MIN_PEER_SIZE} peers: "
        f"{len(df) - weak_peer_count:,}"
    )

    peer_features_present = [
        column
        for column in PEER_RELATIVE_COLUMNS
        if column in X_raw.columns
    ]

    print()
    print(
        "Peer-relative features controlled:"
    )

    for column in peer_features_present:
        print(f"  - {column}")

    # Replace weak-peer values with NaN.
    X_raw.loc[
        weak_peer_mask,
        peer_features_present
    ] = np.nan


# ============================================================
# MISSING VALUE ANALYSIS
# ============================================================

print_header(
    "MISSING VALUE ANALYSIS"
)

missing_before = int(
    X_raw.isna()
    .sum()
    .sum()
)

print(
    f"Missing feature values : "
    f"{missing_before:,}"
)


# ============================================================
# MEDIAN IMPUTATION
# ============================================================

print_header(
    "MEDIAN IMPUTATION"
)

"""
Median imputation:

- handles missing financial values
- is robust against extreme observations
- avoids arbitrary zero replacement
"""

imputer = SimpleImputer(
    strategy="median"
)

X = imputer.fit_transform(
    X_raw
)

print(
    f"Matrix shape : "
    f"{X.shape}"
)

if not np.isfinite(X).all():

    raise ValueError(
        "Non-finite values remain after imputation."
    )


# ============================================================
# TRAIN ISOLATION FOREST
# ============================================================

print_header(
    "TRAINING REVISED ISOLATION FOREST"
)

print(
    f"Training rows     : "
    f"{X.shape[0]:,}"
)

print(
    f"Training features : "
    f"{X.shape[1]:,}"
)

print(
    f"Contamination     : "
    f"{CONTAMINATION}"
)

print(
    f"Estimators        : "
    f"{N_ESTIMATORS}"
)

print(
    f"Random state      : "
    f"{RANDOM_STATE}"
)


model = IsolationForest(
    n_estimators=N_ESTIMATORS,
    contamination=CONTAMINATION,
    max_samples=MAX_SAMPLES,
    random_state=RANDOM_STATE,
    n_jobs=-1,
)


model.fit(X)

print()
print(
    "Isolation Forest training completed."
)


# ============================================================
# GENERATE SCORES
# ============================================================

print_header(
    "GENERATING ML ANOMALY SCORES"
)


"""
Isolation Forest:

predict():
    +1 = normal
    -1 = anomaly

score_samples():
    higher = more normal
    lower  = more abnormal

We invert the raw score so:

    higher ML_ANOMALY_STRENGTH
        =
    more unusual
"""


raw_score = model.score_samples(
    X
)

decision_score = model.decision_function(
    X
)

prediction = model.predict(
    X
)


anomaly_strength = -raw_score


# ============================================================
# PERCENTILE
# ============================================================

"""
Percentile makes the result easier to interpret.

Example:

    99.5
    means the work is more unusual than approximately
    99.5% of works according to this model.

It is NOT a probability of fraud.
"""

ml_percentile = (
    pd.Series(
        anomaly_strength
    )
    .rank(
        method="average",
        pct=True
    )
    .to_numpy()
    * 100
)


ml_anomaly = (
    prediction == -1
).astype(int)


# ============================================================
# SEVERITY
# ============================================================

"""
Severity is an ML-anomaly-strength label.

NONE:
    below 95th percentile

LOW:
    95th–97.5th

MEDIUM:
    97.5th–99th

HIGH:
    top 1%
"""

ml_severity = np.select(
    [
        ml_percentile >= 99,
        ml_percentile >= 97.5,
        ml_percentile >= 95,
    ],
    [
        "HIGH",
        "MEDIUM",
        "LOW",
    ],
    default="NONE"
)


# ============================================================
# BUILD OUTPUT
# ============================================================

print_header(
    "BUILDING ML OUTPUT"
)


context_columns = [
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
    "SOURCE_KEY",

    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "TOTAL_FUND_DISBURSED_AMT",

    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",
]


context_columns = [
    column
    for column in context_columns
    if column in df.columns
]


output_context = (
    df[context_columns]
    .reset_index(drop=True)
)


ml_results = pd.DataFrame({
    "IF_RAW_SCORE": raw_score,
    "IF_DECISION_SCORE": decision_score,
    "ML_ANOMALY_STRENGTH": anomaly_strength,
    "ML_PERCENTILE": ml_percentile,
    "ML_ANOMALY": ml_anomaly,
    "ML_SEVERITY": ml_severity,
})


output = pd.concat(
    [
        output_context,
        ml_results.reset_index(drop=True),
    ],
    axis=1
)


# ============================================================
# VALIDATION
# ============================================================

print_header(
    "VALIDATING ML OUTPUT"
)

output_rows = len(output)

output_unique_ids = (
    output["WORK_ID"]
    .nunique()
)

output_missing_ids = int(
    output["WORK_ID"]
    .isna()
    .sum()
)

output_duplicate_ids = int(
    output["WORK_ID"]
    .duplicated()
    .sum()
)

ml_candidate_count = int(
    output["ML_ANOMALY"]
    .sum()
)


print(
    f"Output rows           : "
    f"{output_rows:,}"
)

print(
    f"Output columns        : "
    f"{len(output.columns):,}"
)

print(
    f"Unique WORK_ID        : "
    f"{output_unique_ids:,}"
)

print(
    f"Missing WORK_ID       : "
    f"{output_missing_ids:,}"
)

print(
    f"Duplicate WORK_ID     : "
    f"{output_duplicate_ids:,}"
)

print(
    f"ML anomaly candidates : "
    f"{ml_candidate_count:,}"
)


if output_rows != len(df):
    raise ValueError(
        "Output row count changed."
    )


if output_unique_ids != output_rows:
    raise ValueError(
        "WORK_ID uniqueness was lost."
    )


if output_missing_ids > 0:
    raise ValueError(
        "Output contains missing WORK_ID."
    )


if output_duplicate_ids > 0:
    raise ValueError(
        "Output contains duplicate WORK_ID."
    )


# ============================================================
# SEVERITY DISTRIBUTION
# ============================================================

severity_distribution = (
    output["ML_SEVERITY"]
    .value_counts()
    .reindex(
        [
            "NONE",
            "LOW",
            "MEDIUM",
            "HIGH",
        ],
        fill_value=0
    )
    .rename_axis(
        "ML_SEVERITY"
    )
    .reset_index(
        name="WORK_COUNT"
    )
)


severity_distribution[
    "PERCENTAGE"
] = (
    severity_distribution["WORK_COUNT"]
    / len(output)
    * 100
)


# ============================================================
# STATE DISTRIBUTION
# ============================================================

if "STATE_NAME" in output.columns:

    state_distribution = (
        output[
            output["ML_ANOMALY"] == 1
        ]
        .groupby("STATE_NAME")
        .size()
        .sort_values(
            ascending=False
        )
        .rename(
            "ML_ANOMALIES"
        )
        .reset_index()
    )

else:

    state_distribution = pd.DataFrame()


# ============================================================
# ML DISTRIBUTION
# ============================================================

distribution = pd.DataFrame({
    "METRIC": [
        "TOTAL_WORKS",
        "ML_ANOMALIES",
        "ML_ANOMALY_PERCENTAGE",
        "HIGH",
        "MEDIUM",
        "LOW",
        "NONE",
        "FEATURE_COUNT",
        "CONTAMINATION",
        "N_ESTIMATORS",
        "MIN_PEER_SIZE",
    ],

    "VALUE": [
        len(output),

        int(
            output["ML_ANOMALY"]
            .sum()
        ),

        float(
            output["ML_ANOMALY"]
            .mean()
            * 100
        ),

        int(
            (
                output["ML_SEVERITY"]
                == "HIGH"
            ).sum()
        ),

        int(
            (
                output["ML_SEVERITY"]
                == "MEDIUM"
            ).sum()
        ),

        int(
            (
                output["ML_SEVERITY"]
                == "LOW"
            ).sum()
        ),

        int(
            (
                output["ML_SEVERITY"]
                == "NONE"
            ).sum()
        ),

        len(selected_features),

        CONTAMINATION,

        N_ESTIMATORS,

        MIN_PEER_SIZE,
    ],
})


# ============================================================
# TOP 20
# ============================================================

print_header(
    "TOP 20 REVISED ML ANOMALY CANDIDATES"
)


top_columns = [
    "WORK_ID",
    "STATE_NAME",
    "CONSTITUENCY",
    "MP_NAME",

    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",

    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",

    "ML_PERCENTILE",
    "ML_ANOMALY",
    "ML_SEVERITY",
]


top_columns = [
    column
    for column in top_columns
    if column in output.columns
]


top20 = (
    output
    .sort_values(
        "ML_ANOMALY_STRENGTH",
        ascending=False
    )
    .head(20)
)


print(
    top20[top_columns]
    .to_string(
        index=False
    )
)


# ============================================================
# SAVE
# ============================================================

print_header(
    "SAVING ML OUTPUTS"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


output.to_csv(
    OUTPUT_FILE,
    index=False
)


severity_distribution.to_csv(
    SUMMARY_FILE,
    index=False
)


distribution.to_csv(
    DISTRIBUTION_FILE,
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print_header(
    "REVISED ML DETECTOR COMPLETE"
)

print(
    f"Total works           : "
    f"{len(output):,}"
)

print(
    f"ML anomaly candidates : "
    f"{ml_candidate_count:,}"
)

print(
    f"Candidate percentage  : "
    f"{ml_candidate_count / len(output) * 100:.2f}%"
)

print()
print(
    "Works by severity:"
)

print(
    severity_distribution[
        [
            "ML_SEVERITY",
            "WORK_COUNT",
            "PERCENTAGE",
        ]
    ].to_string(
        index=False
    )
)

print()
print(
    "Feature count:"
)

print(
    f"  Final ML features : "
    f"{len(selected_features)}"
)

print()
print(
    "Output files:"
)

print(
    f"  {OUTPUT_FILE}"
)

print(
    f"  {SUMMARY_FILE}"
)

print(
    f"  {DISTRIBUTION_FILE}"
)

print()
print(
    "IMPORTANT:"
)

print(
    "ML anomalies are investigation candidates, "
    "not confirmed fraud."
)

print()
print(
    "The ML model was trained independently of "
    "the Rule and Statistical detector scores."
)