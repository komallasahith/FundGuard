import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT = BASE_DIR / "data" / "processed" / "mplads_validated_dedup.csv"
OUTPUT = BASE_DIR / "data" / "processed" / "mplads_work_master.csv"

WORK_KEY = "WORK_RECOMMENDATION_DTL_ID"

print("=" * 70)
print("FUNDGUARD AI — PHASE 2.2")
print("BUILD WORK MASTER DATASET")
print("=" * 70)

# =========================================================
# LOAD
# =========================================================

df = pd.read_csv(INPUT)

print(f"\nInput records: {len(df):,}")
print(f"Unique work IDs: {df[WORK_KEY].nunique():,}")


# =========================================================
# HELPER
# =========================================================

def first_valid(series):
    """
    Return the first meaningful non-null value.
    """
    for value in series:
        if pd.notna(value):
            value = str(value).strip()

            if value and value.lower() not in [
                "nan",
                "none",
                "null"
            ]:
                return value

    return None


def numeric_first(series):
    """
    Return first valid numeric value.
    """
    values = pd.to_numeric(series, errors="coerce").dropna()

    if len(values) > 0:
        return values.iloc[0]

    return None


# =========================================================
# CREATE ONE ROW PER WORK
# =========================================================

work_ids = (
    df[WORK_KEY]
    .dropna()
    .drop_duplicates()
)

master = pd.DataFrame({
    WORK_KEY: work_ids
})

print(f"Master works created: {len(master):,}")


# =========================================================
# WORK INFORMATION
# =========================================================

text_fields = [
    "WORK_ID",
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
    "STATE_NAME",
    "HOUSE_OF_PARLIAMENT",
    "IDA_NAME",
    "TENURE",
    "MP_NAME",
    "WORK_DESCRIPTION",
    "WORK_STAGE",
    "LETTER_NO",
    "CONSTITUENCY",
    "FILE_STATUS",
    "IA_NAME",
    "VENDOR_NAME",
    "WORK_STATUS",
]


for field in text_fields:

    if field not in df.columns:
        continue

    values = (
        df.groupby(WORK_KEY)[field]
        .agg(first_valid)
        .rename(field)
    )

    master = master.merge(
        values,
        on=WORK_KEY,
        how="left"
    )


# =========================================================
# IDENTIFIERS
# =========================================================

id_fields = [
    "CONSTITUENCY_ID",
    "_MP_ID",
    "VENDOR_ID",
]

for field in id_fields:

    if field not in df.columns:
        continue

    values = (
        df.groupby(WORK_KEY)[field]
        .agg(first_valid)
        .rename(field)
    )

    master = master.merge(
        values,
        on=WORK_KEY,
        how="left"
    )


# =========================================================
# DATES
# =========================================================

date_fields = [
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "ACTUAL_END_DATE",
    "TENURE_START_DATE",
    "TENURE_END_DATE",
]

for field in date_fields:

    if field not in df.columns:
        continue

    values = (
        df.groupby(WORK_KEY)[field]
        .agg(first_valid)
        .rename(field)
    )

    master = master.merge(
        values,
        on=WORK_KEY,
        how="left"
    )


# =========================================================
# FINANCIAL VALUES
# =========================================================

financial_fields = [
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
]

for field in financial_fields:

    if field not in df.columns:
        continue

    values = (
        df.groupby(WORK_KEY)[field]
        .agg(numeric_first)
        .rename(field)
    )

    master = master.merge(
        values,
        on=WORK_KEY,
        how="left"
    )


# =========================================================
# LIFECYCLE SOURCE FLAGS
# =========================================================

source_groups = {
    "IS_RECOMMENDED": "Works Recommended",
    "IS_SANCTIONED": "Works Sanctioned",
    "IS_COMPLETED": "Works Completed",
    "HAS_EXPENDITURE_RECORD":
        "Expenditure on Completed and On-going Works as on Date",
}


for new_column, source_name in source_groups.items():

    ids = set(
        df.loc[
            df["_SOURCE_KEY"] == source_name,
            WORK_KEY
        ].dropna()
    )

    master[new_column] = (
        master[WORK_KEY]
        .isin(ids)
        .astype(int)
    )


# =========================================================
# SOURCE RECORD COUNTS
# =========================================================

source_counts = (
    df.groupby([WORK_KEY, "_SOURCE_KEY"])
    .size()
    .unstack(fill_value=0)
)

