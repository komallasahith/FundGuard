import os
from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = BASE_DIR / "data" / "processed" / "mplads_features.csv"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "rule_anomalies.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}\n"
            "Run build_features.py first."
        )

    df = pd.read_csv(INPUT_FILE)

    print("=" * 70)
    print("RULE-BASED ANOMALY DETECTION")
    print("=" * 70)
    print(f"Input rows    : {len(df):,}")
    print(f"Input columns : {len(df.columns):,}")

    return df


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def col_exists(df, col):
    return col in df.columns


def numeric_series(df, col):
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce")
    return pd.Series(np.nan, index=df.index)


def bool_series(df, col):
    if col in df.columns:
        return df[col].fillna(False).astype(bool)
    return pd.Series(False, index=df.index)


# ============================================================
# RULE DETECTION
# ============================================================

def apply_rules(df):

    # --------------------------------------------------------
    # Initialize
    # --------------------------------------------------------

    df["RULE_SCORE"] = 0.0
    df["DATA_QUALITY_SCORE"] = 0.0

    reason_codes = [[] for _ in range(len(df))]
    reasons = [[] for _ in range(len(df))]

    def add_rule(mask, points, code, reason):
        """
        Add anomaly points and explanation to rows satisfying mask.
        """

        mask = mask.fillna(False)

        df.loc[mask, "RULE_SCORE"] += points

        indices = np.where(mask)[0]

        for i in indices:
            reason_codes[i].append(code)
            reasons[i].append(reason)

    # ========================================================
    # RULE 1 — ACTUAL AMOUNT > SANCTION AMOUNT
    # ========================================================

    actual = numeric_series(df, "ACTUAL_AMOUNT")
    sanction = numeric_series(df, "SANCTION_AMOUNT")

    mask = (
        actual.notna()
        & sanction.notna()
        & (actual > sanction)
    )

    add_rule(
        mask,
        30,
        "ACTUAL_GT_SANCTION",
        "Actual expenditure exceeds sanctioned amount"
    )

    # ========================================================
    # RULE 2 — DISBURSEMENT > SANCTION
    # ========================================================

    disbursement = numeric_series(df, "TOTAL_DISBURSED_AMOUNT")

    mask = (
        disbursement.notna()
        & sanction.notna()
        & (disbursement > sanction)
    )

    add_rule(
        mask,
        30,
        "DISBURSEMENT_GT_SANCTION",
        "Total disbursement exceeds sanctioned amount"
    )

    # ========================================================
    # RULE 3 — EXTREME COST VS PEER
    # ========================================================

    cost_ratio = numeric_series(
        df,
        "COST_VS_PEER_MEDIAN"
    )

    mask = (
        cost_ratio.notna()
        & (cost_ratio >= 5)
    )

    add_rule(
        mask,
        20,
        "EXTREME_PEER_COST",
        "Sanctioned cost is at least 5x the peer-group median"
    )

    # ========================================================
    # RULE 4 — HIGH COST VS PEER
    # ========================================================

    mask = (
        cost_ratio.notna()
        & (cost_ratio >= 2)
        & (cost_ratio < 5)
    )

    add_rule(
        mask,
        10,
        "HIGH_PEER_COST",
        "Sanctioned cost is at least 2x the peer-group median"
    )

    # ========================================================
    # RULE 5 — EXTREME PEER Z-SCORE
    # ========================================================

    zscore = numeric_series(
        df,
        "COST_VS_PEER_Z"
    )

    mask = (
        zscore.notna()
        & (zscore >= 5)
    )

    add_rule(
        mask,
        15,
        "EXTREME_COST_ZSCORE",
        "Cost is an extreme statistical outlier within the peer group"
    )

    # ========================================================
    # RULE 6 — HIGH PEER Z-SCORE
    # ========================================================

    mask = (
        zscore.notna()
        & (zscore >= 3)
        & (zscore < 5)
    )

    add_rule(
        mask,
        8,
        "HIGH_COST_ZSCORE",
        "Cost is a statistically significant outlier within the peer group"
    )

    # ========================================================
    # RULE 7 — MULTIPLE VENDORS
    # ========================================================

    vendor_count = numeric_series(
        df,
        "VENDOR_COUNT"
    )

    mask = (
        vendor_count.notna()
        & (vendor_count > 1)
    )

    add_rule(
        mask,
        6,
        "MULTIPLE_VENDORS",
        "Multiple vendors are associated with the work"
    )

    # ========================================================
    # RULE 8 — HIGH TRANSACTION COUNT
    # ========================================================

    transaction_count = numeric_series(
        df,
        "TRANSACTION_COUNT"
    )

    mask = (
        transaction_count.notna()
        & (transaction_count >= 4)
    )

    add_rule(
        mask,
        5,
        "HIGH_TRANSACTION_COUNT",
        "Work contains an unusually high number of expenditure transactions"
    )

    # ========================================================
    # RULE 9 — MULTIPLE TRANSACTIONS
    # ========================================================

    mask = (
        transaction_count.notna()
        & (transaction_count >= 2)
        & (transaction_count < 4)
    )

    add_rule(
        mask,
        2,
        "MULTIPLE_TRANSACTIONS",
        "Work contains multiple expenditure transactions"
    )

    # ========================================================
    # RULE 10 — SANCTIONED WITHOUT EXPENDITURE
    # ========================================================
    #
    # IMPORTANT:
    # This is NOT treated as fraud.
    # A sanctioned work can legitimately have no expenditure yet.
    #
    # Therefore only a small score is assigned.
    # ========================================================

    has_sanction = (
        sanction.notna()
        & (sanction > 0)
    )

    total_disb = numeric_series(
        df,
        "TOTAL_DISBURSED_AMOUNT"
    ).fillna(0)

    mask = (
        has_sanction
        & (total_disb == 0)
    )

    add_rule(
        mask,
        5,
        "SANCTIONED_NO_EXPENDITURE",
        "Work is sanctioned but no expenditure has been recorded"
    )

    # ========================================================
    # RULE 11 — SANCTIONED BUT NOT COMPLETED
    # ========================================================
    #
    # Contextual monitoring signal only.
    # ========================================================

    completed = bool_series(
        df,
        "IS_COMPLETED"
    )

    mask = (
        has_sanction
        & (~completed)
    )

    add_rule(
        mask,
        3,
        "SANCTIONED_NOT_COMPLETED",
        "Work is sanctioned but completion has not been recorded"
    )

    # ========================================================
    # RULE 12 — RECOMMENDED BUT NOT SANCTIONED
    # ========================================================
    #
    # This is mostly a lifecycle monitoring signal.
    # ========================================================

    recommended_amount = numeric_series(
        df,
        "RECOMMENDED_AMOUNT"
    )

    mask = (
        recommended_amount.notna()
        & (recommended_amount > 0)
        & sanction.isna()
    )

    add_rule(
        mask,
        2,
        "RECOMMENDED_NOT_SANCTIONED",
        "Work has a recommendation but no sanction amount is recorded"
    )

    # ========================================================
    # RULE 13 — CHRONOLOGY VIOLATION
    # ========================================================

    chronology_columns = [
        "INVALID_RECOMMENDATION_SANCTION_TIMELINE",
        "INVALID_SANCTION_COMPLETION_TIMELINE",
        "INVALID_RECOMMENDATION_COMPLETION_TIMELINE"
    ]

    chronology_mask = pd.Series(
        False,
        index=df.index
    )

    for col in chronology_columns:
        if col in df.columns:
            chronology_mask = (
                chronology_mask
                | bool_series(df, col)
            )

    add_rule(
        chronology_mask,
        15,
        "CHRONOLOGY_VIOLATION",
        "Work contains an invalid event chronology"
    )

    # ========================================================
    # DATA QUALITY SCORE
    # ========================================================
    #
    # Data quality is deliberately kept separate from
    # anomaly/fraud risk.
    # ========================================================

    missing_sanction = (
        sanction.isna()
        & recommended_amount.notna()
    )

    missing_date_columns = [
        "RECOMMENDATION_DATE",
        "SANCTION_DATE"
    ]

    for col in missing_date_columns:
        if col in df.columns:
            missing = df[col].isna()

            # Small data-quality penalty only
            df.loc[missing, "DATA_QUALITY_SCORE"] += 1

    df.loc[missing_sanction, "DATA_QUALITY_SCORE"] += 1

    # Cap data-quality score
    df["DATA_QUALITY_SCORE"] = (
        df["DATA_QUALITY_SCORE"]
        .clip(upper=10)
    )

    # ========================================================
    # CAP RULE SCORE
    # ========================================================

    df["RULE_SCORE"] = (
        df["RULE_SCORE"]
        .clip(lower=0, upper=100)
        .round(2)
    )

    # ========================================================
    # RISK LEVEL
    # ========================================================

    def risk_level(score):

        if score >= 70:
            return "CRITICAL"

        if score >= 40:
            return "HIGH"

        if score >= 20:
            return "MEDIUM"

        return "LOW"

    df["RULE_RISK_LEVEL"] = (
        df["RULE_SCORE"]
        .apply(risk_level)
    )

    # ========================================================
    # REASON CODES
    # ========================================================

    df["RULE_REASON_CODES"] = [
        "|".join(x) if x else ""
        for x in reason_codes
    ]

    df["RULE_REASONS"] = [
        " | ".join(x) if x else "No rule-based anomaly detected"
        for x in reasons
    ]

    # ========================================================
    # ANOMALY FLAG
    # ========================================================

    df["RULE_ANOMALY_FLAG"] = (
        df["RULE_SCORE"] >= 20
    )

    return df


