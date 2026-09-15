from pathlib import Path
import sys
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# FUNDGUARD — INDIA EVIDENCE BUILDER
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

FEATURE_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "mplads_india_features.csv"
)

HYBRID_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_hybrid_risk.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_investigation_queue.csv"
)


# ============================================================
# HELPERS
# ============================================================

def section(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def clean_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        if np.isnan(value):
            return None
        return float(value)

    return value


def first_existing(df, names):
    for name in names:
        if name in df.columns:
            return name
    return None


def get_value(row, names):
    column = first_existing(row.to_frame().T, names)

    if column is None:
        return None

    return clean_value(row[column])


def fmt_money(value):
    if value is None:
        return "Not available"

    try:
        return f"₹{float(value):,.2f}"
    except Exception:
        return str(value)


def fmt_number(value):
    if value is None:
        return "Not available"

    try:
        x = float(value)

        if x.is_integer():
            return f"{int(x):,}"

        return f"{x:,.2f}"

    except Exception:
        return str(value)


def fmt_days(value):
    if value is None:
        return "Not available"

    try:
        return f"{float(value):,.0f} days"
    except Exception:
        return str(value)


def fmt_percent(value):
    if value is None:
        return "Not available"

    try:
        x = float(value)

        # Ratios such as 0.82 -> 82%
        if 0 <= x <= 1:
            x *= 100

        return f"{x:.1f}%"

    except Exception:
        return str(value)


def is_positive(value):
    if value is None:
        return False

    try:
        return float(value) > 0
    except Exception:
        return False


# ============================================================
# 1. LOAD
# ============================================================

section("1. LOADING DATA")

if not FEATURE_FILE.exists():
    raise FileNotFoundError(
        f"Feature file not found:\n{FEATURE_FILE}"
    )

if not HYBRID_FILE.exists():
    raise FileNotFoundError(
        f"Hybrid file not found:\n{HYBRID_FILE}"
    )


features = pd.read_csv(
    FEATURE_FILE,
    low_memory=False
)

hybrid = pd.read_csv(
    HYBRID_FILE,
    low_memory=False
)


print(
    f"Feature rows : {len(features):,}"
)

print(
    f"Hybrid rows  : {len(hybrid):,}"
)


# ============================================================
# 2. VALIDATE
# ============================================================

section("2. VALIDATING WORK IDS")

for name, df in [
    ("FEATURE", features),
    ("HYBRID", hybrid),
]:

    if "WORK_ID" not in df.columns:
        raise ValueError(
            f"WORK_ID missing from {name}"
        )

    df["WORK_ID"] = (
        df["WORK_ID"]
        .astype(str)
        .str.strip()
    )

    print(
        f"{name:8s} "
        f"rows={len(df):,} "
        f"unique={df['WORK_ID'].nunique():,} "
        f"missing={df['WORK_ID'].isna().sum():,} "
        f"duplicates={df['WORK_ID'].duplicated().sum():,}"
    )


if features["WORK_ID"].duplicated().any():
    raise ValueError(
        "Duplicate WORK_ID in feature dataset."
    )

if hybrid["WORK_ID"].duplicated().any():
    raise ValueError(
        "Duplicate WORK_ID in hybrid dataset."
    )


# ============================================================
# 3. KEEP INVESTIGATION CANDIDATES
# ============================================================

section("3. SELECTING INVESTIGATION CANDIDATES")

if "INVESTIGATION_CANDIDATE" not in hybrid.columns:
    raise ValueError(
        "INVESTIGATION_CANDIDATE missing from hybrid output."
    )


hybrid["INVESTIGATION_CANDIDATE"] = pd.to_numeric(
    hybrid["INVESTIGATION_CANDIDATE"],
    errors="coerce"
).fillna(0).astype(int)


candidates = hybrid[
    hybrid["INVESTIGATION_CANDIDATE"] == 1
].copy()


print(
    f"Investigation candidates : "
    f"{len(candidates):,}"
)


# ============================================================
# 4. MERGE FEATURE DATA
# ============================================================

section("4. ATTACHING FACTUAL WORK EVIDENCE")

# Avoid duplicate detector columns from features.
# Hybrid already contains detector outputs.

detector_columns = [
    "RULE_SCORE",
    "RULE_SEVERITY",
    "RULE_CANDIDATE",
    "STAT_SCORE",
    "STAT_SEVERITY",
    "STAT_CANDIDATE",
    "ML_PERCENTILE",
    "ML_SEVERITY",
    "ML_CANDIDATE",
    "HYBRID_RISK_SCORE",
    "HYBRID_RISK_LEVEL",
    "INVESTIGATION_PRIORITY",
    "INVESTIGATION_CANDIDATE",
    "INDEPENDENT_SIGNAL_COUNT",
    "DETECTOR_AGREEMENT",
]


# Hybrid is already the master table for identity,
# financial fields, and detector outputs.
#
# Only bring feature columns that do NOT already exist
# in the hybrid table. This prevents pandas from creating
# _x / _y duplicates for fields such as SANCTION_AMOUNT.

feature_columns = [
    "WORK_ID"
] + [
    c
    for c in features.columns
    if c != "WORK_ID"
    and c not in hybrid.columns
]


feature_data = features[feature_columns].copy()


evidence = candidates.merge(
    feature_data,
    on="WORK_ID",
    how="left",
    validate="one_to_one"
)


if len(evidence) != len(candidates):
    raise ValueError(
        "Evidence merge changed candidate row count."
    )


print(
    f"Evidence rows : {len(evidence):,}"
)


# ============================================================
# 5. COLUMN MAP
# ============================================================

section("5. DISCOVERING AVAILABLE EVIDENCE FIELDS")


# Identity
STATE_NAME = first_existing(
    evidence,
    ["STATE_NAME"]
)

CONSTITUENCY = first_existing(
    evidence,
    ["CONSTITUENCY"]
)

MP_NAME = first_existing(
    evidence,
    ["MP_NAME"]
)

WORK_CATEGORY = first_existing(
    evidence,
    ["WORK_CATEGORY"]
)

ACTIVITY_NAME = first_existing(
    evidence,
    ["ACTIVITY_NAME"]
)

WORK_DESCRIPTION = first_existing(
    evidence,
    ["WORK_DESCRIPTION"]
)

WORK_STAGE = first_existing(
    evidence,
    ["WORK_STAGE"]
)


# Financial
RECOMMENDED = first_existing(
    evidence,
    [
        "RECOMMENDED_AMOUNT",
        "RECOMMENDED_AMT",
    ]
)

SANCTION = first_existing(
    evidence,
    [
        "SANCTION_AMOUNT",
        "SANCTION_AMT",
    ]
)

ACTUAL = first_existing(
    evidence,
    [
        "ACTUAL_AMOUNT",
        "ACTUAL_AMT",
    ]
)

DISBURSED = first_existing(
    evidence,
    [
        "TOTAL_FUND_DISBURSED_AMT",
        "TOTAL_DISBURSED_AMOUNT",
        "DISBURSED_AMOUNT",
    ]
)


# Payment
PAYMENT_COUNT = first_existing(
    evidence,
    [
        "PAYMENT_COUNT",
        "TOTAL_PAYMENT_COUNT",
    ]
)

VENDOR_COUNT = first_existing(
    evidence,
    [
        "UNIQUE_VENDOR_COUNT",
        "VENDOR_COUNT",
    ]
)

SUCCESS_COUNT = first_existing(
    evidence,
    [
        "PAYMENT_SUCCESS_COUNT",
        "SUCCESSFUL_PAYMENT_COUNT",
    ]
)

IN_PROGRESS_COUNT = first_existing(
    evidence,
    [
        "PAYMENT_IN_PROGRESS_COUNT",
        "IN_PROGRESS_PAYMENT_COUNT",
    ]
)

PAYMENTS_PER_30 = first_existing(
    evidence,
    [
        "PAYMENTS_PER_30_DAYS",
    ]
)

PAYMENTS_PER_100 = first_existing(
    evidence,
    [
        "PAYMENTS_PER_100_DAYS",
    ]
)


# Timeline
RECOMMENDATION_DATE = first_existing(
    evidence,
    [
        "RECOMMENDATION_DATE",
    ]
)

SANCTION_DATE = first_existing(
    evidence,
    [
        "SANCTION_DATE",
    ]
)

FIRST_PAYMENT_DATE = first_existing(
    evidence,
    [
        "FIRST_PAYMENT_DATE",
    ]
)

LAST_PAYMENT_DATE = first_existing(
    evidence,
    [
        "LAST_PAYMENT_DATE",
    ]
)

COMPLETION_DATE = first_existing(
    evidence,
    [
        "COMPLETION_DATE",
        "ACTUAL_COMPLETION_DATE",
    ]
)

COMPLETION_DURATION = first_existing(
    evidence,
    [
        "COMPLETION_DURATION_DAYS",
    ]
)

PAYMENT_AFTER_COMPLETION = first_existing(
    evidence,
    [
        "PAYMENT_AFTER_REPORTED_COMPLETION_DAYS",
    ]
)

COMPLETION_BEFORE_PAYMENT = first_existing(
    evidence,
    [
        "COMPLETION_BEFORE_LAST_PAYMENT",
    ]
)


# Peer
PEER_COUNT = first_existing(
    evidence,
    [
        "PEER_COUNT",
    ]
)

PEER_MEDIAN = first_existing(
    evidence,
    [
        "PEER_MEDIAN_SANCTION",
    ]
)

PEER_MEAN = first_existing(
    evidence,
    [
        "PEER_MEAN_SANCTION",
    ]
)

PEER_Z = first_existing(
    evidence,
    [
        "SANCTION_PEER_Z_SCORE",
        "PEER_Z_SCORE",
    ]
)

SANCTION_TO_PEER = first_existing(
    evidence,
    [
        "SANCTION_TO_PEER_MEDIAN",
    ]
)


# Data quality
COMPLETENESS = first_existing(
    evidence,
    [
        "DATA_COMPLETENESS",
        "DATA_COMPLETENESS_SCORE",
    ]
)

MISSING_FIELDS = first_existing(
    evidence,
    [
        "MISSING_FIELD_COUNT",
        "MISSING_FIELDS_COUNT",
    ]
)

ATTACH_ID = first_existing(
    evidence,
    [
        "ATTACH_ID",
    ]
)

FILE_STATUS = first_existing(
    evidence,
    [
        "FILE_STATUS",
    ]
)


field_map = {
    "STATE_NAME": STATE_NAME,
    "CONSTITUENCY": CONSTITUENCY,
    "MP_NAME": MP_NAME,
    "WORK_CATEGORY": WORK_CATEGORY,
    "ACTIVITY_NAME": ACTIVITY_NAME,
    "WORK_DESCRIPTION": WORK_DESCRIPTION,
    "WORK_STAGE": WORK_STAGE,

    "RECOMMENDED_AMOUNT": RECOMMENDED,
    "SANCTION_AMOUNT": SANCTION,
    "ACTUAL_AMOUNT": ACTUAL,
    "DISBURSED_AMOUNT": DISBURSED,

    "PAYMENT_COUNT": PAYMENT_COUNT,
    "VENDOR_COUNT": VENDOR_COUNT,
    "SUCCESS_COUNT": SUCCESS_COUNT,
    "IN_PROGRESS_COUNT": IN_PROGRESS_COUNT,

    "PAYMENTS_PER_30_DAYS": PAYMENTS_PER_30,
    "PAYMENTS_PER_100_DAYS": PAYMENTS_PER_100,

    "RECOMMENDATION_DATE": RECOMMENDATION_DATE,
    "SANCTION_DATE": SANCTION_DATE,
    "FIRST_PAYMENT_DATE": FIRST_PAYMENT_DATE,
    "LAST_PAYMENT_DATE": LAST_PAYMENT_DATE,
    "COMPLETION_DATE": COMPLETION_DATE,
    "COMPLETION_DURATION_DAYS": COMPLETION_DURATION,

    "PAYMENT_AFTER_REPORTED_COMPLETION_DAYS":
        PAYMENT_AFTER_COMPLETION,

    "COMPLETION_BEFORE_LAST_PAYMENT":
        COMPLETION_BEFORE_PAYMENT,

    "PEER_COUNT": PEER_COUNT,
    "PEER_MEDIAN_SANCTION": PEER_MEDIAN,
    "PEER_MEAN_SANCTION": PEER_MEAN,
    "SANCTION_PEER_Z_SCORE": PEER_Z,
    "SANCTION_TO_PEER_MEDIAN": SANCTION_TO_PEER,

    "DATA_COMPLETENESS": COMPLETENESS,
    "MISSING_FIELD_COUNT": MISSING_FIELDS,
    "ATTACH_ID": ATTACH_ID,
    "FILE_STATUS": FILE_STATUS,
}


for label, column in field_map.items():

    if column is not None:
        print(
            f"{label:42s}: {column}"
        )


# ============================================================
# 6. CALCULATE BASIC FINANCIAL RATIOS
# ============================================================

section("6. CALCULATING FINANCIAL EVIDENCE")


def safe_ratio(a, b):

    a = pd.to_numeric(
        a,
        errors="coerce"
    )

    b = pd.to_numeric(
        b,
        errors="coerce"
    )

    return np.where(
        b > 0,
        a / b,
        np.nan
    )


if SANCTION and ACTUAL:

    evidence["ACTUAL_TO_SANCTION_RATIO"] = (
        safe_ratio(
            evidence[ACTUAL],
            evidence[SANCTION]
        )
    )


if SANCTION and DISBURSED:

    evidence["DISBURSED_TO_SANCTION_RATIO"] = (
        safe_ratio(
            evidence[DISBURSED],
            evidence[SANCTION]
        )
    )


if RECOMMENDED and SANCTION:

    evidence["RECOMMENDED_TO_SANCTION_RATIO"] = (
        safe_ratio(
            evidence[RECOMMENDED],
            evidence[SANCTION]
        )
    )


if SANCTION and PEER_MEDIAN:

    evidence["SANCTION_TO_PEER_MEDIAN_CALCULATED"] = (
        safe_ratio(
            evidence[SANCTION],
            evidence[PEER_MEDIAN]
        )
    )


# ============================================================
# 7. BUILD FACTUAL EVIDENCE
# ============================================================

section("7. BUILDING FACTUAL EVIDENCE")


def build_evidence(row):

    facts = []

    # --------------------------------------------------------
    # Financial
    # --------------------------------------------------------

    sanction = (
        clean_value(row[SANCTION])
        if SANCTION
        else None
    )

    actual = (
        clean_value(row[ACTUAL])
        if ACTUAL
        else None
    )

    disbursed = (
        clean_value(row[DISBURSED])
        if DISBURSED
        else None
    )

    recommended = (
        clean_value(row[RECOMMENDED])
        if RECOMMENDED
        else None
    )

    if recommended is not None:
        facts.append(
            f"Recommended amount: "
            f"{fmt_money(recommended)}."
        )

    if sanction is not None:
        facts.append(
            f"Sanction amount: "
            f"{fmt_money(sanction)}."
        )

    if actual is not None:
        facts.append(
            f"Reported actual expenditure: "
            f"{fmt_money(actual)}."
        )

    if disbursed is not None:
        facts.append(
            f"Recorded fund disbursement: "
            f"{fmt_money(disbursed)}."
        )

    if sanction is not None and actual is not None:

        ratio = clean_value(
            row.get(
                "ACTUAL_TO_SANCTION_RATIO",
                np.nan
            )
        )

        if ratio is not None:
            facts.append(
                f"Actual-to-sanction ratio: "
                f"{fmt_percent(ratio)}."
            )

    if sanction is not None and disbursed is not None:

        ratio = clean_value(
            row.get(
                "DISBURSED_TO_SANCTION_RATIO",
                np.nan
            )
        )

        if ratio is not None:
            facts.append(
                f"Disbursed-to-sanction ratio: "
                f"{fmt_percent(ratio)}."
            )


    # --------------------------------------------------------
    # Payment
    # --------------------------------------------------------

    payment_count = (
        clean_value(row[PAYMENT_COUNT])
        if PAYMENT_COUNT
        else None
    )

    vendor_count = (
        clean_value(row[VENDOR_COUNT])
        if VENDOR_COUNT
        else None
    )

    success_count = (
        clean_value(row[SUCCESS_COUNT])
        if SUCCESS_COUNT
        else None
    )

    in_progress = (
        clean_value(row[IN_PROGRESS_COUNT])
        if IN_PROGRESS_COUNT
        else None
    )

    if payment_count is not None:
        facts.append(
            f"Payment transaction count: "
            f"{fmt_number(payment_count)}."
        )

    if vendor_count is not None:
        facts.append(
            f"Unique vendor count: "
            f"{fmt_number(vendor_count)}."
        )

    if success_count is not None:
        facts.append(
            f"Successful payment count: "
            f"{fmt_number(success_count)}."
        )

    if in_progress is not None:
        facts.append(
            f"In-progress payment count: "
            f"{fmt_number(in_progress)}."
        )

    if PAYMENTS_PER_30:

        value = clean_value(
            row[PAYMENTS_PER_30]
        )

        if value is not None:
            facts.append(
                f"Payments per 30 days: "
                f"{fmt_number(value)}."
            )

    if PAYMENTS_PER_100:

        value = clean_value(
            row[PAYMENTS_PER_100]
        )

        if value is not None:
            facts.append(
                f"Payments per 100 days: "
                f"{fmt_number(value)}."
            )


    # --------------------------------------------------------
    # Timeline
    # --------------------------------------------------------

    if RECOMMENDATION_DATE:

        value = clean_value(
            row[RECOMMENDATION_DATE]
        )

        if value is not None:
            facts.append(
                f"Recommendation date: {value}."
            )

    if SANCTION_DATE:

        value = clean_value(
            row[SANCTION_DATE]
        )

        if value is not None:
            facts.append(
                f"Sanction date: {value}."
            )

    if FIRST_PAYMENT_DATE:

        value = clean_value(
            row[FIRST_PAYMENT_DATE]
        )

        if value is not None:
            facts.append(
                f"First recorded payment date: {value}."
            )

    if COMPLETION_DATE:

        value = clean_value(
            row[COMPLETION_DATE]
        )

        if value is not None:
            facts.append(
                f"Reported completion date: {value}."
            )

    if LAST_PAYMENT_DATE:

        value = clean_value(
            row[LAST_PAYMENT_DATE]
        )

        if value is not None:
            facts.append(
                f"Last recorded payment date: {value}."
            )

    if COMPLETION_DURATION:

        value = clean_value(
            row[COMPLETION_DURATION]
        )

        if value is not None:
            facts.append(
                f"Reported completion duration: "
                f"{fmt_days(value)}."
            )

    if PAYMENT_AFTER_COMPLETION:

        value = clean_value(
            row[PAYMENT_AFTER_COMPLETION]
        )

        if value is not None and float(value) > 0:

            facts.append(
                f"Recorded payment activity occurred "
                f"{fmt_days(value)} after reported completion."
            )


    # --------------------------------------------------------
    # Peer
    # --------------------------------------------------------

    peer_count = (
        clean_value(row[PEER_COUNT])
        if PEER_COUNT
        else None
    )

    peer_median = (
        clean_value(row[PEER_MEDIAN])
        if PEER_MEDIAN
        else None
    )

    peer_mean = (
        clean_value(row[PEER_MEAN])
        if PEER_MEAN
        else None
    )

    peer_z = (
        clean_value(row[PEER_Z])
        if PEER_Z
        else None
    )

    if peer_count is not None:

        facts.append(
            f"Peer-group size used by the feature set: "
            f"{fmt_number(peer_count)}."
        )

    # IMPORTANT:
    # Do not present peer comparisons as meaningful when
    # peer count is below the statistical minimum of 10.

    if (
        peer_count is not None
        and float(peer_count) >= 10
    ):

        if peer_median is not None:

            facts.append(
                f"Peer median sanction amount: "
                f"{fmt_money(peer_median)}."
            )

        if peer_mean is not None:

            facts.append(
                f"Peer mean sanction amount: "
                f"{fmt_money(peer_mean)}."
            )

        if peer_z is not None:

            facts.append(
                f"Sanction peer z-score: "
                f"{fmt_number(peer_z)}."
            )


    # --------------------------------------------------------
    # Data quality
    # --------------------------------------------------------

    completeness = (
        clean_value(row[COMPLETENESS])
        if COMPLETENESS
        else None
    )

    missing_fields = (
        clean_value(row[MISSING_FIELDS])
        if MISSING_FIELDS
        else None
    )

    if completeness is not None:

        facts.append(
            f"Recorded data completeness: "
            f"{fmt_percent(completeness)}."
        )

    if missing_fields is not None:

        facts.append(
            f"Missing-field count: "
            f"{fmt_number(missing_fields)}."
        )

    if ATTACH_ID:

        value = clean_value(
            row[ATTACH_ID]
        )

        if value is not None:
            facts.append(
                f"Attachment identifier is present."
            )
        else:
            facts.append(
                f"Attachment identifier is not present "
                f"in the available record."
            )

    if FILE_STATUS:

        value = clean_value(
            row[FILE_STATUS]
        )

        if value is not None:
            facts.append(
                f"File status: {value}."
            )


    return " ".join(facts)


evidence["FACTUAL_EVIDENCE"] = evidence.apply(
    build_evidence,
    axis=1
)


# ============================================================
# 8. BUILD VERIFICATION FLAGS
# ============================================================

section("8. BUILDING VERIFICATION FLAGS")


def build_verification(row):

    flags = []

    # --------------------------------------------------------
    # Payment behavior
    # --------------------------------------------------------

    payment_count = (
        clean_value(row[PAYMENT_COUNT])
        if PAYMENT_COUNT
        else None
    )

    vendor_count = (
        clean_value(row[VENDOR_COUNT])
        if VENDOR_COUNT
        else None
    )

    if payment_count is not None:

        if float(payment_count) >= 5:

            flags.append(
                "Verify the individual payment transactions "
                "and supporting payment records."
            )

    if vendor_count is not None:

        if float(vendor_count) >= 5:

            flags.append(
                "Verify vendor identities, work orders, "
                "and supporting procurement records."
            )


    # --------------------------------------------------------
    # Timeline
    # --------------------------------------------------------

    after_completion = (
        clean_value(row[PAYMENT_AFTER_COMPLETION])
        if PAYMENT_AFTER_COMPLETION
        else None
    )

    if (
        after_completion is not None
        and float(after_completion) > 0
    ):

        flags.append(
            "Verify the reported completion date against "
            "payment and measurement records."
        )


    # --------------------------------------------------------
    # Financial
    # --------------------------------------------------------

    actual_ratio = clean_value(
        row.get(
            "ACTUAL_TO_SANCTION_RATIO",
            np.nan
        )
    )

    disbursed_ratio = clean_value(
        row.get(
            "DISBURSED_TO_SANCTION_RATIO",
            np.nan
        )
    )

    if (
        actual_ratio is not None
        and float(actual_ratio) > 1
    ):

        flags.append(
            "Verify reported actual expenditure against "
            "the sanctioned amount."
        )

    if (
        disbursed_ratio is not None
        and float(disbursed_ratio) > 1
    ):

        flags.append(
            "Verify recorded disbursement against "
            "the sanctioned amount."
        )


    # --------------------------------------------------------
    # Peer
    # --------------------------------------------------------

    peer_count = (
        clean_value(row[PEER_COUNT])
        if PEER_COUNT
        else None
    )

    if (
        peer_count is not None
        and float(peer_count) < 10
    ):

        flags.append(
            "Peer comparison is weak because fewer than "
            "10 comparable works are available."
        )


    # --------------------------------------------------------
    # Data completeness
    # --------------------------------------------------------

    completeness = (
        clean_value(row[COMPLETENESS])
        if COMPLETENESS
        else None
    )

    if (
        completeness is not None
        and float(completeness) < 0.60
    ):

        flags.append(
            "Verify missing source fields before drawing "
            "strong conclusions from this record."
        )


    # --------------------------------------------------------
    # Always keep investigation human-led
    # --------------------------------------------------------

    flags.append(
        "Confirm findings against original government "
        "records and supporting documents."
    )


    # Remove duplicates while preserving order.

    unique_flags = []

    for flag in flags:

        if flag not in unique_flags:
            unique_flags.append(flag)


    return " ".join(
        f"{i + 1}. {flag}"
        for i, flag in enumerate(unique_flags)
    )


evidence["VERIFICATION_FLAGS"] = evidence.apply(
    build_verification,
    axis=1
)


# ============================================================
# 9. DETECTOR EVIDENCE
# ============================================================

section("9. BUILDING DETECTOR EVIDENCE")


def build_detector_summary(row):

    parts = []

    rule_candidate = int(
        row.get(
            "RULE_CANDIDATE",
            0
        )
        or 0
    )

    stat_candidate = int(
        row.get(
            "STAT_CANDIDATE",
            0
        )
        or 0
    )

    ml_candidate = int(
        row.get(
            "ML_CANDIDATE",
            0
        )
        or 0
    )

    if rule_candidate:

        parts.append(
            "Rule detector produced a candidate signal"
        )

        rule_score = row.get(
            "RULE_SCORE",
            np.nan
        )

        if pd.notna(rule_score):

            parts[-1] += (
                f" with score "
                f"{float(rule_score):.1f}"
            )


    if stat_candidate:

        parts.append(
            "Statistical detector produced a candidate signal"
        )

        stat_score = row.get(
            "STAT_SCORE",
            np.nan
        )

        if pd.notna(stat_score):

            parts[-1] += (
                f" with score "
                f"{float(stat_score):.1f}"
            )


    if ml_candidate:

        parts.append(
            "Isolation Forest produced an ML anomaly signal"
        )

        ml_percentile = row.get(
            "ML_PERCENTILE",
            np.nan
        )

        if pd.notna(ml_percentile):

            parts[-1] += (
                f" at the "
                f"{float(ml_percentile):.2f}th percentile"
            )


    if not parts:

        return "No detector signal."

    return "; ".join(parts) + "."


evidence["DETECTOR_EVIDENCE"] = evidence.apply(
    build_detector_summary,
    axis=1
)


# ============================================================
# 10. INVESTIGATION SUMMARY
# ============================================================

section("10. BUILDING INVESTIGATION SUMMARY")


def build_summary(row):

    identity = []

    if STATE_NAME:
        value = clean_value(row[STATE_NAME])
        if value is not None:
            identity.append(str(value))

    if CONSTITUENCY:
        value = clean_value(row[CONSTITUENCY])
        if value is not None:
            identity.append(str(value))

    if MP_NAME:
        value = clean_value(row[MP_NAME])
        if value is not None:
            identity.append(
                f"MP: {value}"
            )

    location = " | ".join(identity)

    score = clean_value(
        row.get(
            "HYBRID_RISK_SCORE",
            np.nan
        )
    )

    level = clean_value(
        row.get(
            "HYBRID_RISK_LEVEL",
            "NONE"
        )
    )

    agreement = clean_value(
        row.get(
            "DETECTOR_AGREEMENT",
            "UNKNOWN"
        )
    )

    if location:
        start = f"{location}. "
    else:
        start = ""

    return (
        f"{start}"
        f"Hybrid risk level: {level}; "
        f"hybrid score: {fmt_number(score)}; "
        f"detector agreement: {agreement}. "
        f"This record is an investigation candidate "
        f"requiring verification, not a finding of fraud "
        f"or corruption."
    )


evidence["INVESTIGATION_SUMMARY"] = evidence.apply(
    build_summary,
    axis=1
)


# ============================================================
# 11. FINAL QUEUE
# ============================================================

section("11. BUILDING FINAL INVESTIGATION QUEUE")


final_columns = [
    # Identity
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

    # Financial
    "RECOMMENDED_AMOUNT",
    "SANCTION_AMOUNT",
    "ACTUAL_AMOUNT",
    "TOTAL_FUND_DISBURSED_AMT",

    "ACTUAL_TO_SANCTION_RATIO",
    "DISBURSED_TO_SANCTION_RATIO",
    "RECOMMENDED_TO_SANCTION_RATIO",

    # Payments
    "PAYMENT_COUNT",
    "UNIQUE_VENDOR_COUNT",
    "PAYMENT_SUCCESS_COUNT",
    "PAYMENT_IN_PROGRESS_COUNT",
    "PAYMENTS_PER_30_DAYS",
    "PAYMENTS_PER_100_DAYS",

    # Timeline
    "RECOMMENDATION_DATE",
    "SANCTION_DATE",
    "FIRST_PAYMENT_DATE",
    "LAST_PAYMENT_DATE",
    "COMPLETION_DATE",
    "COMPLETION_DURATION_DAYS",
    "PAYMENT_AFTER_REPORTED_COMPLETION_DAYS",
    "COMPLETION_BEFORE_LAST_PAYMENT",

    # Peer
    "PEER_COUNT",
    "PEER_MEDIAN_SANCTION",
    "PEER_MEAN_SANCTION",
    "SANCTION_PEER_Z_SCORE",
    "SANCTION_TO_PEER_MEDIAN",

    # Data quality
    "DATA_COMPLETENESS",
    "MISSING_FIELD_COUNT",
    "ATTACH_ID",
    "FILE_STATUS",

    # Detector
    "RULE_CANDIDATE",
    "RULE_SCORE",
    "RULE_SEVERITY",

    "STAT_CANDIDATE",
    "STAT_SCORE",
    "STAT_SEVERITY",

    "ML_CANDIDATE",
    "ML_PERCENTILE",
    "ML_SEVERITY",

    "INDEPENDENT_SIGNAL_COUNT",
    "DETECTOR_AGREEMENT",

    # Hybrid
    "HYBRID_RISK_SCORE",
    "HYBRID_RISK_LEVEL",
    "INVESTIGATION_PRIORITY",
    "INVESTIGATION_CANDIDATE",
    "PEER_DATA_SUFFICIENT",
    "SCORE_REGIME",
    "DATA_QUALITY_TIER",

    # Evidence
    "DETECTOR_EVIDENCE",
    "FACTUAL_EVIDENCE",
    "VERIFICATION_FLAGS",
    "INVESTIGATION_SUMMARY",
]


final_columns = [
    c
    for c in final_columns
    if c in evidence.columns
]


queue = evidence[
    final_columns
].copy()


# ============================================================
# 12. SORT
# ============================================================

priority_order = {
    "P1": 1,
    "P2": 2,
    "P3": 3,
    "P4": 4,
}


queue["_PRIORITY"] = (
    queue[
        "INVESTIGATION_PRIORITY"
    ].map(priority_order)
)


queue = queue.sort_values(
    [
        "_PRIORITY",
        "HYBRID_RISK_SCORE",
    ],
    ascending=[
        True,
        False,
    ]
)


queue = queue.drop(
    columns=["_PRIORITY"]
)


# ============================================================
# 13. SAVE
# ============================================================

section("12. SAVING INVESTIGATION QUEUE")


queue.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    f"Saved: {OUTPUT_FILE}"
)

