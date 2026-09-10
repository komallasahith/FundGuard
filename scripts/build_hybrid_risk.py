import os
import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

RULE_FILE = "data/outputs/rule_anomalies.csv"
STAT_FILE = "data/outputs/statistical_anomalies.csv"
ML_FILE = "data/outputs/isolation_forest_anomalies.csv"

OUTPUT_DIR = "data/outputs"
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "fundguard_risk_results.csv"
)


# ============================================================
# WEIGHTS
# ============================================================

RULE_WEIGHT = 0.35
STAT_WEIGHT = 0.35
ML_WEIGHT = 0.30


# ============================================================
# LOAD
# ============================================================

def load_results():

    for file in [RULE_FILE, STAT_FILE, ML_FILE]:

        if not os.path.exists(file):
            raise FileNotFoundError(
                f"\nRequired file not found:\n{file}\n\n"
                "Run all three detection stages first."
            )

    print("=" * 70)
    print("FUNDGUARD HYBRID RISK ENGINE")
    print("=" * 70)

    rule_df = pd.read_csv(RULE_FILE)
    stat_df = pd.read_csv(STAT_FILE)
    ml_df = pd.read_csv(ML_FILE)

    print(f"Rule rows        : {len(rule_df):,}")
    print(f"Statistical rows : {len(stat_df):,}")
    print(f"ML rows          : {len(ml_df):,}")

    return rule_df, stat_df, ml_df


# ============================================================
# VALIDATE KEY
# ============================================================

def validate_key(df, name):

    key = "WORK_RECOMMENDATION_DTL_ID"

    if key not in df.columns:

        raise ValueError(
            f"{key} not found in {name}"
        )

    duplicate_count = df[key].duplicated().sum()

    if duplicate_count > 0:

        raise ValueError(
            f"{name} contains "
            f"{duplicate_count:,} duplicate work IDs."
        )


# ============================================================
# MERGE DETECTORS
# ============================================================

def merge_results(rule_df, stat_df, ml_df):

    validate_key(
        rule_df,
        "rule results"
    )

    validate_key(
        stat_df,
        "statistical results"
    )

    validate_key(
        ml_df,
        "Isolation Forest results"
    )

    key = "WORK_RECOMMENDATION_DTL_ID"

    # --------------------------------------------------------
    # Select only required detector columns
    # --------------------------------------------------------

    rule_columns = [
        key,
        "RULE_SCORE",
        "RULE_RISK_LEVEL",
        "RULE_ANOMALY_FLAG",
        "RULE_REASON_CODES",
        "RULE_REASONS",
        "DATA_QUALITY_SCORE"
    ]

    stat_columns = [
        key,
        "STATISTICAL_SCORE",
        "STATISTICAL_RISK_LEVEL",
        "STATISTICAL_ANOMALY_FLAG",
        "STATISTICAL_REASON_CODES",
        "STATISTICAL_REASONS",
        "STATISTICAL_CONFIDENCE"
    ]

    ml_columns = [
        key,
        "ISOLATION_FOREST_SCORE",
        "ISOLATION_FOREST_RISK_LEVEL",
        "ISOLATION_FOREST_ANOMALY_FLAG",
        "ISOLATION_FOREST_REASON"
    ]

    rule_columns = [
        c for c in rule_columns
        if c in rule_df.columns
    ]

    stat_columns = [
        c for c in stat_columns
        if c in stat_df.columns
    ]

    ml_columns = [
        c for c in ml_columns
        if c in ml_df.columns
    ]

    rule = rule_df[rule_columns].copy()
    stat = stat_df[stat_columns].copy()
    ml = ml_df[ml_columns].copy()

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    df = rule.merge(
        stat,
        on=key,
        how="left"
    )

    df = df.merge(
        ml,
        on=key,
        how="left"
    )

    print(
        f"\nMerged works : {len(df):,}"
    )

    return df


# ============================================================
# CALCULATE HYBRID SCORE
# ============================================================

def calculate_hybrid_score(df):

    # --------------------------------------------------------
    # Fill missing detector scores
    # --------------------------------------------------------

    rule_score = pd.to_numeric(
        df["RULE_SCORE"],
        errors="coerce"
    ).fillna(0)

    stat_score = pd.to_numeric(
        df["STATISTICAL_SCORE"],
        errors="coerce"
    ).fillna(0)

    ml_score = pd.to_numeric(
        df["ISOLATION_FOREST_SCORE"],
        errors="coerce"
    ).fillna(0)

    # --------------------------------------------------------
    # Weighted score
    # --------------------------------------------------------

    df["RULE_CONTRIBUTION"] = (
        rule_score * RULE_WEIGHT
    )

    df["STATISTICAL_CONTRIBUTION"] = (
        stat_score * STAT_WEIGHT
    )

    df["ML_CONTRIBUTION"] = (
        ml_score * ML_WEIGHT
    )

    df["HYBRID_RISK_SCORE"] = (
        df["RULE_CONTRIBUTION"]
        + df["STATISTICAL_CONTRIBUTION"]
        + df["ML_CONTRIBUTION"]
    ).clip(
        0,
        100
    ).round(2)

    return df


