import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = BASE_DIR / "data" / "processed" / "india_work_collection.csv"

print("=" * 70)
print("FUNDGUARD WORK ID VALIDATION")
print("=" * 70)

if not INPUT_FILE.exists():
    print(f"ERROR: File not found: {INPUT_FILE}")
    raise SystemExit(1)

df = pd.read_csv(INPUT_FILE, low_memory=False)

print(f"\nRows loaded: {len(df):,}")

ID_COL = "WORK_RECOMMENDATION_DTL_ID"

if ID_COL not in df.columns:
    print(f"ERROR: {ID_COL} not found.")
    raise SystemExit(1)

# ------------------------------------------------------------
# 1. BASIC ID COUNTS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("1. BASIC WORK ID COUNTS")
print("=" * 70)

total_rows = len(df)

missing_ids = df[ID_COL].isna().sum()

unique_ids = df[ID_COL].nunique(dropna=True)

print(f"Total rows:       {total_rows:,}")
print(f"Unique work IDs:  {unique_ids:,}")
print(f"Missing work IDs: {missing_ids:,}")


# ------------------------------------------------------------
# 2. DUPLICATE IDs
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("2. DUPLICATE WORK IDs")
print("=" * 70)

id_counts = df[ID_COL].value_counts()

duplicate_ids = id_counts[id_counts > 1]

print(
    f"Work IDs appearing more than once: "
    f"{len(duplicate_ids):,}"
)

if len(duplicate_ids) > 0:

    print("\nTop duplicated IDs:")

    print(
        duplicate_ids
        .head(20)
        .to_string()
    )

else:

    print("GOOD: Every work ID appears only once.")


# ------------------------------------------------------------
# 3. WORK ID + STATE
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("3. WORK IDs ACROSS STATES")
print("=" * 70)

if "_STATE_NAME" in df.columns:

    state_counts = (
        df.groupby(ID_COL)["_STATE_NAME"]
        .nunique()
    )

    cross_state = state_counts[state_counts > 1]

    print(
        f"Work IDs appearing in multiple states: "
        f"{len(cross_state):,}"
    )

    if len(cross_state) > 0:

        print("\nExamples:")

        examples = (
            df[df[ID_COL].isin(cross_state.index)]
            [[ID_COL, "_STATE_NAME", "_MP_NAME", "_CONSTITUENCY"]]
            .sort_values(ID_COL)
            .head(30)
        )

        print(examples.to_string(index=False))

    else:

        print("GOOD: No work ID appears across multiple states.")


# ------------------------------------------------------------
# 4. WORK ID + MP
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("4. WORK IDs ACROSS MPs")
print("=" * 70)

if "_MP_ID" in df.columns:

    mp_counts = (
        df.groupby(ID_COL)["_MP_ID"]
        .nunique()
    )

    cross_mp = mp_counts[mp_counts > 1]

    print(
        f"Work IDs associated with multiple MPs: "
        f"{len(cross_mp):,}"
    )

    if len(cross_mp) > 0:

        print("\nExamples:")

        examples = (
            df[df[ID_COL].isin(cross_mp.index)]
            [[ID_COL, "_STATE_NAME", "_MP_ID", "_MP_NAME"]]
            .sort_values(ID_COL)
            .head(30)
        )

        print(examples.to_string(index=False))

    else:

        print("GOOD: No work ID is associated with multiple MPs.")


# ------------------------------------------------------------
# 5. WORK ID + CONSTITUENCY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("5. WORK IDs ACROSS CONSTITUENCIES")
print("=" * 70)