print(
    f"Rows : {len(queue):,}"
)

print(
    f"Columns : {len(queue.columns):,}"
)


# ============================================================
# 14. SUMMARY
# ============================================================

section("13. EVIDENCE BUILDER SUMMARY")


print(
    f"Investigation candidates : "
    f"{len(queue):,}"
)


print()

print(
    "Risk levels:"
)

print(
    queue[
        "HYBRID_RISK_LEVEL"
    ]
    .value_counts()
    .to_string()
)


print()

print(
    "Detector agreement:"
)

print(
    queue[
        "DETECTOR_AGREEMENT"
    ]
    .value_counts()
    .to_string()
)


# ============================================================
# 15. SAMPLE EVIDENCE
# ============================================================

section("14. SAMPLE INVESTIGATION EVIDENCE")


sample = queue.head(5)


for _, row in sample.iterrows():

    print()
    print(
        f"WORK_ID: {row['WORK_ID']}"
    )

    print(
        f"Risk: "
        f"{row.get('HYBRID_RISK_LEVEL', 'N/A')} "
        f"| Score: "
        f"{row.get('HYBRID_RISK_SCORE', 'N/A')}"
    )

    print(
        f"Agreement: "
        f"{row.get('DETECTOR_AGREEMENT', 'N/A')}"
    )

    print()

    print(
        "Detector evidence:"
    )

    print(
        row.get(
            "DETECTOR_EVIDENCE",
            ""
        )
    )

    print()

    print(
        "Factual evidence:"
    )

    print(
        row.get(
            "FACTUAL_EVIDENCE",
            ""
        )
    )

    print()

    print(
        "Verification:"
    )

    print(
        row.get(
            "VERIFICATION_FLAGS",
            ""
        )
    )


# ============================================================
# DONE
# ============================================================

section("EVIDENCE BUILDER COMPLETE")

print(
    "Hybrid risk        : READY"
)

print(
    "Factual evidence   : READY"
)

print(
    "Verification flags : READY"
)

print(
    "Investigation queue: READY"
)

print()

print(
    "The queue identifies records for human investigation."
)

print(
    "It does not establish fraud, corruption, or guilt."
)