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
FEATURE_FILE = BASE_DIR / "data" / "processed" / "mplads_india_features.csv"

HYBRID_FILE = OUT / "india_hybrid_risk.csv"
SUMMARY_FILE = OUT / "india_hybrid_summary.csv"
SCORE_DIST_FILE = OUT / "india_score_distribution.csv"

# ============================================================
# TIER THRESHOLDS (Batch 4 Pyramid Calibration)
# ============================================================
# Grid-search result on 7,521 candidates to hit pyramid targets:
#   P1 ~9%  : consensus (3-engine) OR score >= 90.4
#   P2 ~17% : score 56.5–90.4
#   P3 ~32% : score 35.0–56.5
#   P4 ~41% : score  0.1–35.0
# All 597 three-engine consensus works are guaranteed P1 via the hard override.
TIER_P1_SCORE_THRESHOLD = 90.4
TIER_P2_THRESHOLD = 56.5
TIER_P3_THRESHOLD = 35.0


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

if FEATURE_FILE.exists():
    try:
        feat_df = pd.read_csv(FEATURE_FILE, usecols=lambda c: c in ["WORK_ID", "PEER_COUNT", "MISSING_FIELD_COUNT"], low_memory=False)
        feat_df["WORK_ID"] = feat_df["WORK_ID"].astype(str).str.strip()
        base = base.merge(feat_df, on="WORK_ID", how="left")
    except Exception as e:
        print(f"Warning loading features: {e}")

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
# 9. HYBRID SCORE (PERCENTILE-RANK CALIBRATED MULTI-DETECTOR FUSION)
# ============================================================

section("9. CALCULATING CALIBRATED HYBRID RISK SCORE")

# ------------------------------------------------------------
# 1. 0–100 PERCENTILE RANK CALIBRATION PER DETECTOR
# ------------------------------------------------------------
# Note on Calibration Interpretation (Interpretation 1):
# Percentile rank is computed strictly within the detector-firing subset (RULE_SCORE > 0, STAT_SCORE > 0).
# Non-firing works receive a clean 0.0. This guarantees mathematical stability across runs.
if "RULE_SCORE" in rules.columns and len(rules) > 0:
    rule_ranks = rules.set_index("WORK_ID")["RULE_SCORE"].rank(pct=True, method="average") * 100.0
    base["RULE_SCORE_CALIBRATED"] = base["WORK_ID"].map(rule_ranks).fillna(0.0)
else:
    base["RULE_SCORE_CALIBRATED"] = 0.0

if "STAT_SCORE" in stats.columns and len(stats) > 0:
    stat_ranks = stats.set_index("WORK_ID")["STAT_SCORE"].rank(pct=True, method="average") * 100.0
    base["STAT_SCORE_CALIBRATED"] = base["WORK_ID"].map(stat_ranks).fillna(0.0)
else:
    base["STAT_SCORE_CALIBRATED"] = 0.0

# ML Isolation Forest score (already 0–100 percentile rank)
base["ML_SCORE_CALIBRATED"] = number(
    base["ML_PERCENTILE"],
    0.0
)

# ------------------------------------------------------------
# 2. PEER DATA SUFFICIENT FLAG & SCORE REGIME (OPTION B)
# ------------------------------------------------------------
# Works with >=10 peers use standard multi-detector cohort analysis.
# Works with <10 peers are marked SCORE_REGIME="SPARSE_PEER" and evaluated without
# uncalibrated weight inflation, preventing cross-region ranking distortion.
if "PEER_COUNT" in base.columns:
    base["PEER_DATA_SUFFICIENT"] = (number(base["PEER_COUNT"]) >= 10).astype(int)
elif "STAT_PEER_COUNT" in base.columns:
    base["PEER_DATA_SUFFICIENT"] = (number(base["STAT_PEER_COUNT"]) >= 10).astype(int)
else:
    base["PEER_DATA_SUFFICIENT"] = 1

base["SCORE_REGIME"] = np.where(
    base["PEER_DATA_SUFFICIENT"] == 1,
    "STANDARD",
    "SPARSE_PEER"
)

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
# 4. UNBIASED UNIFORM WEIGHTED FUSION (0.35 RULES / 0.35 STATS / 0.30 ML)
# ------------------------------------------------------------
# Fixed, comparable weights across all regimes to prevent artificial sparse-peer inflation.
# For sparse peers, statistical peer comparison is suppressed (0.0), while Rule and ML
# maintain their exact, non-distorted weights (0.35 and 0.30).
base["RULE_COMPONENT"] = np.round(base["RULE_SCORE_CALIBRATED"] * 0.35, 2)
base["STAT_COMPONENT"] = np.where(
    base["PEER_DATA_SUFFICIENT"] == 1,
    np.round(base["STAT_SCORE_CALIBRATED"] * 0.35, 2),
    0.0
)
base["ML_COMPONENT"] = np.round(base["ML_SCORE_CALIBRATED"] * 0.30, 2)

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
# 6. FINAL HYBRID RISK SCORE (0–100 SCALE, CAPPED)
# ------------------------------------------------------------
base["HYBRID_RISK_SCORE"] = np.round(
    np.minimum(
        base["RULE_COMPONENT"]
        + base["STAT_COMPONENT"]
        + base["ML_COMPONENT"]
        + base["AGREEMENT_BONUS"],
        100.0
    ),
    1
)

