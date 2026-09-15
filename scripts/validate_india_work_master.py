import pandas as pd
from pathlib import Path


INPUT_FILE = Path(
    "data/processed/mplads_india_work_master.csv"
)


print("=" * 70)
print("FUNDGUARD INDIA WORK MASTER VALIDATION")
print("=" * 70)


# ============================================================
# LOAD
# ============================================================

if not INPUT_FILE.exists():
    print(f"ERROR: File not found: {INPUT_FILE}")
    raise SystemExit(1)

df = pd.read_csv(
    INPUT_FILE,
    low_memory=False
)

print(f"\nRows:    {len(df):,}")
print(f"Columns: {len(df.columns):,}")


# ============================================================
# 1. WORK ID
# ============================================================

print("\n" + "=" * 70)
print("1. WORK ID")
print("=" * 70)

print(
    f"Unique WORK_IDs: "
    f"{df['WORK_ID'].nunique(dropna=True):,}"
)

print(
    f"Missing WORK_IDs: "
    f"{df['WORK_ID'].isna().sum():,}"
)

print(
    f"Duplicate WORK_IDs: "
    f"{df['WORK_ID'].duplicated().sum():,}"
)


# ============================================================
# 2. GEOGRAPHY
# ============================================================

print("\n" + "=" * 70)
print("2. GEOGRAPHY")
print("=" * 70)

for col in [
    "STATE_ID",
    "STATE_NAME",
    "CONSTITUENCY_ID",
    "CONSTITUENCY"
]:

    print(
        f"{col:25} "
        f"unique={df[col].nunique(dropna=True):,} "
        f"missing={df[col].isna().sum():,}"
    )


# ============================================================
# 3. MP
# ============================================================

print("\n" + "=" * 70)
print("3. MP")
print("=" * 70)

for col in [
    "MP_ID",
    "MP_NAME"
]:

    print(
        f"{col:25} "
        f"unique={df[col].nunique(dropna=True):,} "
        f"missing={df[col].isna().sum():,}"
    )


# ============================================================
# 4. WORK INFORMATION
# ============================================================

print("\n" + "=" * 70)
print("4. WORK INFORMATION")
print("=" * 70)

for col in [
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
    "WORK_DESCRIPTION",
    "WORK_STAGE",
    "SOURCE_KEY"
]:

    print(
        f"{col:25} "
        f"unique={df[col].nunique(dropna=True):,} "
        f"missing={df[col].isna().sum():,}"
    )


# ============================================================
# 5. FINANCIAL DATA
# ============================================================

print("\n" + "=" * 70)
print("5. FINANCIAL DATA")
print("=" * 70)

financial_cols = [
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT"
]

for col in financial_cols:

    values = pd.to_numeric(
        df[col],
        errors="coerce"
    )

    print(f"\n{col}")

    print(
        f"  Missing: "
        f"{values.isna().sum():,}"
    )

    print(
        f"  Zero: "
        f"{(values == 0).sum():,}"
    )

    print(
        f"  Negative: "
        f"{(values < 0).sum():,}"
    )

    if values.notna().any():

        print(
            f"  Minimum: "
            f"{values.min():,.2f}"
        )

        print(
            f"  Maximum: "
            f"{values.max():,.2f}"
        )

        print(
            f"  Median: "
            f"{values.median():,.2f}"
        )


# ============================================================
# 6. RECOMMENDED VS SANCTIONED
# ============================================================

print("\n" + "=" * 70)
print("6. RECOMMENDED VS SANCTIONED")
print("=" * 70)

recommended = pd.to_numeric(
    df["RECOMMENDED_AMOUNT"],
    errors="coerce"
)

sanctioned = pd.to_numeric(
    df["SANCTION_AMOUNT"],
    errors="coerce"
)

both_available = (
    recommended.notna()
    & sanctioned.notna()
)

print(
    f"Both amounts available: "
    f"{both_available.sum():,}"
)

print(
    f"Recommended > Sanctioned: "
    f"{(
        (recommended > sanctioned)
        & both_available
    ).sum():,}"
)

print(
    f"Sanctioned > Recommended: "
    f"{(
        (sanctioned > recommended)
        & both_available
    ).sum():,}"
)

print(
    f"Equal amounts: "
    f"{(
        (recommended == sanctioned)
        & both_available
    ).sum():,}"
)


# ============================================================
# 7. DATES
# ============================================================

print("\n" + "=" * 70)
print("7. DATES")
print("=" * 70)

date_cols = [
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "TENURE_START_DATE",
    "TENURE_END_DATE"
]

for col in date_cols:

    dates = pd.to_datetime(
        df[col],
        errors="coerce"
    )

    print(f"\n{col}")

    print(
        f"  Valid dates: "
        f"{dates.notna().sum():,}"
    )

    print(
        f"  Missing dates: "
        f"{dates.isna().sum():,}"
    )

    if dates.notna().any():

        print(
            f"  Earliest: "
            f"{dates.min()}"
        )

        print(
            f"  Latest: "
            f"{dates.max()}"
        )


# ============================================================
# 8. DATE CONSISTENCY
# ============================================================

print("\n" + "=" * 70)
print("8. DATE CONSISTENCY")
print("=" * 70)

recommendation_date = pd.to_datetime(
    df["RECOMMENDATION_DATE"],
    errors="coerce"
)

sanction_date = pd.to_datetime(
    df["SANCTION_DATE"],
    errors="coerce"
)

both_dates = (
    recommendation_date.notna()
    & sanction_date.notna()
)

sanction_before_recommendation = (
    (sanction_date < recommendation_date)
    & both_dates
)

print(
    "Sanction date before recommendation date: "
    f"{sanction_before_recommendation.sum():,}"
)


# ============================================================
# 9. STATE SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("9. STATE SUMMARY")
print("=" * 70)

state_summary = (
    df.groupby("STATE_NAME")
    .agg(
        works=("WORK_ID", "nunique"),
        MPs=("MP_ID", "nunique"),
        constituencies=("CONSTITUENCY_ID", "nunique"),
        recommended=(
            "RECOMMENDED_AMOUNT",
            lambda x: pd.to_numeric(
                x,
                errors="coerce"
            ).sum()
        ),
        sanctioned=(
            "SANCTION_AMOUNT",
            lambda x: pd.to_numeric(
                x,
                errors="coerce"
            ).sum()
        )
    )
    .sort_values(
        "works",
        ascending=False
    )
)

print(
    state_summary.to_string()
)


# ============================================================
# 10. CATEGORY SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("10. WORK CATEGORY SUMMARY")
print("=" * 70)

category_summary = (
    df["WORK_CATEGORY"]
    .fillna("MISSING")
    .value_counts()
)

print(
    category_summary.to_string()
)


# ============================================================
# 11. SOURCE SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("11. SOURCE SUMMARY")
print("=" * 70)

print(
    df["SOURCE_KEY"]
    .fillna("MISSING")
    .value_counts()
    .to_string()
)


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 70)
print("WORK MASTER VALIDATION COMPLETE")
print("=" * 70)

print(
    f"""
Rows:              {len(df):,}
Columns:           {len(df.columns):,}
States/UTs:        {df['STATE_NAME'].nunique(dropna=True):,}
MPs:               {df['MP_ID'].nunique(dropna=True):,}
Constituencies:    {df['CONSTITUENCY_ID'].nunique(dropna=True):,}
Unique WORK_IDs:   {df['WORK_ID'].nunique(dropna=True):,}
"""
)

print("=" * 70)