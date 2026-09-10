import os
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler


warnings.filterwarnings("ignore")


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = "data/processed/mplads_features.csv"

OUTPUT_DIR = "data/outputs"
MODEL_DIR = "models"

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "isolation_forest_anomalies.csv"
)

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "isolation_forest.pkl"
)

IMPUTER_FILE = os.path.join(
    MODEL_DIR,
    "isolation_forest_imputer.pkl"
)

SCALER_FILE = os.path.join(
    MODEL_DIR,
    "isolation_forest_scaler.pkl"
)


# ============================================================
# MODEL CONFIG
# ============================================================

RANDOM_STATE = 42

# Fraction of observations expected to be anomalous.
# This does NOT mean fraud percentage.
CONTAMINATION = 0.02

N_ESTIMATORS = 300

# Maximum features used by each tree
MAX_FEATURES = 0.8


# ============================================================
# FEATURES
# ============================================================

# These are deliberately selected features.
#
# We DO NOT use:
# - RULE_SCORE
# - STATISTICAL_SCORE
# - RULE_RISK_LEVEL
# - STATISTICAL_RISK_LEVEL
#
# because those would make the ML model dependent on the
# previous detection layers.
#
# We also avoid IDs and text columns.

FEATURE_COLUMNS = [

    # --------------------------------------------------------
    # Financial
    # --------------------------------------------------------

    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",

    "TOTAL_DISBURSED_AMOUNT",
    "DISBURSEMENT_COUNT",

    "ACTUAL_TO_SANCTION_RATIO",
    "DISBURSEMENT_TO_SANCTION_RATIO",

    # --------------------------------------------------------
    # Peer benchmarking
    # --------------------------------------------------------

    "COST_VS_PEER_MEDIAN",
    "COST_VS_PEER_MEAN",
    "COST_VS_PEER_STD",
    "COST_VS_PEER_Z",

    # --------------------------------------------------------
    # Timeline
    # --------------------------------------------------------

    "DAYS_RECOMMENDATION_TO_SANCTION",
    "DAYS_SANCTION_TO_COMPLETION",
    "DAYS_RECOMMENDATION_TO_COMPLETION",

    # --------------------------------------------------------
    # Transactions
    # --------------------------------------------------------

    "TRANSACTION_COUNT",
    "VENDOR_COUNT",

    "AVG_TRANSACTION_AMOUNT",
    "MAX_TRANSACTION_AMOUNT",
    "MIN_TRANSACTION_AMOUNT",

    # --------------------------------------------------------
    # Financial behavior
    # --------------------------------------------------------

    "TRANSACTION_AMOUNT_STD",
    "TRANSACTION_AMOUNT_CV",

    # --------------------------------------------------------
    # Log-transformed financial features
    # --------------------------------------------------------

    "LOG_SANCTION_AMOUNT",
    "LOG_ACTUAL_AMOUNT",
    "LOG_DISBURSED_AMOUNT",

    # --------------------------------------------------------
    # Data completeness
    # --------------------------------------------------------

    "DATA_COMPLETENESS_SCORE"
]


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"\nInput file not found:\n{INPUT_FILE}\n\n"
            "Run build_features.py first."
        )

    df = pd.read_csv(INPUT_FILE)

    print("=" * 70)
    print("ISOLATION FOREST ANOMALY DETECTION")
    print("=" * 70)

    print(f"Input rows    : {len(df):,}")
    print(f"Input columns : {len(df.columns):,}")

    return df


# ============================================================
# CHECK FEATURES
# ============================================================