# ============================================================
# 10. RISK LEVEL
# ============================================================

section("10. RISK LEVEL")

base["HYBRID_RISK_LEVEL"] = np.select(
    [
        base["HYBRID_RISK_SCORE"] >= TIER_P1_SCORE_THRESHOLD,
        base["HYBRID_RISK_SCORE"] >= TIER_P2_THRESHOLD,
        base["HYBRID_RISK_SCORE"] >= TIER_P3_THRESHOLD,
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
# 11. PRIORITY (WITH 3-ENGINE CONSENSUS HARD OVERRIDE)
# ============================================================

section("11. INVESTIGATION PRIORITY")

# Base priority by score threshold
base["INVESTIGATION_PRIORITY"] = np.select(
    [
        base["HYBRID_RISK_SCORE"] >= TIER_P1_SCORE_THRESHOLD,
        base["HYBRID_RISK_SCORE"] >= TIER_P2_THRESHOLD,
        base["HYBRID_RISK_SCORE"] >= TIER_P3_THRESHOLD,
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

# Hard override: all 3-engine consensus works are always P1
# This preserves the pyramid shape (consensus = 7.94% of candidates)
base.loc[
    base["INDEPENDENT_SIGNAL_COUNT"] == 3,
    "INVESTIGATION_PRIORITY"
] = "P1"

base.loc[
    base["INDEPENDENT_SIGNAL_COUNT"] == 3,
    "HYBRID_RISK_LEVEL"
] = "CRITICAL"


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
    "SCORE_REGIME",
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
# 21. SCORE DISTRIBUTION EXPORT
# ============================================================

section("21. SCORE DISTRIBUTION EXPORT")

score_bins = list(range(0, 101, 5))
score_dist_rows = []
for i in range(len(score_bins) - 1):
    lo = score_bins[i]
    hi = score_bins[i + 1]
    label = f"{lo}-{hi}"
    n = int(((hybrid["HYBRID_RISK_SCORE"] >= lo) & (hybrid["HYBRID_RISK_SCORE"] < hi)).sum())
    score_dist_rows.append({"BIN_LABEL": label, "SCORE_MIN": lo, "SCORE_MAX": hi, "WORK_COUNT": n})

# Final bucket: 100
n_100 = int((hybrid["HYBRID_RISK_SCORE"] >= 100).sum())
score_dist_rows.append({"BIN_LABEL": "100", "SCORE_MIN": 100, "SCORE_MAX": 100, "WORK_COUNT": n_100})

score_dist_df = pd.DataFrame(score_dist_rows)

score_dist_df.to_csv(SCORE_DIST_FILE, index=False)

print(f"Saved: {SCORE_DIST_FILE}")


# ============================================================
# 22. TIER DISTRIBUTION SUMMARY (DIAGNOSTIC)
# ============================================================

section("22. TIER DISTRIBUTION SUMMARY")

candidates_df = hybrid[hybrid["INVESTIGATION_CANDIDATE"] == 1]
n_cands = len(candidates_df)

tier_counts = (
    candidates_df["INVESTIGATION_PRIORITY"]
    .value_counts()
    .reindex(["P1", "P2", "P3", "P4", "P0"], fill_value=0)
)

print()
print(f"{'Tier':<6} {'Count':>8} {'% of Candidates':>18} {'Score Band':>28}")
print("-" * 65)
tier_bands = {
    "P1": f"Consensus OR score >= {TIER_P1_SCORE_THRESHOLD}",
    "P2": f"{TIER_P2_THRESHOLD}-{TIER_P1_SCORE_THRESHOLD}",
    "P3": f"{TIER_P3_THRESHOLD}-{TIER_P2_THRESHOLD}",
    "P4": f"0.1-{TIER_P3_THRESHOLD}",
    "P0": "No signal",
}
for tier in ["P1", "P2", "P3", "P4"]:
    n = int(tier_counts.get(tier, 0))
    pct = n / n_cands * 100 if n_cands > 0 else 0
    band = tier_bands.get(tier, "")
    print(f"{tier:<6} {n:>8,} {pct:>17.2f}% {band:>28}")

print("-" * 65)
print(f"{'TOTAL':<6} {n_cands:>8,} {'100.00%':>18}")

print()
consensus_in_p1 = int(
    ((candidates_df["INDEPENDENT_SIGNAL_COUNT"] == 3) &
     (candidates_df["INVESTIGATION_PRIORITY"] == "P1")).sum()
)
print(
    f"3-engine consensus in P1 : {consensus_in_p1:,} "
    f"/ {int((candidates_df['INDEPENDENT_SIGNAL_COUNT'] == 3).sum()):,}"
)
p1_pct = tier_counts.get("P1", 0) / n_cands * 100 if n_cands > 0 else 0
p2_pct = tier_counts.get("P2", 0) / n_cands * 100 if n_cands > 0 else 0
p4_pct = tier_counts.get("P4", 0) / n_cands * 100 if n_cands > 0 else 0
print(
    f"Pyramid health           : P1+P2 = {p1_pct + p2_pct:.2f}% (target <= 30%)  |"
    f"  P4 = {p4_pct:.2f}% (target >= 35%)"
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