import pandas as pd
from pathlib import Path


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = BASE_DIR / "data" / "processed" / "india_work_collection.csv"


# ============================================================
# LOAD
# ============================================================

print("=" * 70)
print("FUNDGUARD INDIA-WIDE COLLECTION VALIDATION")
print("=" * 70)

if not INPUT_FILE.exists():
    print(f"\nERROR: File not found:")
    print(INPUT_FILE)
    raise SystemExit(1)

print(f"\nLoading:")
print(INPUT_FILE)

df = pd.read_csv(INPUT_FILE, low_memory=False)

print("\nDataset loaded successfully.")
print(f"Rows:    {len(df):,}")
print(f"Columns: {len(df.columns):,}")


# ============================================================
# BASIC INFORMATION
# ============================================================

print("\n" + "=" * 70)
print("1. BASIC DATASET INFORMATION")
print("=" * 70)

print(f"Rows:    {len(df):,}")
print(f"Columns: {len(df.columns):,}")

print("\nColumns:")
for i, col in enumerate(df.columns, 1):
    print(f"{i:3}. {col}")


# ============================================================
# STATE ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("2. STATE / UT ANALYSIS")
print("=" * 70)

STATE_COL = "_STATE_NAME"

if STATE_COL in df.columns:

    states = (
        df[STATE_COL]
        .fillna("MISSING")
        .astype(str)
        .value_counts()
        .sort_index()
    )

    print(f"\nUnique states/UTs: {len(states)}\n")

    for state, count in states.items():
        print(f"{state:50} {count:>10,}")

else:
    print(f"ERROR: {STATE_COL} column not found.")


# ============================================================
# MP ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("3. MP ANALYSIS")
print("=" * 70)

MP_ID_COL = "_MP_ID"
MP_NAME_COL = "_MP_NAME"

if MP_ID_COL in df.columns:

    unique_mps = df[MP_ID_COL].nunique(dropna=True)
    print(f"Unique MP IDs: {unique_mps:,}")

if MP_NAME_COL in df.columns:

    unique_mp_names = df[MP_NAME_COL].nunique(dropna=True)
    print(f"Unique MP names: {unique_mp_names:,}")

    missing_mp_names = df[MP_NAME_COL].isna().sum()
    print(f"Missing MP names: {missing_mp_names:,}")


# ============================================================
# CONSTITUENCY ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("4. CONSTITUENCY ANALYSIS")
print("=" * 70)

CON_ID_COL = "_CONSTITUENCY_ID"
CON_NAME_COL = "_CONSTITUENCY"

if CON_ID_COL in df.columns:

    unique_constituencies = df[CON_ID_COL].nunique(dropna=True)
    print(f"Unique constituency IDs: {unique_constituencies:,}")

if CON_NAME_COL in df.columns:

    unique_constituency_names = df[CON_NAME_COL].nunique(dropna=True)
    print(
        f"Unique constituency names: "
        f"{unique_constituency_names:,}"
    )

    missing_constituencies = df[CON_NAME_COL].isna().sum()
    print(
        f"Missing constituency names: "
        f"{missing_constituencies:,}"
    )


# ============================================================
# STATE + CONSTITUENCY + MP MAPPING
# ============================================================

print("\n" + "=" * 70)
print("5. MP–CONSTITUENCY MAPPING")
print("=" * 70)

mapping_cols = [
    "_STATE_ID",
    "_STATE_NAME",
    "_MP_ID",
    "_MP_NAME",
    "_CONSTITUENCY_ID",
    "_CONSTITUENCY",
]

available_mapping_cols = [
    c for c in mapping_cols if c in df.columns
]

if len(available_mapping_cols) == len(mapping_cols):

    mappings = df[available_mapping_cols].drop_duplicates()

    print(
        f"Unique state/MP/constituency mappings: "
        f"{len(mappings):,}"
    )

    # Check MP + constituency combinations
    mp_const = (
        df[
            [
                "_STATE_ID",
                "_MP_ID",
                "_CONSTITUENCY_ID",
            ]
        ]
        .drop_duplicates()
    )

    print(
        f"Unique state + MP + constituency combinations: "
        f"{len(mp_const):,}"
    )

else:

    print("Some mapping columns are missing:")
    for col in mapping_cols:
        if col not in df.columns:
            print(f"  MISSING: {col}")


# ============================================================
# MISSING VALUES
# ============================================================

print("\n" + "=" * 70)
print("6. MISSING VALUES")
print("=" * 70)

missing = df.isna().sum()

missing = missing[missing > 0].sort_values(ascending=False)

if len(missing) == 0:

    print("No missing values.")

else:

    print("\nColumns containing missing values:\n")

    for col, count in missing.items():

        percentage = (count / len(df)) * 100

        print(
            f"{col:50} "
            f"{count:>10,} "
            f"({percentage:6.2f}%)"
        )


