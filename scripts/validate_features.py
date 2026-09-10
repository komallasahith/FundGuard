import pandas as pd
import numpy as np
from pathlib import Path

INPUT = Path("data/processed/mplads_features.csv")

print("=" * 75)
print("FUNDGUARD AI — PHASE 2.5")
print("FEATURE VALIDATION")
print("=" * 75)

df = pd.read_csv(INPUT)

print(f"\nRows:    {len(df):,}")
print(f"Columns: {len(df.columns)}")


# =========================================================
# 1. MISSING VALUES
# =========================================================

print("\n" + "-" * 75)
print("1. MISSING VALUE ANALYSIS")
print("-" * 75)

missing = df.isna().sum()
missing_pct = (missing / len(df)) * 100

missing_report = pd.DataFrame({
    "missing": missing,
    "percentage": missing_pct
})

missing_report = missing_report[
    missing_report["missing"] > 0
].sort_values(
    "missing",
    ascending=False
)

print(missing_report.to_string())


# =========================================================
# 2. NUMERIC FEATURE SUMMARY
# =========================================================

print("\n" + "-" * 75)
print("2. NUMERIC FEATURE SUMMARY")
print("-" * 75)

numeric = df.select_dtypes(
    include=["number"]
)

print(
    numeric.describe()
    .T[
        [
            "count",
            "mean",
            "std",
            "min",
            "50%",
            "max"
        ]
    ]
    .to_string()
)


# =========================================================
# 3. INFINITE VALUES
# =========================================================

print("\n" + "-" * 75)
print("3. INFINITE VALUE CHECK")
print("-" * 75)

inf_counts = np.isinf(
    numeric
).sum()

inf_counts = inf_counts[
    inf_counts > 0
]

if len(inf_counts) == 0:
    print("No infinite values found. ✅")
else:
    print(inf_counts.to_string())


# =========================================================
# 4. NEGATIVE TIMELINES
# =========================================================

print("\n" + "-" * 75)
print("4. NEGATIVE TIMELINE INVESTIGATION")
print("-" * 75)

timeline_cols = [
    "RECOMMENDATION_TO_SANCTION_DAYS",
    "SANCTION_TO_COMPLETION_DAYS",
    "RECOMMENDATION_TO_COMPLETION_DAYS",
]

for column in timeline_cols:

    if column not in df.columns:
        continue

    negative = df[column] < 0

    print(
        f"{column}: "
        f"{negative.sum():,} negative values"
    )


# Detailed negative timeline cases

negative_cases = df[
    (
        df["RECOMMENDATION_TO_SANCTION_DAYS"] < 0
    )
    |
    (
        df["SANCTION_TO_COMPLETION_DAYS"] < 0
    )
].copy()

print(
    f"\nTotal works with at least one negative timeline: "
    f"{len(negative_cases):,}"
)

if len(negative_cases) > 0:

    columns = [
        "WORK_RECOMMENDATION_DTL_ID",
        "WORK_ID",
        "MP_NAME",
        "CONSTITUENCY",
        "RECOMMENDATION_DATE",
        "SANCTION_DATE",
        "ACTUAL_END_DATE",
        "RECOMMENDATION_TO_SANCTION_DAYS",
        "SANCTION_TO_COMPLETION_DAYS",
        "WORK_STAGE",
        "WORK_STATUS",
    ]

    columns = [
        c for c in columns
        if c in negative_cases.columns
    ]

    print("\nSample negative timeline records:")
    print(
        negative_cases[columns]
        .head(30)
        .to_string(index=False)
    )


# =========================================================
# 5. FINANCIAL RATIO CHECK
# =========================================================

print("\n" + "-" * 75)
print("5. FINANCIAL RATIO VALIDATION")
print("-" * 75)

ratio_columns = [
    "RECOMMENDATION_TO_SANCTION_RATIO",
    "ACTUAL_TO_SANCTION_RATIO",
    "DISBURSEMENT_TO_SANCTION_RATIO",
    "COST_VS_PEER_MEDIAN",
]

for column in ratio_columns:

    if column not in df.columns:
        continue

    series = df[column].dropna()

    print(f"\n{column}")

    print(
        f"  Available: {len(series):,}"
    )

    print(
        f"  < 0:       {(series < 0).sum():,}"
    )

    print(
        f"  = 0:       {(series == 0).sum():,}"
    )

    print(
        f"  > 1:       {(series > 1).sum():,}"
    )

    print(
        f"  > 2:       {(series > 2).sum():,}"
    )

    print(
        f"  > 5:       {(series > 5).sum():,}"
    )

    print(
        f"  Maximum:   {series.max():,.4f}"
    )


