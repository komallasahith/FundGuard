import os
import json
import numpy as np
import pandas as pd


# ============================================================
# CONFIG
# ============================================================

RISK_FILE = "data/outputs/fundguard_risk_results.csv"
FEATURE_FILE = "data/processed/mplads_features.csv"

OUTPUT_DIR = "data/outputs"

CSV_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "fundguard_evidence.csv"
)

JSON_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "fundguard_evidence.json"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.exists(RISK_FILE):
        raise FileNotFoundError(
            f"Risk file not found:\n{RISK_FILE}"
        )

    if not os.path.exists(FEATURE_FILE):
        raise FileNotFoundError(
            f"Feature file not found:\n{FEATURE_FILE}"
        )

    risk_df = pd.read_csv(RISK_FILE)
    feature_df = pd.read_csv(FEATURE_FILE)

    key = "WORK_RECOMMENDATION_DTL_ID"

    if key not in risk_df.columns:
        raise ValueError(
            f"{key} missing from risk results"
        )

    if key not in feature_df.columns:
        raise ValueError(
            f"{key} missing from feature dataset"
        )

    print("=" * 70)
    print("FUNDGUARD EVIDENCE BUILDER")
    print("=" * 70)

    print(
        f"Risk rows       : {len(risk_df):,}"
    )

    print(
        f"Feature rows    : {len(feature_df):,}"
    )

    # --------------------------------------------------------
    # Select original feature information
    # --------------------------------------------------------

    feature_columns = [
        key,

        "MP_NAME",
        "CONSTITUENCY_NAME",
        "WORK_CATEGORY",
        "ACTIVITY_NAME",

        "RECOMMENDED_AMOUNT",
        "SANCTION_AMOUNT",
        "ACTUAL_AMOUNT",

        "COST_VS_PEER_MEDIAN",
        "COST_VS_PEER_Z",

        "TRANSACTION_COUNT",
        "VENDOR_COUNT",

        "MAX_TRANSACTION_AMOUNT",
        "MIN_TRANSACTION_AMOUNT",

        "RECOMMENDATION_DATE",
        "SANCTION_DATE",
        "COMPLETION_DATE",

        "DAYS_RECOMMENDATION_TO_SANCTION",
        "DAYS_SANCTION_TO_COMPLETION",
        "DAYS_RECOMMENDATION_TO_COMPLETION"
    ]

    feature_columns = [
        c
        for c in feature_columns
        if c in feature_df.columns
    ]

    feature_df = feature_df[
        feature_columns
    ].copy()

    # --------------------------------------------------------
    # Ensure one row per work
    # --------------------------------------------------------

    if feature_df[key].duplicated().any():

        duplicate_count = (
            feature_df[key].duplicated().sum()
        )

        raise ValueError(
            f"Feature dataset contains "
            f"{duplicate_count:,} duplicate work IDs."
        )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    df = risk_df.merge(
        feature_df,
        on=key,
        how="left",
        suffixes=("", "_FEATURE")
    )

    print(
        f"Merged rows     : {len(df):,}"
    )

    # --------------------------------------------------------
    # Verify important columns
    # --------------------------------------------------------

    important = [
        "MP_NAME",
        "SANCTION_AMOUNT",
        "COST_VS_PEER_MEDIAN"
    ]

    print("\nEvidence source verification:")

    for column in important:

        if column in df.columns:

            available = (
                df[column].notna().sum()
            )

            print(
                f"  {column:<30}: "
                f"{available:,} available"
            )

        else:

            print(
                f"  {column:<30}: MISSING"
            )

    return df


# ============================================================
# HELPERS
# ============================================================

def value(row, column, default=None):

    if column not in row.index:
        return default

    result = row[column]

    if pd.isna(result):
        return default

    return result


def number(row, column):

    result = value(
        row,
        column
    )

    if result is None:
        return None

    try:
        return float(result)

    except (
        ValueError,
        TypeError
    ):
        return None


# ============================================================
# BUILD EVIDENCE RECORD
# ============================================================