# ============================================================
# SORTING
# ============================================================

def sort_results(df):

    return df.sort_values(
        by=[
            "RULE_SCORE",
            "DATA_QUALITY_SCORE"
        ],
        ascending=[
            False,
            False
        ]
    ).reset_index(drop=True)


# ============================================================
# SUMMARY
# ============================================================

def print_summary(df):

    print("\n" + "=" * 70)
    print("RULE DETECTION SUMMARY")
    print("=" * 70)

    total = len(df)

    anomaly_count = int(
        df["RULE_ANOMALY_FLAG"].sum()
    )

    print(f"Total works             : {total:,}")
    print(f"Rule anomaly candidates : {anomaly_count:,}")

    print("\nRisk levels:")

    risk_counts = (
        df["RULE_RISK_LEVEL"]
        .value_counts()
        .reindex(
            ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            fill_value=0
        )
    )

    for level, count in risk_counts.items():

        percentage = (
            count / total * 100
            if total > 0
            else 0
        )

        print(
            f"  {level:<10}: "
            f"{count:>5,} "
            f"({percentage:.2f}%)"
        )

    print("\nRule trigger counts:")

    rule_columns = [
        "ACTUAL_GT_SANCTION",
        "DISBURSEMENT_GT_SANCTION",
        "EXTREME_PEER_COST",
        "HIGH_PEER_COST",
        "EXTREME_COST_ZSCORE",
        "HIGH_COST_ZSCORE",
        "MULTIPLE_VENDORS",
        "HIGH_TRANSACTION_COUNT",
        "MULTIPLE_TRANSACTIONS",
        "SANCTIONED_NO_EXPENDITURE",
        "SANCTIONED_NOT_COMPLETED",
        "RECOMMENDED_NOT_SANCTIONED",
        "CHRONOLOGY_VIOLATION"
    ]

    codes = df["RULE_REASON_CODES"].fillna("")

    for code in rule_columns:

        count = codes.str.contains(
            code,
            regex=False
        ).sum()

        if count > 0:
            print(
                f"  {code:<35}: {count:,}"
            )

    # --------------------------------------------------------
    # Top anomalies
    # --------------------------------------------------------

    print("\nTop 20 rule-based anomaly candidates:")
    print("-" * 70)

    display_columns = [
        "WORK_RECOMMENDATION_DTL_ID",
        "MP_NAME",
        "CONSTITUENCY_NAME",
        "WORK_CATEGORY",
        "SANCTION_AMOUNT",
        "ACTUAL_AMOUNT",
        "TOTAL_DISBURSED_AMOUNT",
        "COST_VS_PEER_MEDIAN",
        "COST_VS_PEER_Z",
        "RULE_SCORE",
        "RULE_RISK_LEVEL",
        "RULE_REASON_CODES"
    ]

    display_columns = [
        c for c in display_columns
        if c in df.columns
    ]

    print(
        df[
            display_columns
        ].head(20).to_string(index=False)
    )


# ============================================================
# SAVE
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
        f"Saved rule results to:\n"
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

    df = load_data()

    df = apply_rules(df)

    df = sort_results(df)

    print_summary(df)

    save_results(df)

    print("\nRule detection completed successfully.")


if __name__ == "__main__":
    main()