def check_features(df):

    print("\nChecking ML features...")

    available = []
    missing = []

    for column in FEATURE_COLUMNS:

        if column in df.columns:
            available.append(column)
        else:
            missing.append(column)

    print(
        f"Available features : {len(available)}"
    )

    if missing:

        print("\nMissing features:")

        for column in missing:
            print(f"  - {column}")

        print(
            "\nMissing features will be skipped."
        )

    if len(available) < 5:

        raise ValueError(
            "Too few usable ML features."
        )

    return available


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_features(df, feature_columns):

    X = df[feature_columns].copy()

    # --------------------------------------------------------
    # Convert everything to numeric
    # --------------------------------------------------------

    for column in feature_columns:

        X[column] = pd.to_numeric(
            X[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Replace infinite values
    # --------------------------------------------------------

    X = X.replace(
        [np.inf, -np.inf],
        np.nan
    )

    # --------------------------------------------------------
    # Statistics before imputation
    # --------------------------------------------------------

    missing_count = int(
        X.isna().sum().sum()
    )

    print(
        f"Missing feature values : "
        f"{missing_count:,}"
    )

    # --------------------------------------------------------
    # Median imputation
    # --------------------------------------------------------
    #
    # Median is robust to extreme values.
    #
    # Important:
    # Missing values are NOT automatically considered fraud.
    # --------------------------------------------------------

    imputer = SimpleImputer(
        strategy="median"
    )

    X_imputed = imputer.fit_transform(X)

    # --------------------------------------------------------
    # Robust scaling
    # --------------------------------------------------------
    #
    # Financial values can differ enormously in magnitude.
    # RobustScaler uses median/IQR and is less affected by
    # extreme observations.
    # --------------------------------------------------------

    scaler = RobustScaler()

    X_scaled = scaler.fit_transform(
        X_imputed
    )

    return (
        X_scaled,
        imputer,
        scaler
    )


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model(X):

    print("\nTraining Isolation Forest...")

    print(
        f"Estimators       : {N_ESTIMATORS}"
    )

    print(
        f"Contamination    : {CONTAMINATION}"
    )

    print(
        f"Max features     : {MAX_FEATURES}"
    )

    model = IsolationForest(

        n_estimators=N_ESTIMATORS,

        contamination=CONTAMINATION,

        max_features=MAX_FEATURES,

        random_state=RANDOM_STATE,

        n_jobs=-1
    )

    model.fit(X)

    print(
        "Isolation Forest training completed."
    )

    return model


# ============================================================
# GENERATE ANOMALY SCORES
# ============================================================

def generate_scores(df, model, X):

    # --------------------------------------------------------
    # Raw predictions
    #
    #  1  = normal
    # -1  = anomaly
    # --------------------------------------------------------

    predictions = model.predict(X)

    # --------------------------------------------------------
    # decision_function
    #
    # Higher = more normal
    # Lower  = more anomalous
    # --------------------------------------------------------

    decision_scores = model.decision_function(X)

    # --------------------------------------------------------
    # Convert to anomaly strength
    #
    # Lower decision score = stronger anomaly.
    #
    # We reverse it and normalize it to 0-100.
    # --------------------------------------------------------

    anomaly_strength = -decision_scores

    min_score = anomaly_strength.min()
    max_score = anomaly_strength.max()

    if max_score > min_score:

        normalized_score = (
            (anomaly_strength - min_score)
            / (max_score - min_score)
        ) * 100

    else:

        normalized_score = np.zeros(
            len(df)
        )

    normalized_score = np.clip(
        normalized_score,
        0,
        100
    )

    # --------------------------------------------------------
    # Store results
    # --------------------------------------------------------

    df["ISOLATION_FOREST_PREDICTION"] = (
        predictions
    )

    df["ISOLATION_FOREST_DECISION_SCORE"] = (
        decision_scores.round(6)
    )

    df["ISOLATION_FOREST_SCORE"] = (
        normalized_score.round(2)
    )

    df["ISOLATION_FOREST_ANOMALY_FLAG"] = (
        predictions == -1
    )

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------

    def risk_level(score):

        if score >= 80:
            return "CRITICAL"

        if score >= 60:
            return "HIGH"

        if score >= 40:
            return "MEDIUM"

        return "LOW"

    df["ISOLATION_FOREST_RISK_LEVEL"] = (
        df["ISOLATION_FOREST_SCORE"]
        .apply(risk_level)
    )

    return df


# ============================================================
# ADD ML REASONS
# ============================================================

def add_ml_reasons(df):

    def reason(row):

        score = row[
            "ISOLATION_FOREST_SCORE"
        ]

        if score >= 80:

            return (
                "Isolation Forest identified the work "
                "as highly unusual compared with the "
                "overall feature distribution"
            )

        if score >= 60:

            return (
                "Isolation Forest identified the work "
                "as unusually different from typical "
                "works"
            )

        if score >= 40:

            return (
                "Isolation Forest identified moderate "
                "deviation from typical work patterns"
            )

        return (
            "No strong Isolation Forest anomaly detected"
        )

    df["ISOLATION_FOREST_REASON"] = (
        df.apply(
            reason,
            axis=1
        )
    )

    return df


# ============================================================
# SORT RESULTS
# ============================================================

def sort_results(df):

    return df.sort_values(
        by="ISOLATION_FOREST_SCORE",
        ascending=False
    ).reset_index(drop=True)


# ============================================================
# SUMMARY
# ============================================================

def print_summary(df):

    print("\n" + "=" * 70)
    print("ISOLATION FOREST SUMMARY")
    print("=" * 70)

    total = len(df)

    anomaly_count = int(
        df[
            "ISOLATION_FOREST_ANOMALY_FLAG"
        ].sum()
    )

    print(
        f"Total works              : {total:,}"
    )

    print(
        f"ML anomaly candidates    : "
        f"{anomaly_count:,}"
    )

    print(
        f"Detected percentage      : "
        f"{anomaly_count / total * 100:.2f}%"
    )

    # --------------------------------------------------------
    # Risk levels
    # --------------------------------------------------------

    print("\nML risk levels:")

    counts = (
        df[
            "ISOLATION_FOREST_RISK_LEVEL"
        ]
        .value_counts()
        .reindex(
            [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW"
            ],
            fill_value=0
        )
    )

    for level, count in counts.items():

        percentage = (
            count / total * 100
            if total
            else 0
        )

        print(
            f"  {level:<10}: "
            f"{count:>5,} "
            f"({percentage:.2f}%)"
        )

    # --------------------------------------------------------
    # Score statistics
    # --------------------------------------------------------

    print("\nScore statistics:")

    print(
        f"  Minimum : "
        f"{df['ISOLATION_FOREST_SCORE'].min():.2f}"
    )

    print(
        f"  Median  : "
        f"{df['ISOLATION_FOREST_SCORE'].median():.2f}"
    )

    print(
        f"  Mean    : "
        f"{df['ISOLATION_FOREST_SCORE'].mean():.2f}"
    )

    print(
        f"  Maximum : "
        f"{df['ISOLATION_FOREST_SCORE'].max():.2f}"
    )

    # --------------------------------------------------------
    # Top candidates
    # --------------------------------------------------------

    print(
        "\nTop 20 Isolation Forest anomaly candidates:"
    )

    print("-" * 70)

    columns = [

        "WORK_RECOMMENDATION_DTL_ID",

        "MP_NAME",

        "WORK_CATEGORY",

        "SANCTION_AMOUNT",

        "ACTUAL_AMOUNT",

        "TOTAL_DISBURSED_AMOUNT",

        "COST_VS_PEER_MEDIAN",

        "COST_VS_PEER_Z",

        "ISOLATION_FOREST_SCORE",

        "ISOLATION_FOREST_RISK_LEVEL",

        "ISOLATION_FOREST_ANOMALY_FLAG"
    ]

    columns = [
        c for c in columns
        if c in df.columns
    ]

    print(
        df[
            columns
        ]
        .head(20)
        .to_string(index=False)
    )


# ============================================================
# SAVE MODEL
# ============================================================

def save_model(
    model,
    imputer,
    scaler
):

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    joblib.dump(
        model,
        MODEL_FILE
    )

    joblib.dump(
        imputer,
        IMPUTER_FILE
    )

    joblib.dump(
        scaler,
        SCALER_FILE
    )

    print("\n" + "=" * 70)
    print("MODEL FILES")
    print("=" * 70)

    print(
        f"Model   : {MODEL_FILE}"
    )

    print(
        f"Imputer : {IMPUTER_FILE}"
    )

    print(
        f"Scaler  : {SCALER_FILE}"
    )


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(df):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 70)
    print("OUTPUT")
    print("=" * 70)

    print(
        f"Saved results to:\n"
        f"{OUTPUT_FILE}"
    )

    print(
        f"Rows    : {len(df):,}"
    )

    print(
        f"Columns : {len(df.columns):,}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # 1. Load
    # --------------------------------------------------------

    df = load_data()

    # --------------------------------------------------------
    # 2. Check features
    # --------------------------------------------------------

    feature_columns = check_features(
        df
    )

    print("\nFeatures used by Isolation Forest:")

    for column in feature_columns:
        print(f"  - {column}")

    # --------------------------------------------------------
    # 3. Prepare
    # --------------------------------------------------------

    (
        X,
        imputer,
        scaler
    ) = prepare_features(
        df,
        feature_columns
    )

    print(
        f"\nML matrix shape : {X.shape}"
    )

    # --------------------------------------------------------
    # 4. Train
    # --------------------------------------------------------

    model = train_model(X)

    # --------------------------------------------------------
    # 5. Score
    # --------------------------------------------------------

    df = generate_scores(
        df,
        model,
        X
    )

    # --------------------------------------------------------
    # 6. Reasons
    # --------------------------------------------------------

    df = add_ml_reasons(
        df
    )

    # --------------------------------------------------------
    # 7. Sort
    # --------------------------------------------------------

    df = sort_results(
        df
    )

    # --------------------------------------------------------
    # 8. Summary
    # --------------------------------------------------------

    print_summary(
        df
    )

    # --------------------------------------------------------
    # 9. Save model
    # --------------------------------------------------------

    save_model(
        model,
        imputer,
        scaler
    )

    # --------------------------------------------------------
    # 10. Save results
    # --------------------------------------------------------

    save_results(
        df
    )

    print(
        "\nIsolation Forest detection completed successfully."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()