def build_evidence_record(row):

    key = "WORK_RECOMMENDATION_DTL_ID"

    work_id = value(
        row,
        key
    )

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    mp_name = value(
        row,
        "MP_NAME",
        "Unknown"
    )

    constituency = value(
        row,
        "CONSTITUENCY_NAME",
        "Unknown"
    )

    work_category = value(
        row,
        "WORK_CATEGORY",
        "Unknown"
    )

    activity = value(
        row,
        "ACTIVITY_NAME",
        "Unknown"
    )

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    hybrid_score = number(
        row,
        "HYBRID_RISK_SCORE"
    )

    final_risk = value(
        row,
        "FINAL_RISK_LEVEL",
        "LOW"
    )

    agreement = value(
        row,
        "DETECTOR_AGREEMENT",
        "NONE"
    )

    agreement_count = number(
        row,
        "DETECTOR_AGREEMENT_COUNT"
    )

    priority = value(
        row,
        "INVESTIGATION_PRIORITY"
    )

    # --------------------------------------------------------
    # Detector scores
    # --------------------------------------------------------

    rule_score = number(
        row,
        "RULE_SCORE"
    )

    statistical_score = number(
        row,
        "STATISTICAL_SCORE"
    )

    ml_score = number(
        row,
        "ISOLATION_FOREST_SCORE"
    )

    # --------------------------------------------------------
    # Financial
    # --------------------------------------------------------

    recommended = number(
        row,
        "RECOMMENDED_AMOUNT"
    )

    sanctioned = number(
        row,
        "SANCTION_AMOUNT"
    )

    actual = number(
        row,
        "ACTUAL_AMOUNT"
    )

    cost_ratio = number(
        row,
        "COST_VS_PEER_MEDIAN"
    )

    peer_z = number(
        row,
        "COST_VS_PEER_Z"
    )

    # --------------------------------------------------------
    # Transactions
    # --------------------------------------------------------

    transaction_count = number(
        row,
        "TRANSACTION_COUNT"
    )

    vendor_count = number(
        row,
        "VENDOR_COUNT"
    )

    max_transaction = number(
        row,
        "MAX_TRANSACTION_AMOUNT"
    )

    # --------------------------------------------------------
    # Timeline
    # --------------------------------------------------------

    recommendation_date = value(
        row,
        "RECOMMENDATION_DATE"
    )

    sanction_date = value(
        row,
        "SANCTION_DATE"
    )

    completion_date = value(
        row,
        "COMPLETION_DATE"
    )

    recommendation_to_sanction = number(
        row,
        "DAYS_RECOMMENDATION_TO_SANCTION"
    )

    sanction_to_completion = number(
        row,
        "DAYS_SANCTION_TO_COMPLETION"
    )

    # ========================================================
    # EVIDENCE ARRAYS
    # ========================================================

    financial_evidence = []
    statistical_evidence = []
    transaction_evidence = []
    timeline_evidence = []

    # ========================================================
    # FINANCIAL EVIDENCE
    # ========================================================

    if (
        actual is not None
        and sanctioned is not None
        and actual > sanctioned
    ):

        financial_evidence.append({
            "type": "actual_exceeds_sanction",
            "severity": "high",
            "finding": (
                "Actual expenditure exceeds "
                "the sanctioned amount"
            ),
            "actual_amount": actual,
            "sanction_amount": sanctioned
        })

    # --------------------------------------------------------

    disbursed = number(
        row,
        "TOTAL_DISBURSED_AMOUNT"
    )

    if (
        disbursed is not None
        and sanctioned is not None
        and disbursed > sanctioned
    ):

        financial_evidence.append({
            "type": "disbursement_exceeds_sanction",
            "severity": "high",
            "finding": (
                "Disbursement exceeds "
                "the sanctioned amount"
            ),
            "disbursed_amount": disbursed,
            "sanction_amount": sanctioned
        })

    # --------------------------------------------------------
    # Peer cost
    # --------------------------------------------------------

    if cost_ratio is not None:

        if cost_ratio >= 10:

            financial_evidence.append({
                "type": "extreme_peer_cost",
                "severity": "high",
                "finding": (
                    "Sanctioned cost is at least "
                    "10x the peer-group median"
                ),
                "ratio": cost_ratio
            })

        elif cost_ratio >= 5:

            financial_evidence.append({
                "type": "extreme_peer_cost",
                "severity": "high",
                "finding": (
                    "Sanctioned cost is at least "
                    "5x the peer-group median"
                ),
                "ratio": cost_ratio
            })

        elif cost_ratio >= 2:

            financial_evidence.append({
                "type": "high_peer_cost",
                "severity": "medium",
                "finding": (
                    "Sanctioned cost is at least "
                    "2x the peer-group median"
                ),
                "ratio": cost_ratio
            })

    # ========================================================
    # STATISTICAL EVIDENCE
    # ========================================================

    if peer_z is not None:

        if peer_z >= 10:

            statistical_evidence.append({
                "type": "extreme_z_score",
                "severity": "high",
                "finding": (
                    "Cost is an extreme statistical "
                    "outlier within the peer distribution"
                ),
                "z_score": peer_z
            })

        elif peer_z >= 5:

            statistical_evidence.append({
                "type": "extreme_z_score",
                "severity": "high",
                "finding": (
                    "Cost is more than 5 standard "
                    "deviations above the peer distribution"
                ),
                "z_score": peer_z
            })

        elif peer_z >= 3:

            statistical_evidence.append({
                "type": "high_z_score",
                "severity": "medium",
                "finding": (
                    "Cost is more than 3 standard "
                    "deviations above the peer distribution"
                ),
                "z_score": peer_z
            })

    # ========================================================
    # TRANSACTION EVIDENCE
    # ========================================================

    if (
        vendor_count is not None
        and vendor_count > 1
    ):

        transaction_evidence.append({
            "type": "multiple_vendors",
            "severity": "medium",
            "finding": (
                "Multiple vendors are associated "
                "with this work"
            ),
            "vendor_count": int(
                vendor_count
            )
        })

    if (
        transaction_count is not None
        and transaction_count >= 4
    ):

        transaction_evidence.append({
            "type": "high_transaction_count",
            "severity": "medium",
            "finding": (
                "Work contains multiple "
                "expenditure transactions"
            ),
            "transaction_count": int(
                transaction_count
            )
        })

    elif (
        transaction_count is not None
        and transaction_count >= 2
    ):

        transaction_evidence.append({
            "type": "multiple_transactions",
            "severity": "low",
            "finding": (
                "Work contains multiple "
                "expenditure transactions"
            ),
            "transaction_count": int(
                transaction_count
            )
        })

    # ========================================================
    # TIMELINE EVIDENCE
    # ========================================================

    if (
        recommendation_date is not None
        and sanction_date is not None
    ):

        timeline_evidence.append({
            "type": "recommendation_to_sanction",
            "severity": "info",
            "finding": (
                "Recommendation and sanction "
                "dates are available"
            ),
            "recommendation_date": recommendation_date,
            "sanction_date": sanction_date,
            "days": recommendation_to_sanction
        })

    if (
        sanction_date is not None
        and completion_date is not None
    ):

        timeline_evidence.append({
            "type": "sanction_to_completion",
            "severity": "info",
            "finding": (
                "Sanction and completion "
                "dates are available"
            ),
            "sanction_date": sanction_date,
            "completion_date": completion_date,
            "days": sanction_to_completion
        })

    # ========================================================
    # BUILD SUMMARY
    # ========================================================

    summary_parts = []

    if (
        cost_ratio is not None
        and cost_ratio >= 2
    ):

        summary_parts.append(
            f"sanctioned cost is "
            f"{cost_ratio:.2f}x the peer median"
        )

    if (
        peer_z is not None
        and peer_z >= 3
    ):

        summary_parts.append(
            f"peer-group z-score is "
            f"{peer_z:.2f}"
        )

    if (
        actual is not None
        and sanctioned is not None
        and actual > sanctioned
    ):

        summary_parts.append(
            "actual expenditure exceeds sanction"
        )

    if (
        disbursed is not None
        and sanctioned is not None
        and disbursed > sanctioned
    ):

        summary_parts.append(
            "disbursement exceeds sanction"
        )

    if (
        vendor_count is not None
        and vendor_count > 1
    ):

        summary_parts.append(
            f"{int(vendor_count)} vendors recorded"
        )

    if (
        transaction_count is not None
        and transaction_count >= 2
    ):

        summary_parts.append(
            f"{int(transaction_count)} "
            "expenditure transactions"
        )

    if summary_parts:

        summary = (
            "The work shows "
            + "; ".join(summary_parts)
            + "."
        )

    else:

        summary = (
            "No major evidence signals were identified."
        )

    # ========================================================
    # GUIDANCE
    # ========================================================

    if final_risk == "CRITICAL":

        guidance = (
            "Prioritize for detailed review. "
            "Validate sanction, estimate, expenditure, "
            "vendor and implementation records."
        )

    elif final_risk == "HIGH":

        guidance = (
            "Prioritize for investigation and "
            "cross-check the underlying financial "
            "and implementation records."
        )

    elif final_risk == "MEDIUM":

        guidance = (
            "Review supporting records and monitor "
            "for additional anomaly signals."
        )

    else:

        guidance = (
            "No immediate investigation priority "
            "based on current detection signals."
        )

    # ========================================================
    # FINAL RECORD
    # ========================================================

    return {

        "work_id": work_id,

        "identity": {
            "mp_name": mp_name,
            "constituency": constituency,
            "work_category": work_category,
            "activity_name": activity
        },

        "risk": {
            "hybrid_score": hybrid_score,
            "risk_level": final_risk,
            "detector_agreement": agreement,
            "detector_agreement_count": (
                int(agreement_count)
                if agreement_count is not None
                else 0
            ),
            "investigation_priority": priority
        },

        "detector_scores": {
            "rule": rule_score,
            "statistical": statistical_score,
            "isolation_forest": ml_score
        },

        "financial": {
            "recommended_amount": recommended,
            "sanction_amount": sanctioned,
            "actual_amount": actual,
            "disbursed_amount": disbursed,
            "cost_vs_peer_median": cost_ratio
        },

        "statistical": {
            "peer_z_score": peer_z
        },

        "transactions": {
            "transaction_count": (
                int(transaction_count)
                if transaction_count is not None
                else None
            ),
            "vendor_count": (
                int(vendor_count)
                if vendor_count is not None
                else None
            ),
            "max_transaction_amount": max_transaction
        },

        "timeline": {
            "recommendation_date": recommendation_date,
            "sanction_date": sanction_date,
            "completion_date": completion_date,
            "days_recommendation_to_sanction": (
                recommendation_to_sanction
            ),
            "days_sanction_to_completion": (
                sanction_to_completion
            )
        },

        "evidence": {
            "financial": financial_evidence,
            "statistical": statistical_evidence,
            "transaction": transaction_evidence,
            "timeline": timeline_evidence
        },

        "summary": summary,

        "investigation_guidance": guidance,

        "disclaimer": (
            "This system identifies anomaly/risk "
            "candidates for investigation. It does "
            "not establish fraud or wrongdoing."
        )
    }