# ============================================================
# DETECTOR AGREEMENT
# ============================================================

def calculate_agreement(df):

    rule_flag = (
        df["RULE_ANOMALY_FLAG"]
        .fillna(False)
        .astype(bool)
    )

    stat_flag = (
        df["STATISTICAL_ANOMALY_FLAG"]
        .fillna(False)
        .astype(bool)
    )

    ml_flag = (
        df["ISOLATION_FOREST_ANOMALY_FLAG"]
        .fillna(False)
        .astype(bool)
    )

    df["DETECTOR_AGREEMENT_COUNT"] = (
        rule_flag.astype(int)
        + stat_flag.astype(int)
        + ml_flag.astype(int)
    )

    def agreement_label(count):

        if count == 3:
            return "STRONG"

        if count == 2:
            return "MODERATE"

        if count == 1:
            return "SINGLE_DETECTOR"

        return "NONE"

    df["DETECTOR_AGREEMENT"] = (
        df["DETECTOR_AGREEMENT_COUNT"]
        .apply(agreement_label)
    )

    return df


# ============================================================
# FINAL RISK LEVEL
# ============================================================

def calculate_risk_level(df):

    def risk_level(row):

        score = row["HYBRID_RISK_SCORE"]
        agreement = row["DETECTOR_AGREEMENT_COUNT"]

        # ----------------------------------------------------
        # Critical
        #
        # Require both a high score and strong evidence.
        # ----------------------------------------------------

        if score >= 70 and agreement >= 2:
            return "CRITICAL"

        # ----------------------------------------------------
        # High
        # ----------------------------------------------------

        if score >= 50 and agreement >= 2:
            return "HIGH"

        if score >= 65 and agreement >= 1:
            return "HIGH"

        # ----------------------------------------------------
        # Medium
        # ----------------------------------------------------

        if score >= 30:
            return "MEDIUM"

        if score >= 20 and agreement >= 2:
            return "MEDIUM"

        # ----------------------------------------------------
        # Low
        # ----------------------------------------------------

        return "LOW"

    df["FINAL_RISK_LEVEL"] = (
        df.apply(
            risk_level,
            axis=1
        )
    )

    return df


# ============================================================
# BUILD EVIDENCE
# ============================================================

def build_evidence(df):

    evidence = []

    for _, row in df.iterrows():

        items = []

        # ----------------------------------------------------
        # Rule evidence
        # ----------------------------------------------------

        rule_reasons = str(
            row.get(
                "RULE_REASONS",
                ""
            )
        )

        if (
            rule_reasons
            and rule_reasons != "nan"
            and rule_reasons !=
            "No rule-based anomaly detected"
        ):

            items.append(
                "RULE: " + rule_reasons
            )

        # ----------------------------------------------------
        # Statistical evidence
        # ----------------------------------------------------

        stat_reasons = str(
            row.get(
                "STATISTICAL_REASONS",
                ""
            )
        )

        if (
            stat_reasons
            and stat_reasons != "nan"
            and stat_reasons !=
            "No statistical anomaly detected"
        ):

            items.append(
                "STATISTICAL: " + stat_reasons
            )

        # ----------------------------------------------------
        # ML evidence
        # ----------------------------------------------------

        ml_reason = str(
            row.get(
                "ISOLATION_FOREST_REASON",
                ""
            )
        )

        if (
            ml_reason
            and ml_reason != "nan"
            and ml_reason !=
            "No strong Isolation Forest anomaly detected"
            and ml_reason !=
            "No strong Isolation Forest anomaly detected"
        ):

            items.append(
                "ML: " + ml_reason
            )

        # ----------------------------------------------------
        # Agreement
        # ----------------------------------------------------

        agreement = row.get(
            "DETECTOR_AGREEMENT",
            "NONE"
        )

        if agreement == "STRONG":

            items.append(
                "All three detection layers identify "
                "unusual behavior"
            )

        elif agreement == "MODERATE":

            items.append(
                "Two independent detection layers "
                "identify unusual behavior"
            )

        elif agreement == "SINGLE_DETECTOR":

            items.append(
                "Only one detection layer identifies "
                "unusual behavior"
            )

        if not items:

            items.append(
                "No significant anomaly evidence detected"
            )

        evidence.append(
            " | ".join(items)
        )

    df["EVIDENCE_SUMMARY"] = evidence

    return df


# ============================================================
# INVESTIGATION PRIORITY
# ============================================================

def calculate_priority(df):

    def priority(row):

        level = row["FINAL_RISK_LEVEL"]
        agreement = row["DETECTOR_AGREEMENT_COUNT"]

        if level == "CRITICAL":
            return 1

        if level == "HIGH":
            return 2

        if level == "MEDIUM":
            return 3

        if agreement >= 2:
            return 4

        return 5

    df["INVESTIGATION_PRIORITY"] = (
        df.apply(
            priority,
            axis=1
        )
    )

    return df


