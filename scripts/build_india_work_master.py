import pandas as pd
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = Path("data/processed/india_work_collection.csv")
OUTPUT_FILE = Path("data/processed/mplads_india_work_master.csv")


# ============================================================
# LOAD
# ============================================================

print("=" * 70)
print("FUNDGUARD INDIA-WIDE WORK MASTER")
print("=" * 70)

if not INPUT_FILE.exists():
    print(f"\nERROR: Input file not found:")
    print(INPUT_FILE)
    raise SystemExit(1)

print(f"\nLoading:")
print(INPUT_FILE)

df = pd.read_csv(INPUT_FILE, low_memory=False)

print(f"Loaded rows: {len(df):,}")
print(f"Loaded columns: {len(df.columns):,}")


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "WORK_RECOMMENDATION_DTL_ID",
    "STATE_NAME",
    "CONSTITUENCY_ID",
    "CONSTITUENCY",
    "MP_NAME",
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
    "WORK_DESCRIPTION",
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "WORK_STAGE",
    "_STATE_ID",
    "_STATE_NAME",
    "_MP_ID",
    "_MP_NAME",
    "_CONSTITUENCY_ID",
    "_CONSTITUENCY",
    "_SOURCE_KEY",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:

    print("\nERROR: Required columns missing:")

    for col in missing_columns:
        print(f"  - {col}")

    raise SystemExit(1)


# ============================================================
# CREATE CLEAN WORK MASTER
# ============================================================

print("\n[1/5] Creating canonical WORK_ID...")

master = pd.DataFrame()

master["WORK_ID"] = df["WORK_RECOMMENDATION_DTL_ID"]


# ============================================================
# GEOGRAPHY
# ============================================================

print("[2/5] Adding geography...")

master["STATE_ID"] = df["_STATE_ID"]

master["STATE_NAME"] = (
    df["_STATE_NAME"]
    .fillna(df["STATE_NAME"])
)

master["CONSTITUENCY_ID"] = (
    df["_CONSTITUENCY_ID"]
    .fillna(df["CONSTITUENCY_ID"])
)

master["CONSTITUENCY"] = (
    df["_CONSTITUENCY"]
    .fillna(df["CONSTITUENCY"])
)


# ============================================================
# MP
# ============================================================

print("[3/5] Adding MP information...")

master["MP_ID"] = df["_MP_ID"]

master["MP_NAME"] = (
    df["_MP_NAME"]
    .fillna(df["MP_NAME"])
)


# ============================================================
# WORK INFORMATION
# ============================================================

print("[4/5] Adding work information...")

master["WORK_CATEGORY"] = df["WORK_CATEGORY"]

master["ACTIVITY_NAME"] = df["ACTIVITY_NAME"]

master["WORK_DESCRIPTION"] = df["WORK_DESCRIPTION"]

master["WORK_STAGE"] = df["WORK_STAGE"]

master["SOURCE_KEY"] = df["_SOURCE_KEY"]


# ============================================================
# FINANCIAL INFORMATION
# ============================================================

master["RECOMMENDED_AMOUNT"] = pd.to_numeric(
    df["RECOMMENDED_AMOUNT"],
    errors="coerce"
)

master["SANCTION_AMOUNT"] = pd.to_numeric(
    df["SANCTION_AMOUNT"],
    errors="coerce"
)


# ============================================================
# DATE INFORMATION
# ============================================================

master["RECOMMENDATION_DATE"] = pd.to_datetime(
    df["RECOMMENDATION_DATE"],
    errors="coerce"
)

master["SANCTION_DATE"] = pd.to_datetime(
    df["SANCTION_DATE"],
    errors="coerce"
)


# ============================================================
# ADDITIONAL RAW INFORMATION
# ============================================================

master["ATTACH_ID"] = df["ATTACH_ID"]

master["FILE_STATUS"] = df["FILE_STATUS"]

master["FLAG"] = df["FLAG"]

master["HOUSE_OF_PARLIAMENT"] = df["HOUSE_OF_PARLIAMENT"]

master["IDA_NAME"] = df["IDA_NAME"]

master["LETTER_NO"] = df["LETTER_NO"]

master["TENURE"] = df["TENURE"]

master["TENURE_START_DATE"] = pd.to_datetime(
    df["TENURE_START_DATE"],
    errors="coerce"
)

master["TENURE_END_DATE"] = pd.to_datetime(
    df["TENURE_END_DATE"],
    errors="coerce"
)


# ============================================================
# REMOVE DUPLICATE WORK IDs
# ============================================================

print("\n[5/5] Validating one-row-per-work structure...")

before = len(master)

master = master.drop_duplicates(
    subset=["WORK_ID"],
    keep="first"
)

after = len(master)

removed = before - after

print(f"Rows before deduplication: {before:,}")
print(f"Rows after deduplication:  {after:,}")
print(f"Duplicate rows removed:    {removed:,}")


# ============================================================
# SORT
# ============================================================

master = master.sort_values(
    by=[
        "STATE_NAME",
        "CONSTITUENCY",
        "MP_NAME",
        "WORK_ID"
    ],
    na_position="last"
).reset_index(drop=True)


# ============================================================
# SAVE
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

master.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("INDIA WORK MASTER CREATED")
print("=" * 70)

print(f"""
Output:
    {OUTPUT_FILE}

Rows:
    {len(master):,}

Columns:
    {len(master.columns):,}

Unique WORK_IDs:
    {master["WORK_ID"].nunique(dropna=True):,}

Missing WORK_IDs:
    {master["WORK_ID"].isna().sum():,}

States / UTs:
    {master["STATE_NAME"].nunique(dropna=True):,}

MPs:
    {master["MP_ID"].nunique(dropna=True):,}

Constituencies:
    {master["CONSTITUENCY_ID"].nunique(dropna=True):,}
""")

print("=" * 70)
print("WORK MASTER BUILD COMPLETE")
print("=" * 70)