# ============================================================
# BUILD ALL
# ============================================================

def build_all(df):

    records = []

    print("\nBuilding structured evidence...")

    for _, row in df.iterrows():

        records.append(
            build_evidence_record(row)
        )

    print(
        f"Evidence records created: "
        f"{len(records):,}"
    )

    return records


# ============================================================
# FLATTEN JSON → CSV
# ============================================================

def flatten_record(record):

    return {

        "WORK_ID": record["work_id"],

        "MP_NAME": record["identity"]["mp_name"],

        "CONSTITUENCY_NAME": (
            record["identity"]["constituency"]
        ),

        "WORK_CATEGORY": (
            record["identity"]["work_category"]
        ),

        "ACTIVITY_NAME": (
            record["identity"]["activity_name"]
        ),

        "HYBRID_RISK_SCORE": (
            record["risk"]["hybrid_score"]
        ),

        "FINAL_RISK_LEVEL": (
            record["risk"]["risk_level"]
        ),

        "DETECTOR_AGREEMENT": (
            record["risk"]["detector_agreement"]
        ),

        "DETECTOR_AGREEMENT_COUNT": (
            record["risk"]["detector_agreement_count"]
        ),

        "INVESTIGATION_PRIORITY": (
            record["risk"]["investigation_priority"]
        ),

        "RULE_SCORE": (
            record["detector_scores"]["rule"]
        ),

        "STATISTICAL_SCORE": (
            record["detector_scores"]["statistical"]
        ),

        "ISOLATION_FOREST_SCORE": (
            record["detector_scores"]["isolation_forest"]
        ),

        "RECOMMENDED_AMOUNT": (
            record["financial"]["recommended_amount"]
        ),

        "SANCTION_AMOUNT": (
            record["financial"]["sanction_amount"]
        ),

        "ACTUAL_AMOUNT": (
            record["financial"]["actual_amount"]
        ),

        "DISBURSED_AMOUNT": (
            record["financial"]["disbursed_amount"]
        ),

        "COST_VS_PEER_MEDIAN": (
            record["financial"]["cost_vs_peer_median"]
        ),

        "PEER_Z_SCORE": (
            record["statistical"]["peer_z_score"]
        ),

        "TRANSACTION_COUNT": (
            record["transactions"]["transaction_count"]
        ),

        "VENDOR_COUNT": (
            record["transactions"]["vendor_count"]
        ),

        "MAX_TRANSACTION_AMOUNT": (
            record["transactions"]["max_transaction_amount"]
        ),

        "RECOMMENDATION_DATE": (
            record["timeline"]["recommendation_date"]
        ),

        "SANCTION_DATE": (
            record["timeline"]["sanction_date"]
        ),

        "COMPLETION_DATE": (
            record["timeline"]["completion_date"]
        ),

        "DAYS_RECOMMENDATION_TO_SANCTION": (
            record["timeline"][
                "days_recommendation_to_sanction"
            ]
        ),

        "DAYS_SANCTION_TO_COMPLETION": (
            record["timeline"][
                "days_sanction_to_completion"
            ]
        ),

        "SUMMARY": record["summary"],

        "INVESTIGATION_GUIDANCE": (
            record["investigation_guidance"]
        ),

        "DISCLAIMER": record["disclaimer"],

        "FINANCIAL_EVIDENCE": json.dumps(
            record["evidence"]["financial"],
            ensure_ascii=False
        ),

        "STATISTICAL_EVIDENCE": json.dumps(
            record["evidence"]["statistical"],
            ensure_ascii=False
        ),

        "TRANSACTION_EVIDENCE": json.dumps(
            record["evidence"]["transaction"],
            ensure_ascii=False
        ),

        "TIMELINE_EVIDENCE": json.dumps(
            record["evidence"]["timeline"],
            ensure_ascii=False
        )
    }