if "_CONSTITUENCY_ID" in df.columns:

    constituency_counts = (
        df.groupby(ID_COL)["_CONSTITUENCY_ID"]
        .nunique()
    )

    cross_constituency = constituency_counts[
        constituency_counts > 1
    ]

    print(
        f"Work IDs associated with multiple constituencies: "
        f"{len(cross_constituency):,}"
    )

    if len(cross_constituency) > 0:

        print("\nExamples:")

        examples = (
            df[df[ID_COL].isin(cross_constituency.index)]
            [[
                ID_COL,
                "_STATE_NAME",
                "_CONSTITUENCY_ID",
                "_CONSTITUENCY"
            ]]
            .sort_values(ID_COL)
            .head(30)
        )

        print(examples.to_string(index=False))

    else:

        print(
            "GOOD: No work ID is associated with "
            "multiple constituencies."
        )


# ------------------------------------------------------------
# 6. WORK ID + SOURCE KEY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("6. WORK IDs ACROSS SOURCE TYPES")
print("=" * 70)

if "_SOURCE_KEY" in df.columns:

    source_counts = (
        df.groupby(ID_COL)["_SOURCE_KEY"]
        .nunique()
    )

    multiple_sources = source_counts[
        source_counts > 1
    ]

    print(
        f"Work IDs appearing under multiple source types: "
        f"{len(multiple_sources):,}"
    )

    if len(multiple_sources) > 0:

        print("\nExamples:")

        examples = (
            df[df[ID_COL].isin(multiple_sources.index)]
            [[ID_COL, "_SOURCE_KEY", "_STATE_NAME"]]
            .sort_values(ID_COL)
            .head(50)
        )

        print(examples.to_string(index=False))

    else:

        print(
            "No work IDs appear under multiple source types."
        )


# ------------------------------------------------------------
# 7. WORK ID + STAGE
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("7. WORK IDs ACROSS WORK STAGES")
print("=" * 70)

if "WORK_STAGE" in df.columns:

    stage_counts = (
        df.groupby(ID_COL)["WORK_STAGE"]
        .nunique()
    )

    multiple_stages = stage_counts[
        stage_counts > 1
    ]

    print(
        f"Work IDs with multiple WORK_STAGE values: "
        f"{len(multiple_stages):,}"
    )

    if len(multiple_stages) > 0:

        print("\nExamples:")

        examples = (
            df[df[ID_COL].isin(multiple_stages.index)]
            [[ID_COL, "WORK_STAGE", "_SOURCE_KEY"]]
            .sort_values(ID_COL)
            .head(50)
        )

        print(examples.to_string(index=False))

    else:

        print("No work IDs have multiple WORK_STAGE values.")


# ------------------------------------------------------------
# 8. SOURCE × ID SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("8. SOURCE / UNIQUE WORK ID SUMMARY")
print("=" * 70)

if "_SOURCE_KEY" in df.columns:

    summary = (
        df.groupby("_SOURCE_KEY")[ID_COL]
        .agg(
            records="size",
            unique_work_ids="nunique"
        )
    )

    summary["duplicate_records"] = (
        summary["records"] -
        summary["unique_work_ids"]
    )

    print(summary.to_string())


# ------------------------------------------------------------
# 9. POTENTIAL ONE-ROW-PER-WORK TEST
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("9. ONE-ROW-PER-WORK TEST")
print("=" * 70)

if missing_ids == 0 and len(duplicate_ids) == 0:

    print(
        "PASS: WORK_RECOMMENDATION_DTL_ID is unique "
        "for every row."
    )

elif missing_ids > 0:

    print(
        "WARNING: Some rows have missing work IDs."
    )

    if len(duplicate_ids) > 0:
        print(
            "WARNING: Some work IDs also appear multiple times."
        )

else:

    print(
        "WARNING: Multiple rows share the same work ID."
    )


# ------------------------------------------------------------
# 10. FINAL RESULT
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL RESULT")
print("=" * 70)

print(f"""
Rows:                  {total_rows:,}
Unique WORK IDs:       {unique_ids:,}
Missing WORK IDs:      {missing_ids:,}
Duplicate WORK IDs:    {len(duplicate_ids):,}
""")

print("=" * 70)
print("WORK ID VALIDATION COMPLETE")
print("=" * 70)