source_columns = {
    "RECOMMENDED_RECORD_COUNT":
        "Works Recommended",

    "SANCTIONED_RECORD_COUNT":
        "Works Sanctioned",

    "COMPLETED_RECORD_COUNT":
        "Works Completed",

    "EXPENDITURE_RECORD_COUNT":
        "Expenditure on Completed and On-going Works as on Date",
}


for new_column, source_name in source_columns.items():

    if source_name in source_counts.columns:

        master[new_column] = (
            master[WORK_KEY]
            .map(source_counts[source_name])
            .fillna(0)
            .astype(int)
        )

    else:

        master[new_column] = 0


# =========================================================
# NORMALIZE FINANCIAL COLUMNS
# =========================================================

for field in [
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
]:

    if field in master.columns:

        master[field] = pd.to_numeric(
            master[field],
            errors="coerce"
        )


# =========================================================
# BASIC FINANCIAL FEATURES
# =========================================================

master["RECOMMENDATION_TO_SANCTION_RATIO"] = (
    master["SANCTION_AMOUNT"]
    / master["RECOMMENDED_AMOUNT"]
)

master["ACTUAL_TO_SANCTION_RATIO"] = (
    master["ACTUAL_AMOUNT"]
    / master["SANCTION_AMOUNT"]
)

master["SANCTION_MINUS_RECOMMENDED"] = (
    master["SANCTION_AMOUNT"]
    - master["RECOMMENDED_AMOUNT"]
)

master["SANCTION_MINUS_ACTUAL"] = (
    master["SANCTION_AMOUNT"]
    - master["ACTUAL_AMOUNT"]
)


# =========================================================
# DATE CONVERSION
# =========================================================

for field in [
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "ACTUAL_END_DATE",
    "TENURE_START_DATE",
    "TENURE_END_DATE",
]:

    if field in master.columns:

        master[field] = pd.to_datetime(
            master[field],
            errors="coerce",
            dayfirst=True
        )


# =========================================================
# TIMELINE FEATURES
# =========================================================

master["RECOMMENDATION_TO_SANCTION_DAYS"] = (
    master["SANCTION_DATE"]
    - master["RECOMMENDATION_DATE"]
).dt.days

master["SANCTION_TO_COMPLETION_DAYS"] = (
    master["ACTUAL_END_DATE"]
    - master["SANCTION_DATE"]
).dt.days

master["RECOMMENDATION_TO_COMPLETION_DAYS"] = (
    master["ACTUAL_END_DATE"]
    - master["RECOMMENDATION_DATE"]
).dt.days


# =========================================================
# DATA QUALITY FLAGS
# =========================================================

master["MISSING_SANCTION_AMOUNT"] = (
    master["SANCTION_AMOUNT"].isna().astype(int)
)

master["MISSING_ACTUAL_AMOUNT"] = (
    master["ACTUAL_AMOUNT"].isna().astype(int)
)

master["MISSING_RECOMMENDATION_DATE"] = (
    master["RECOMMENDATION_DATE"].isna().astype(int)
)

master["MISSING_SANCTION_DATE"] = (
    master["SANCTION_DATE"].isna().astype(int)
)


# =========================================================
# SAVE
# =========================================================

master = master.sort_values(
    WORK_KEY
).reset_index(drop=True)

master.to_csv(
    OUTPUT,
    index=False
)


# =========================================================
# REPORT
# =========================================================

print("\n" + "-" * 70)
print("MASTER DATASET")
print("-" * 70)

print(f"Rows:    {len(master):,}")
print(f"Columns: {len(master.columns)}")

print("\nLifecycle coverage:")

for column in [
    "IS_RECOMMENDED",
    "IS_SANCTIONED",
    "IS_COMPLETED",
    "HAS_EXPENDITURE_RECORD",
]:

    print(
        f"{column:35} "
        f"{master[column].sum():,}"
    )


print("\nFinancial availability:")

for column in [
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
]:

    if column in master.columns:

        available = master[column].notna().sum()

        print(
            f"{column:30} "
            f"{available:,}"
        )


print("\nTimeline availability:")

for column in [
    "RECOMMENDATION_TO_SANCTION_DAYS",
    "SANCTION_TO_COMPLETION_DAYS",
]:

    print(
        f"{column:40} "
        f"{master[column].notna().sum():,}"
    )


print("\nSaved:")
print(OUTPUT)

print("\n" + "=" * 70)
print("PHASE 2.2 COMPLETE")
print("=" * 70)