# ============================================================
# SAVE
# ============================================================

def save_outputs(records):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    # JSON
    with open(
        JSON_OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False,
            allow_nan=False
        )

    # CSV
    flattened = [
        flatten_record(record)
        for record in records
    ]

    evidence_df = pd.DataFrame(
        flattened
    )

    evidence_df.to_csv(
        CSV_OUTPUT,
        index=False
    )

    print("\n" + "=" * 70)
    print("EVIDENCE OUTPUT")
    print("=" * 70)

    print(
        f"CSV  : {CSV_OUTPUT}"
    )

    print(
        f"JSON : {JSON_OUTPUT}"
    )

    print(
        f"Rows : {len(evidence_df):,}"
    )


# ============================================================
# SHOW TOP RESULTS
# ============================================================

def show_top(records):

    print("\n" + "=" * 70)
    print("TOP EVIDENCE RECORDS")
    print("=" * 70)

    for record in records[:10]:

        print("\n" + "-" * 70)

        print(
            f"Work ID    : {record['work_id']}"
        )

        print(
            f"MP         : "
            f"{record['identity']['mp_name']}"
        )

        print(
            f"Constituency: "
            f"{record['identity']['constituency']}"
        )

        print(
            f"Risk Score : "
            f"{record['risk']['hybrid_score']}"
        )

        print(
            f"Risk Level : "
            f"{record['risk']['risk_level']}"
        )

        print(
            f"Agreement  : "
            f"{record['risk']['detector_agreement']}"
        )

        print(
            f"Summary    : "
            f"{record['summary']}"
        )

        print(
            f"Guidance   : "
            f"{record['investigation_guidance']}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    df = load_data()

    records = build_all(
        df
    )

    save_outputs(
        records
    )

    show_top(
        records
    )

    print(
        "\nEvidence builder completed successfully."
    )


if __name__ == "__main__":
    main()