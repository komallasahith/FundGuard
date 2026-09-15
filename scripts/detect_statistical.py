import os
from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = BASE_DIR / "data" / "outputs" / "rule_anomalies.csv"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "statistical_anomalies.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}\n"
            "Run detect_rules.py first."
        )

    df = pd.read_csv(INPUT_FILE)

    print("=" * 70)
    print("STATISTICAL ANOMALY DETECTION")
    print("=" * 70)

    print(f"Input rows    : {len(df):,}")
    print(f"Input columns : {len(df.columns):,}")

    return df


# ============================================================
# HELPER
# ============================================================

def numeric(df, column):

    if column in df.columns:
        return pd.to_numeric(
            df[column],
            errors="coerce"
        )

    return pd.Series(
        np.nan,
        index=df.index
    )


# ============================================================
# STATISTICAL DETECTION
# ============================================================

def detect_statistical_anomalies(df):

    # --------------------------------------------------------
    # Initialize
    # --------------------------------------------------------

    df["STATISTICAL_SCORE"] = 0.0

    reason_codes = [
        []
        for _ in range(len(df))
    ]

    reasons = [
        []
        for _ in range(len(df))
    ]

    # --------------------------------------------------------
    # Helper to add points
    # --------------------------------------------------------

    def add_signal(
        mask,
        points,
        code,
        reason
    ):

        mask = mask.fillna(False)

        df.loc[
            mask,
            "STATISTICAL_SCORE"
        ] += points

        indices = np.where(mask)[0]

        for i in indices:

            reason_codes[i].append(code)

            reasons[i].append(reason)

    # ========================================================
    # SIGNAL 1
    # Peer cost ratio >= 2
    # ========================================================

    cost_ratio = numeric(
        df,
        "COST_VS_PEER_MEDIAN"
    )

    mask = (
        cost_ratio.notna()
        & (cost_ratio >= 2)
        & (cost_ratio < 5)
    )

    add_signal(
        mask,
        15,
        "PEER_RATIO_HIGH",
        "Sanctioned cost is at least 2x the peer-group median"
    )

    # ========================================================
    # SIGNAL 2
    # Peer cost ratio >= 5
    # ========================================================

    mask = (
        cost_ratio.notna()
        & (cost_ratio >= 5)
        & (cost_ratio < 10)
    )

    add_signal(
        mask,
        30,
        "PEER_RATIO_EXTREME",
        "Sanctioned cost is at least 5x the peer-group median"
    )

    # ========================================================
    # SIGNAL 3
    # Peer cost ratio >= 10
    # ========================================================

    mask = (
        cost_ratio.notna()
        & (cost_ratio >= 10)
    )

    add_signal(
        mask,
        40,
        "PEER_RATIO_SEVERE",
        "Sanctioned cost is at least 10x the peer-group median"
    )

    # ========================================================
    # SIGNAL 4
    # Z-SCORE >= 3
    # ========================================================

    zscore = numeric(
        df,
        "COST_VS_PEER_Z"
    )

    mask = (
        zscore.notna()
        & (zscore >= 3)
        & (zscore < 5)
    )

    add_signal(
        mask,
        20,
        "ZSCORE_HIGH",
        "Cost is more than 3 standard deviations above the peer distribution"
    )

    # ========================================================
    # SIGNAL 5
    # Z-SCORE >= 5
    # ========================================================

    mask = (
        zscore.notna()
        & (zscore >= 5)
        & (zscore < 10)
    )

    add_signal(
        mask,
        30,
        "ZSCORE_EXTREME",
        "Cost is more than 5 standard deviations above the peer distribution"
    )

    # ========================================================
    # SIGNAL 6
    # Z-SCORE >= 10
    # ========================================================

    mask = (
        zscore.notna()
        & (zscore >= 10)
    )

    add_signal(
        mask,
        40,
        "ZSCORE_SEVERE",
        "Cost is an extremely distant statistical outlier"
    )

    # ========================================================
    # SIGNAL 7
    # ROBUST DEVIATION
    # ========================================================

    robust_z = numeric(
        df,
        "COST_VS_PEER_ROBUST_Z"
    )

    if robust_z.notna().any():

        mask = (
            robust_z.notna()
            & (robust_z >= 3)
            & (robust_z < 5)
        )

        add_signal(
            mask,
            15,
            "ROBUST_Z_HIGH",
            "Cost is significantly above the robust peer distribution"
        )

        mask = (
            robust_z.notna()
            & (robust_z >= 5)
        )

        add_signal(
            mask,
            25,
            "ROBUST_Z_EXTREME",
            "Cost is an extreme outlier under robust statistical analysis"
        )

    # ========================================================
    # SIGNAL 8
    # PEER PERCENTILE
    # ========================================================

    percentile = numeric(
        df,
        "COST_PEER_PERCENTILE"
    )

    if percentile.notna().any():

        # Handles both 0-1 and 0-100 representations

        percentile_100 = np.where(
            percentile <= 1,
            percentile * 100,
            percentile
        )

        percentile_100 = pd.Series(
            percentile_100,
            index=df.index
        )

        mask = (
            percentile_100.notna()
            & (percentile_100 >= 95)
            & (percentile_100 < 99)
        )

        add_signal(
            mask,
            10,
            "PEER_PERCENTILE_HIGH",
            "Cost lies in the top 5% of the peer distribution"
        )

        mask = (
            percentile_100.notna()
            & (percentile_100 >= 99)
        )

        add_signal(
            mask,
            20,
            "PEER_PERCENTILE_EXTREME",
            "Cost lies in the top 1% of the peer distribution"
        )

    # ========================================================
    # SIGNAL 9
    # LOW PEER SAMPLE SIZE
    # ========================================================
    #
    # This is NOT an anomaly.
    # We record it as statistical confidence information.
    # ========================================================

    peer_count = numeric(
        df,
        "PEER_COUNT"
    )

    df["STATISTICAL_CONFIDENCE"] = "UNKNOWN"

    high_confidence = (
        peer_count.notna()
        & (peer_count >= 30)
    )

    medium_confidence = (
        peer_count.notna()
        & (peer_count >= 10)
        & (peer_count < 30)
    )

    low_confidence = (
        peer_count.notna()
        & (peer_count < 10)
    )

    df.loc[
        high_confidence,
        "STATISTICAL_CONFIDENCE"
    ] = "HIGH"

    df.loc[
        medium_confidence,
        "STATISTICAL_CONFIDENCE"
    ] = "MEDIUM"

    df.loc[
        low_confidence,
        "STATISTICAL_CONFIDENCE"
    ] = "LOW"

    # ========================================================
    # CAP SCORE
    # ========================================================

    df["STATISTICAL_SCORE"] = (
        df["STATISTICAL_SCORE"]
        .clip(
            lower=0,
            upper=100
        )
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

    df["STATISTICAL_RISK_LEVEL"] = (
        df["STATISTICAL_SCORE"]
        .apply(risk_level)
    )

    # ========================================================
    # REASONS
    # ========================================================

    df["STATISTICAL_REASON_CODES"] = [
        "|".join(x) if x else ""
        for x in reason_codes
    ]

    df["STATISTICAL_REASONS"] = [
        " | ".join(x)
        if x
        else "No statistical anomaly detected"
        for x in reasons
    ]

    # ========================================================
    # ANOMALY FLAG
    # ========================================================

    df["STATISTICAL_ANOMALY_FLAG"] = (
        df["STATISTICAL_SCORE"] >= 20
    )

    return df


# ============================================================
# SORT
# ============================================================

def sort_results(df):

    return df.sort_values(
        by="STATISTICAL_SCORE",
        ascending=False
    ).reset_index(drop=True)


# ============================================================
# SUMMARY
# ============================================================

def print_summary(df):

    print("\n" + "=" * 70)
    print("STATISTICAL DETECTION SUMMARY")
    print("=" * 70)

    total = len(df)

    anomaly_count = int(
        df["STATISTICAL_ANOMALY_FLAG"].sum()
    )

    print(
        f"Total works                  : {total:,}"
    )

    print(
        f"Statistical anomaly candidates: "
        f"{anomaly_count:,}"
    )

    print("\nRisk levels:")

    counts = (
        df["STATISTICAL_RISK_LEVEL"]
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

    print("\nStatistical signal counts:")

    signal_columns = [
        "PEER_RATIO_HIGH",
        "PEER_RATIO_EXTREME",
        "PEER_RATIO_SEVERE",
        "ZSCORE_HIGH",
        "ZSCORE_EXTREME",
        "ZSCORE_SEVERE",
        "ROBUST_Z_HIGH",
        "ROBUST_Z_EXTREME",
        "PEER_PERCENTILE_HIGH",
        "PEER_PERCENTILE_EXTREME"
    ]

    codes = (
        df["STATISTICAL_REASON_CODES"]
        .fillna("")
    )

    for code in signal_columns:

        count = codes.str.contains(
            code,
            regex=False
        ).sum()

        if count > 0:

            print(
                f"  {code:<35}: "
                f"{count:,}"
            )

    # ========================================================
    # TOP 20
    # ========================================================

    print("\nTop 20 statistical anomaly candidates:")
    print("-" * 70)

    columns = [
        "WORK_RECOMMENDATION_DTL_ID",
        "MP_NAME",
        "WORK_CATEGORY",
        "SANCTION_AMOUNT",
        "COST_VS_PEER_MEDIAN",
        "COST_VS_PEER_Z",
        "COST_VS_PEER_ROBUST_Z",
        "PEER_COUNT",
        "STATISTICAL_CONFIDENCE",
        "STATISTICAL_SCORE",
        "STATISTICAL_RISK_LEVEL",
        "STATISTICAL_REASON_CODES"
    ]

    columns = [
        c for c in columns
        if c in df.columns
    ]

    print(
        df[
            columns
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
        f"Saved statistical results to:\n"
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

    df = detect_statistical_anomalies(df)

    df = sort_results(df)

    print_summary(df)

    save_results(df)

    print(
        "\nStatistical detection completed successfully."
    )


if __name__ == "__main__":
    main()