# ============================================================
# SUMMARY
# ============================================================

def print_summary(df):

    print("\n" + "=" * 70)
    print("HYBRID RISK SUMMARY")
    print("=" * 70)

    total = len(df)

    # --------------------------------------------------------
    # Risk levels
    # --------------------------------------------------------

    print("\nFinal risk levels:")

    counts = (
        df["FINAL_RISK_LEVEL"]
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
    # Agreement
    # --------------------------------------------------------

    print("\nDetector agreement:")

    agreement_counts = (
        df["DETECTOR_AGREEMENT"]
        .value_counts()
        .reindex(
            [
                "STRONG",
                "MODERATE",
                "SINGLE_DETECTOR",
                "NONE"
            ],
            fill_value=0
        )
    )

    for level, count in agreement_counts.items():

        print(
            f"  {level:<16}: "
            f"{count:>5,}"
        )

    # --------------------------------------------------------
    # Score statistics
    # --------------------------------------------------------

    print("\nHybrid score statistics:")

    print(
        f"  Minimum : "
        f"{df['HYBRID_RISK_SCORE'].min():.2f}"
    )

    print(
        f"  Median  : "
        f"{df['HYBRID_RISK_SCORE'].median():.2f}"
    )

    print(
        f"  Mean    : "
        f"{df['HYBRID_RISK_SCORE'].mean():.2f}"
    )

    print(
        f"  Maximum : "
        f"{df['HYBRID_RISK_SCORE'].max():.2f}"
    )

    # --------------------------------------------------------
    # Top candidates
    # --------------------------------------------------------

    print(
        "\nTop 25 FundGuard risk candidates:"
    )

    print("-" * 70)

    columns = [

        "WORK_RECOMMENDATION_DTL_ID",

        "MP_NAME",

        "RULE_SCORE",

        "STATISTICAL_SCORE",

        "ISOLATION_FOREST_SCORE",

        "HYBRID_RISK_SCORE",

        "DETECTOR_AGREEMENT",

        "FINAL_RISK_LEVEL",

        "INVESTIGATION_PRIORITY",

        "RULE_REASON_CODES",

        "STATISTICAL_REASON_CODES"
    ]

    columns = [
        c for c in columns
        if c in df.columns
    ]

    print(
        df[
            columns
        ]
        .head(25)
        .to_string(index=False)
    )


# ============================================================
# SAVE
# ============================================================

def save_results(df):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Put important columns first
    # --------------------------------------------------------

    first_columns = [

        "WORK_RECOMMENDATION_DTL_ID",

        "MP_NAME",

        "RULE_SCORE",

        "STATISTICAL_SCORE",

        "ISOLATION_FOREST_SCORE",

        "RULE_CONTRIBUTION",

        "STATISTICAL_CONTRIBUTION",

        "ML_CONTRIBUTION",

        "HYBRID_RISK_SCORE",

        "DETECTOR_AGREEMENT_COUNT",

        "DETECTOR_AGREEMENT",

        "FINAL_RISK_LEVEL",

        "INVESTIGATION_PRIORITY",

        "EVIDENCE_SUMMARY"
    ]

    first_columns = [
        c for c in first_columns
        if c in df.columns
    ]

    remaining = [
        c for c in df.columns
        if c not in first_columns
    ]

    df = df[
        first_columns + remaining
    ]

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 70)
    print("HYBRID OUTPUT")
    print("=" * 70)

    print(
        f"Saved to:\n{OUTPUT_FILE}"
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

    (
        rule_df,
        stat_df,
        ml_df
    ) = load_results()

    # --------------------------------------------------------
    # 2. Merge
    # --------------------------------------------------------

    df = merge_results(
        rule_df,
        stat_df,
        ml_df
    )

    # --------------------------------------------------------
    # 3. Hybrid score
    # --------------------------------------------------------

    df = calculate_hybrid_score(
        df
    )

    # --------------------------------------------------------
    # 4. Detector agreement
    # --------------------------------------------------------

    df = calculate_agreement(
        df
    )

    # --------------------------------------------------------
    # 5. Final risk level
    # --------------------------------------------------------

    df = calculate_risk_level(
        df
    )

    # --------------------------------------------------------
    # 6. Evidence
    # --------------------------------------------------------

    df = build_evidence(
        df
    )

    # --------------------------------------------------------
    # 7. Investigation priority
    # --------------------------------------------------------

    df = calculate_priority(
        df
    )

    # --------------------------------------------------------
    # 8. Sort
    # --------------------------------------------------------

    df = df.sort_values(
        by=[
            "INVESTIGATION_PRIORITY",
            "HYBRID_RISK_SCORE"
        ],
        ascending=[
            True,
            False
        ]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # 9. Summary
    # --------------------------------------------------------

    print_summary(
        df
    )

    # --------------------------------------------------------
    # 10. Save
    # --------------------------------------------------------

    save_results(
        df
    )

    print(
        "\nFundGuard hybrid risk engine "
        "completed successfully."
    )


if __name__ == "__main__":
    main()