# =========================================================
# 6. FINANCIAL CONSISTENCY
# =========================================================

print("\n" + "-" * 75)
print("6. FINANCIAL CONSISTENCY")
print("-" * 75)

checks = {
    "Actual > Sanction":
        (
            df["ACTUAL_AMOUNT"]
            > df["SANCTION_AMOUNT"]
        ),

    "Disbursement > Sanction":
        (
            df["TOTAL_DISBURSED"]
            > df["SANCTION_AMOUNT"]
        ),

    "Sanction < Recommended":
        (
            df["SANCTION_AMOUNT"]
            < df["RECOMMENDED_AMOUNT"]
        ),

    "Negative sanctioned amount":
        (
            df["SANCTION_AMOUNT"] < 0
        ),

    "Negative actual amount":
        (
            df["ACTUAL_AMOUNT"] < 0
        ),

    "Negative disbursement":
        (
            df["TOTAL_DISBURSED"] < 0
        ),
}

for name, condition in checks.items():

    print(
        f"{name:35} "
        f"{condition.fillna(False).sum():,}"
    )


# =========================================================
# 7. TRANSACTION FEATURES
# =========================================================

print("\n" + "-" * 75)
print("7. TRANSACTION FEATURE CHECK")
print("-" * 75)

transaction_columns = [
    "TRANSACTION_COUNT",
    "VENDOR_COUNT",
    "EXPENDITURE_DATE_COUNT",
]

for column in transaction_columns:

    if column not in df.columns:
        continue

    print(
        f"{column:30} "
        f"min={df[column].min()} "
        f"median={df[column].median()} "
        f"max={df[column].max()}"
    )


# =========================================================
# 8. CATEGORICAL COVERAGE
# =========================================================

print("\n" + "-" * 75)
print("8. CATEGORICAL COVERAGE")
print("-" * 75)

categorical_columns = [
    "STATE_NAME",
    "MP_NAME",
    "CONSTITUENCY",
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
    "WORK_STAGE",
    "WORK_STATUS",
]

for column in categorical_columns:

    if column not in df.columns:
        continue

    print(
        f"{column:25} "
        f"unique={df[column].nunique(dropna=True):,} "
        f"missing={df[column].isna().sum():,}"
    )


# =========================================================
# 9. DUPLICATE WORK IDENTIFIERS
# =========================================================

print("\n" + "-" * 75)
print("9. WORK IDENTIFIER CHECK")
print("-" * 75)

print(
    "Unique WORK_RECOMMENDATION_DTL_ID:",
    df["WORK_RECOMMENDATION_DTL_ID"].nunique()
)

print(
    "Duplicate master rows:",
    df["WORK_RECOMMENDATION_DTL_ID"].duplicated().sum()
)


# =========================================================
# 10. EXTREME COST VALUES
# =========================================================

print("\n" + "-" * 75)
print("10. EXTREME SANCTION AMOUNTS")
print("-" * 75)

cols = [
    "WORK_RECOMMENDATION_DTL_ID",
    "WORK_ID",
    "MP_NAME",
    "CONSTITUENCY",
    "WORK_CATEGORY",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "TOTAL_DISBURSED",
    "COST_VS_PEER_MEDIAN",
    "COST_Z_SCORE",
]

cols = [
    c for c in cols
    if c in df.columns
]

print(
    df[
        cols
    ]
    .sort_values(
        "SANCTION_AMOUNT",
        ascending=False
    )
    .head(20)
    .to_string(index=False)
)


# =========================================================
# 11. RISK SIGNAL SUMMARY
# =========================================================

print("\n" + "-" * 75)
print("11. EXISTING RISK SIGNALS")
print("-" * 75)

risk_columns = [
    "MULTIPLE_VENDOR_FLAG",
    "MULTIPLE_TRANSACTION_FLAG",
    "ACTUAL_EXCEEDS_SANCTION_FLAG",
    "DISBURSEMENT_EXCEEDS_SANCTION_FLAG",
    "NEGATIVE_TIMELINE_FLAG",
]

for column in risk_columns:

    if column in df.columns:

        print(
            f"{column:40} "
            f"{df[column].sum():,}"
        )


print("\n" + "=" * 75)
print("FEATURE VALIDATION REPORT COMPLETE")
print("=" * 75)