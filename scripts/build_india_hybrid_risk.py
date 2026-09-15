from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# FUNDGUARD — HYBRID RISK ENGINE
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
OUT = BASE_DIR / "data" / "outputs"

RULE_FILE = OUT / "india_rule_anomalies.csv"
STAT_FILE = OUT / "india_statistical_anomalies.csv"
ML_FILE = OUT / "india_ml_anomalies.csv"

HYBRID_FILE = OUT / "india_hybrid_risk.csv"
SUMMARY_FILE = OUT / "india_hybrid_summary.csv"


# ============================================================
# HELPERS
# ============================================================

def section(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def load(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found:\n{path}")

    df = pd.read_csv(path, low_memory=False)

    if "WORK_ID" not in df.columns:
        raise ValueError(f"WORK_ID missing in {path}")

    df["WORK_ID"] = df["WORK_ID"].astype(str).str.strip()

    return df


def number(series, default=0):
    return pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(default)


# ============================================================
# 1. LOAD
# ============================================================

section("1. LOADING DETECTOR OUTPUTS")

rules = load(RULE_FILE)
stats = load(STAT_FILE)
ml = load(ML_FILE)

print(f"Rules rows       : {len(rules):,}")
print(f"Statistical rows : {len(stats):,}")
print(f"ML rows          : {len(ml):,}")


# ============================================================
# 2. VALIDATE
# ============================================================

section("2. VALIDATING INPUTS")

for name, df in [
    ("RULE", rules),
    ("STAT", stats),
    ("ML", ml),
]:

    print(
        f"{name:6s} "
        f"rows={len(df):,} "
        f"unique={df['WORK_ID'].nunique():,} "
        f"missing={df['WORK_ID'].isna().sum():,} "
        f"duplicates={df['WORK_ID'].duplicated().sum():,}"
    )

    if df["WORK_ID"].isna().any():
        raise ValueError(f"{name}: missing WORK_ID")

    if df["WORK_ID"].duplicated().any():
        raise ValueError(f"{name}: duplicate WORK_ID")


# ============================================================
# 3. VERIFY REQUIRED COLUMNS
# ============================================================

section("3. CHECKING REQUIRED COLUMNS")

required_rule = [
    "RULE_CANDIDATE",
    "RULE_SCORE",
    "RULE_SEVERITY",
]

required_stat = [
    "STAT_CANDIDATE",
    "STAT_SCORE",
    "STAT_SEVERITY",
]

required_ml = [
    "ML_ANOMALY",
    "ML_PERCENTILE",
    "ML_SEVERITY",
]


for column in required_rule:

    if column not in rules.columns:
        raise ValueError(
            f"Missing rule column: {column}"
        )


for column in required_stat:

    if column not in stats.columns:
        raise ValueError(
            f"Missing statistical column: {column}"
        )


for column in required_ml:

    if column not in ml.columns:
        raise ValueError(
            f"Missing ML column: {column}"
        )


print("All required detector columns found.")


# ============================================================
# 4. BUILD BASE FROM ML
# ============================================================

section("4. BUILDING BASE TABLE")

# ML contains every work, so use it as the master table.

context_columns = [
    "WORK_ID",
    "STATE_ID",
    "STATE_NAME",
    "CONSTITUENCY_ID",
    "CONSTITUENCY",
    "MP_ID",
    "MP_NAME",
    "WORK_CATEGORY",
    "ACTIVITY_NAME",
    "WORK_DESCRIPTION",
    "WORK_STAGE",
    "SOURCE_KEY",

    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "TOTAL_FUND_DISBURSED_AMT",

    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",

    "ML_ANOMALY",
    "ML_PERCENTILE",
    "ML_SEVERITY",
]


context_columns = [
    c for c in context_columns
    if c in ml.columns
]


base = ml[context_columns].copy()


base["ML_CANDIDATE"] = number(
    base["ML_ANOMALY"]
).astype(int)


base["ML_PERCENTILE"] = number(
    base["ML_PERCENTILE"],
    np.nan
)


base["ML_SEVERITY"] = (
    base["ML_SEVERITY"]
    .fillna("NONE")
    .astype(str)
)


print(
    f"Base rows : {len(base):,}"
)


# ============================================================
# 5. MERGE RULES
# ============================================================

section("5. MERGING RULE DETECTOR")

rule_data = rules[
    [
        "WORK_ID",
        "RULE_CANDIDATE",
        "RULE_SCORE",
        "RULE_SEVERITY",
    ]
].copy()


rule_data["RULE_CANDIDATE"] = number(
    rule_data["RULE_CANDIDATE"]
).astype(int)


rule_data["RULE_SCORE"] = number(
    rule_data["RULE_SCORE"]
)


rule_data["RULE_SEVERITY"] = (
    rule_data["RULE_SEVERITY"]
    .fillna("NONE")
    .astype(str)
)


base = base.merge(
    rule_data,
    on="WORK_ID",
    how="left",
    validate="one_to_one"
)


base["RULE_CANDIDATE"] = (
    number(
        base["RULE_CANDIDATE"]
    )
    .astype(int)
)


base["RULE_SCORE"] = number(
    base["RULE_SCORE"]
)


base["RULE_SEVERITY"] = (
    base["RULE_SEVERITY"]
    .fillna("NONE")
    .astype(str)
)


print(
    f"Rule candidates : "
    f"{base['RULE_CANDIDATE'].sum():,}"
)


# ============================================================
# 6. MERGE STATISTICS
# ============================================================

section("6. MERGING STATISTICAL DETECTOR")

stat_data = stats[
    [
        "WORK_ID",
        "STAT_CANDIDATE",
        "STAT_SCORE",
        "STAT_SEVERITY",
    ]
].copy()


stat_data["STAT_CANDIDATE"] = number(
    stat_data["STAT_CANDIDATE"]
).astype(int)


stat_data["STAT_SCORE"] = number(
    stat_data["STAT_SCORE"]
)


stat_data["STAT_SEVERITY"] = (
    stat_data["STAT_SEVERITY"]
    .fillna("NONE")
    .astype(str)
)


base = base.merge(
    stat_data,
    on="WORK_ID",
    how="left",
    validate="one_to_one"
)


base["STAT_CANDIDATE"] = (
    number(
        base["STAT_CANDIDATE"]
    )
    .astype(int)
)


base["STAT_SCORE"] = number(
    base["STAT_SCORE"]
)


base["STAT_SEVERITY"] = (
    base["STAT_SEVERITY"]
    .fillna("NONE")
    .astype(str)
)


print(
    f"Statistical candidates : "
    f"{base['STAT_CANDIDATE'].sum():,}"
)


# ============================================================
# 7. VERIFY MERGE
# ============================================================

section("7. VALIDATING HYBRID TABLE")

print(
    f"Rows           : {len(base):,}"
)

print(
    f"Unique WORK_ID : "
    f"{base['WORK_ID'].nunique():,}"
)

print(
    f"Missing IDs    : "
    f"{base['WORK_ID'].isna().sum():,}"
)

print(
    f"Duplicate IDs  : "
    f"{base['WORK_ID'].duplicated().sum():,}"
)


if len(base) != len(ml):
    raise ValueError(
        "Row count changed during hybrid merge."
    )


if base["WORK_ID"].duplicated().any():
    raise ValueError(
        "Duplicate WORK_ID after merge."
    )


# ============================================================
# 8. INDEPENDENT SIGNAL COUNT
# ============================================================

section("8. INDEPENDENT SIGNAL COUNT")

base["INDEPENDENT_SIGNAL_COUNT"] = (
    base["RULE_CANDIDATE"]
    + base["STAT_CANDIDATE"]
    + base["ML_CANDIDATE"]
)


print(
    base[
        "INDEPENDENT_SIGNAL_COUNT"
    ]
    .value_counts()
    .sort_index()
    .to_string()
)


# ============================================================
# 9. HYBRID SCORE (CALIBRATED 0–100 MULTI-DETECTOR FUSION)
# ============================================================

section("9. CALCULATING CALIBRATED HYBRID RISK SCORE")

# ------------------------------------------------------------
# 1. 0–100 UNIFIED CALIBRATION PER DETECTOR
# ------------------------------------------------------------
# Rule score (0–35 scale) normalized to 0–100
base["RULE_SCORE_CALIBRATED"] = np.clip(
    (base["RULE_SCORE"] / 35.0) * 100.0,
    0,
    100.0
)

# Statistical IQR/Z-score (0–35 scale) normalized to 0–100
base["STAT_SCORE_CALIBRATED"] = np.clip(
    (base["STAT_SCORE"] / 35.0) * 100.0,
    0,
    100.0
)

# ML Isolation Forest score (already 0–100 percentile rank)
base["ML_SCORE_CALIBRATED"] = np.clip(
    base["ML_PERCENTILE"],
    0,
    100.0
)

# ------------------------------------------------------------
# 2. PEER DATA SUFFICIENT FLAG
# ------------------------------------------------------------
if "PEER_COUNT" in base.columns:
    base["PEER_DATA_SUFFICIENT"] = (number(base["PEER_COUNT"]) >= 10).astype(int)
elif "STAT_PEER_COUNT" in base.columns:
    base["PEER_DATA_SUFFICIENT"] = (number(base["STAT_PEER_COUNT"]) >= 10).astype(int)
else:
    base["PEER_DATA_SUFFICIENT"] = 1

# ------------------------------------------------------------
# 3. DATA QUALITY TIER
# ------------------------------------------------------------
missing_cnt = number(base["MISSING_FIELD_COUNT"]) if "MISSING_FIELD_COUNT" in base.columns else 0
base["DATA_QUALITY_TIER"] = np.select(
    [
        missing_cnt == 0,
        missing_cnt == 1,
        missing_cnt >= 2
    ],
    [
        "HIGH",
        "MEDIUM",
        "LOW"
    ],
    default="MEDIUM"
)

# ------------------------------------------------------------
# 4. WEIGHTED FUSION (0.35 RULES / 0.35 STATS / 0.30 ML)
# ------------------------------------------------------------
base["RULE_COMPONENT"] = base["RULE_SCORE_CALIBRATED"] * 0.35
base["STAT_COMPONENT"] = base["STAT_SCORE_CALIBRATED"] * 0.35
base["ML_COMPONENT"] = base["ML_SCORE_CALIBRATED"] * 0.30

# ------------------------------------------------------------
# 5. DETECTOR AGREEMENT BONUS
# ------------------------------------------------------------
base["AGREEMENT_BONUS"] = np.select(
    [
        base["INDEPENDENT_SIGNAL_COUNT"] >= 3,
        base["INDEPENDENT_SIGNAL_COUNT"] >= 2,
    ],
    [
        10.0,
        5.0,
    ],
    default=0.0
)

# ------------------------------------------------------------
# 6. FINAL HYBRID RISK SCORE (0–100 SCALE)
# ------------------------------------------------------------
base["HYBRID_RISK_SCORE"] = np.round(
    base["RULE_COMPONENT"]
    + base["STAT_COMPONENT"]
    + base["ML_COMPONENT"]
    + base["AGREEMENT_BONUS"],
    1
)

# ============================================================
# 10. RISK LEVEL
# ============================================================

section("10. RISK LEVEL")

base["HYBRID_RISK_LEVEL"] = np.select(
    [
        base["HYBRID_RISK_SCORE"] >= 60,
        base["HYBRID_RISK_SCORE"] >= 40,
        base["HYBRID_RISK_SCORE"] >= 20,
        base["HYBRID_RISK_SCORE"] > 0,
    ],
    [
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    ],
    default="NONE"
)

# ============================================================
# 11. PRIORITY
# ============================================================

section("11. INVESTIGATION PRIORITY")

base["INVESTIGATION_PRIORITY"] = np.select(
    [
        base["HYBRID_RISK_SCORE"] >= 60,
        base["HYBRID_RISK_SCORE"] >= 40,
        base["HYBRID_RISK_SCORE"] >= 20,
        base["HYBRID_RISK_SCORE"] > 0,
    ],
    [
        "P1",
        "P2",
        "P3",
        "P4",
    ],
    default="P0"
)


# ============================================================
# 12. AGREEMENT DESCRIPTION
# ============================================================

base["DETECTOR_AGREEMENT"] = np.select(
    [
        base["INDEPENDENT_SIGNAL_COUNT"] == 3,
        base["INDEPENDENT_SIGNAL_COUNT"] == 2,
        base["INDEPENDENT_SIGNAL_COUNT"] == 1,
    ],
    [
        "RULE + STATISTICAL + ML",
        "TWO METHODS AGREE",
        "ONE METHOD",
    ],
    default="NO SIGNAL"
)


base["INVESTIGATION_CANDIDATE"] = (
    base["INDEPENDENT_SIGNAL_COUNT"] > 0
).astype(int)


# ============================================================
# 13. SORT
# ============================================================

priority_order = {
    "P1": 1,
    "P2": 2,
    "P3": 3,
    "P4": 4,
    "P0": 5,
}


base["_PRIORITY"] = (
    base["INVESTIGATION_PRIORITY"]
    .map(priority_order)
)


base = base.sort_values(
    [
        "_PRIORITY",
        "HYBRID_RISK_SCORE",
        "ML_PERCENTILE",
    ],
    ascending=[
        True,
        False,
        False,
    ]
)


base = base.drop(
    columns=["_PRIORITY"]
)


# ============================================================
# 14. FINAL COLUMNS
# ============================================================

final_columns = [
    "WORK_ID",
    "STATE_ID",
    "STATE_NAME",
    "CONSTITUENCY_ID",
    "CONSTITUENCY",
    "MP_ID",
    "MP_NAME",

    "WORK_CATEGORY",
    "ACTIVITY_NAME",
    "WORK_DESCRIPTION",
    "WORK_STAGE",
    "SOURCE_KEY",

    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "TOTAL_FUND_DISBURSED_AMT",

    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",

    "RULE_SCORE",
    "RULE_SCORE_CALIBRATED",
    "RULE_SEVERITY",
    "RULE_CANDIDATE",

    "STAT_SCORE",
    "STAT_SCORE_CALIBRATED",
    "STAT_SEVERITY",
    "STAT_CANDIDATE",

    "ML_PERCENTILE",
    "ML_SCORE_CALIBRATED",
    "ML_SEVERITY",
    "ML_CANDIDATE",

    "PEER_DATA_SUFFICIENT",
    "DATA_QUALITY_TIER",

    "RULE_COMPONENT",
    "STAT_COMPONENT",
    "ML_COMPONENT",
    "AGREEMENT_BONUS",

    "INDEPENDENT_SIGNAL_COUNT",
    "DETECTOR_AGREEMENT",

    "HYBRID_RISK_SCORE",
    "HYBRID_RISK_LEVEL",
    "INVESTIGATION_PRIORITY",
    "INVESTIGATION_CANDIDATE",
]


hybrid = base[
    [
        c for c in final_columns
        if c in base.columns
    ]
].copy()


# ============================================================
# 15. SAVE
# ============================================================

section("12. SAVING OUTPUT")

OUT.mkdir(
    parents=True,
    exist_ok=True
)


hybrid.to_csv(
    HYBRID_FILE,
    index=False
)


print(
    f"Saved: {HYBRID_FILE}"
)


# ============================================================
# 16. SUMMARY
# ============================================================

section("13. HYBRID SUMMARY")

total = len(hybrid)

candidates = int(
    hybrid[
        "INVESTIGATION_CANDIDATE"
    ].sum()
)


print(
    f"Total works              : "
    f"{total:,}"
)

print(
    f"Investigation candidates : "
    f"{candidates:,}"
)

print(
    f"Candidate percentage     : "
    f"{candidates / total * 100:.2f}%"
)


print()

print(
    "Risk level distribution:"
)


risk_summary = (
    hybrid
    .groupby(
        "HYBRID_RISK_LEVEL"
    )
    .size()
    .reindex(
        [
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW",
            "NONE",
        ],
        fill_value=0
    )
    .rename("WORK_COUNT")
    .reset_index()
)


risk_summary["PERCENTAGE"] = (
    risk_summary["WORK_COUNT"]
    / total
    * 100
)


print(
    risk_summary.to_string(
        index=False
    )
)


# ============================================================
# 17. AGREEMENT SUMMARY
# ============================================================

print()

print(
    "Detector agreement:"
)


agreement = (
    hybrid
    .groupby(
        "DETECTOR_AGREEMENT"
    )
    .size()
    .sort_values(
        ascending=False
    )
    .rename("WORK_COUNT")
    .reset_index()
)


agreement["PERCENTAGE"] = (
    agreement["WORK_COUNT"]
    / total
    * 100
)


print(
    agreement.to_string(
        index=False
    )
)


# ============================================================
# 18. TOP STATES
# ============================================================

print()

print(
    "Top states by investigation candidates:"
)


state_summary = (
    hybrid[
        hybrid[
            "INVESTIGATION_CANDIDATE"
        ] == 1
    ]
    .groupby("STATE_NAME")
    .size()
    .sort_values(
        ascending=False
    )
    .rename(
        "INVESTIGATION_CANDIDATES"
    )
    .reset_index()
)


print(
    state_summary
    .head(20)
    .to_string(index=False)
)


# ============================================================
# 19. TOP 30 QUEUE
# ============================================================

section(
    "14. TOP 30 INVESTIGATION CANDIDATES"
)


queue_columns = [
    "WORK_ID",
    "STATE_NAME",
    "CONSTITUENCY",
    "MP_NAME",

    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",

    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",

    "RULE_CANDIDATE",
    "STAT_CANDIDATE",
    "ML_CANDIDATE",

    "INDEPENDENT_SIGNAL_COUNT",
    "DETECTOR_AGREEMENT",

    "HYBRID_RISK_SCORE",
    "HYBRID_RISK_LEVEL",
    "INVESTIGATION_PRIORITY",
]


top30 = (
    hybrid[
        hybrid[
            "INVESTIGATION_CANDIDATE"
        ] == 1
    ]
    .head(30)
)


print(
    top30[
        queue_columns
    ].to_string(
        index=False
    )
)


# ============================================================
# 20. SAVE SUMMARY
# ============================================================

summary = pd.DataFrame(
    [
        {
            "METRIC": "TOTAL_WORKS",
            "VALUE": total,
        },
        {
            "METRIC": "INVESTIGATION_CANDIDATES",
            "VALUE": candidates,
        },
        {
            "METRIC": "CANDIDATE_PERCENTAGE",
            "VALUE":
                candidates / total * 100,
        },
        {
            "METRIC": "RULE_CANDIDATES",
            "VALUE":
                int(
                    hybrid[
                        "RULE_CANDIDATE"
                    ].sum()
                ),
        },
        {
            "METRIC": "STATISTICAL_CANDIDATES",
            "VALUE":
                int(
                    hybrid[
                        "STAT_CANDIDATE"
                    ].sum()
                ),
        },
        {
            "METRIC": "ML_CANDIDATES",
            "VALUE":
                int(
                    hybrid[
                        "ML_CANDIDATE"
                    ].sum()
                ),
        },
        {
            "METRIC": "TWO_OR_MORE_METHODS",
            "VALUE":
                int(
                    (
                        hybrid[
                            "INDEPENDENT_SIGNAL_COUNT"
                        ] >= 2
                    ).sum()
                ),
        },
        {
            "METRIC": "ALL_THREE_METHODS",
            "VALUE":
                int(
                    (
                        hybrid[
                            "INDEPENDENT_SIGNAL_COUNT"
                        ] == 3
                    ).sum()
                ),
        },
    ]
)


summary.to_csv(
    SUMMARY_FILE,
    index=False
)


print(
    f"Saved: {SUMMARY_FILE}"
)


# ============================================================
# DONE
# ============================================================

section(
    "HYBRID RISK ENGINE COMPLETE"
)

print(
    "Rule detector       : READY"
)

print(
    "Statistical detector: READY"
)

print(
    "ML detector         : READY"
)

print(
    "Hybrid risk engine  : READY"
)

print()

print(
    "Next: Evidence Builder"
)

print()

print(
    "Risk scores are investigation-priority signals, "
    "not findings of fraud or corruption."
)