# ============================================================
# DUPLICATE ROWS
# ============================================================

print("\n" + "=" * 70)
print("7. DUPLICATE ROW ANALYSIS")
print("=" * 70)

duplicate_rows = df.duplicated().sum()

print(f"Duplicate complete rows: {duplicate_rows:,}")


# ============================================================
# WORK ID ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("8. WORK ID ANALYSIS")
print("=" * 70)

WORK_ID_CANDIDATES = [
    "WORK_ID",
    "Work_ID",
    "work_id",
    "WORKID",
    "WorkId",
    "ID",
    "WORKID_NO",
]

work_id_col = None

for col in WORK_ID_CANDIDATES:

    if col in df.columns:
        work_id_col = col
        break

if work_id_col:

    print(f"Work ID column: {work_id_col}")

    unique_work_ids = df[work_id_col].nunique(dropna=True)

    print(f"Unique work IDs: {unique_work_ids:,}")

    missing_work_ids = df[work_id_col].isna().sum()

    print(f"Missing work IDs: {missing_work_ids:,}")

    duplicate_work_ids = (
        df[work_id_col]
        .value_counts()
    )

    duplicate_work_ids = duplicate_work_ids[
        duplicate_work_ids > 1
    ]

    print(
        f"Work IDs appearing more than once: "
        f"{len(duplicate_work_ids):,}"
    )

else:

    print("WARNING: Could not automatically find a WORK_ID column.")


# ============================================================
# WORK ID + STATE CHECK
# ============================================================

print("\n" + "=" * 70)
print("9. CROSS-STATE WORK ID CHECK")
print("=" * 70)

if work_id_col and STATE_COL in df.columns:

    work_state_counts = (
        df.groupby(work_id_col)[STATE_COL]
        .nunique()
    )

    cross_state = work_state_counts[
        work_state_counts > 1
    ]

    print(
        f"Work IDs appearing in multiple states: "
        f"{len(cross_state):,}"
    )

    if len(cross_state) > 0:

        print("\nWARNING: Example cross-state Work IDs:")

        print(
            cross_state
            .sort_values(ascending=False)
            .head(20)
        )

    else:

        print("GOOD: No work IDs appear across multiple states.")


# ============================================================
# RECORD TYPE / SOURCE KEY
# ============================================================

print("\n" + "=" * 70)
print("10. SOURCE / RECORD TYPE ANALYSIS")
print("=" * 70)

SOURCE_COL = "_SOURCE_KEY"

if SOURCE_COL in df.columns:

    source_counts = (
        df[SOURCE_COL]
        .fillna("MISSING")
        .value_counts()
    )

    for source, count in source_counts.items():

        percentage = (count / len(df)) * 100

        print(
            f"{source:60} "
            f"{count:>10,} "
            f"({percentage:6.2f}%)"
        )

else:

    print(f"{SOURCE_COL} column not found.")


# ============================================================
# STATE SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("11. STATE SUMMARY")
print("=" * 70)

required_cols = [
    "_STATE_NAME",
    "_MP_ID",
    "_CONSTITUENCY_ID",
]

if all(col in df.columns for col in required_cols):

    state_summary = (
        df.groupby("_STATE_NAME")
        .agg(
            records=("_STATE_NAME", "size"),
            MPs=("_MP_ID", "nunique"),
            constituencies=("_CONSTITUENCY_ID", "nunique"),
        )
        .sort_values("records", ascending=False)
    )

    print()

    print(state_summary.to_string())


# ============================================================
# NUMERIC DATA
# ============================================================

print("\n" + "=" * 70)
print("12. NUMERIC COLUMN CHECK")
print("=" * 70)

numeric_cols = df.select_dtypes(
    include=["number"]
).columns

print(f"Numeric columns: {len(numeric_cols)}")

if len(numeric_cols) > 0:

    print("\nPotential infinite values:")

    for col in numeric_cols:

        try:

            inf_count = (
                df[col]
                .isin([float("inf"), float("-inf")])
                .sum()
            )

            if inf_count > 0:

                print(
                    f"  {col}: {inf_count:,}"
                )

        except Exception:
            pass


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)

print(f"""
Dataset:
    {INPUT_FILE}

Rows:
    {len(df):,}

Columns:
    {len(df.columns):,}

States / UTs:
    {df[STATE_COL].nunique(dropna=True) if STATE_COL in df.columns else "N/A"}

Unique MPs:
    {df[MP_ID_COL].nunique(dropna=True) if MP_ID_COL in df.columns else "N/A"}

Unique Constituencies:
    {df[CON_ID_COL].nunique(dropna=True) if CON_ID_COL in df.columns else "N/A"}

Duplicate complete rows:
    {duplicate_rows:,}
""")

print("=" * 70)
print("DO NOT RUN THE ML PIPELINE YET.")
print("Review the validation output first.")
print("=" * 70)