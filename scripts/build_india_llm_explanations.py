import os
import json
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

QUEUE_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_investigation_queue.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_llm_explanations.csv"
)

CACHE_FILE = (
    BASE_DIR
    / "data"
    / "outputs"
    / "india_llm_explanations_cache.json"
)

API_URL = (
    "https://api.groq.com/openai/v1/chat/completions"
)

MODEL = "openai/gpt-oss-120b"

# ============================================================
# SELECTIVE LLM REASONING
# ============================================================
#
# FundGuard does NOT depend on the LLM.
#
# All investigation candidates are detected deterministically.
# LLM is only an optional reasoning layer for representative
# high-priority cases.
#
# Maximum new case-level calls:
#
#   50 CRITICAL
#   30 HIGH
#   20 MEDIUM
#   ----------------
#   100 TOTAL
#
# LOW cases are not sent to the LLM.
# ============================================================

MAX_LLM_WORKS = 100

CRITICAL_LIMIT = 50
HIGH_LIMIT = 30
MEDIUM_LIMIT = 20

REQUEST_TIMEOUT = 60
MAX_RETRIES = 2


# ============================================================
# HELPERS
# ============================================================


def get_value(row, column, default="Not available"):

    if column not in row.index:
        return default

    value = row[column]

    if pd.isna(value):
        return default

    return value


def money(value):

    if pd.isna(value):
        return "Not available"

    try:
        return f"₹{float(value):,.0f}"
    except Exception:
        return str(value)


def number(value):

    if pd.isna(value):
        return "Not available"

    try:
        return round(float(value), 3)
    except Exception:
        return value


def clean_json(text):

    text = text.strip()

    if text.startswith("```"):

        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end > start:
        return text[start:end + 1]

    return text


# ============================================================
# COMPACT EVIDENCE
# ============================================================


def build_evidence(row):

    return {

        "work_id": str(
            get_value(row, "WORK_ID")
        ),

        "state": get_value(
            row,
            "STATE_NAME"
        ),

        "constituency": get_value(
            row,
            "CONSTITUENCY"
        ),

        "work_category": get_value(
            row,
            "WORK_CATEGORY"
        ),

        "activity": get_value(
            row,
            "ACTIVITY_NAME"
        ),

        "description": get_value(
            row,
            "WORK_DESCRIPTION"
        ),

        "work_stage": get_value(
            row,
            "WORK_STAGE"
        ),

        # Hybrid
        "risk_level": get_value(
            row,
            "HYBRID_RISK_LEVEL"
        ),

        "risk_score": number(
            get_value(
                row,
                "HYBRID_RISK_SCORE"
            )
        ),

        "priority": get_value(
            row,
            "INVESTIGATION_PRIORITY"
        ),

        "independent_signals": number(
            get_value(
                row,
                "INDEPENDENT_SIGNAL_COUNT"
            )
        ),

        "detector_agreement": get_value(
            row,
            "DETECTOR_AGREEMENT"
        ),

        # Financial
        "sanction": money(
            get_value(
                row,
                "SANCTION_AMOUNT"
            )
        ),

        "actual": money(
            get_value(
                row,
                "ACTUAL_AMOUNT"
            )
        ),

        "disbursed": money(
            get_value(
                row,
                "TOTAL_FUND_DISBURSED_AMT"
            )
        ),

        # Payments
        "payment_count": number(
            get_value(
                row,
                "PAYMENT_COUNT"
            )
        ),

        "successful_payments": number(
            get_value(
                row,
                "PAYMENT_SUCCESS_COUNT"
            )
        ),

        "in_progress_payments": number(
            get_value(
                row,
                "PAYMENT_IN_PROGRESS_COUNT"
            )
        ),

        "vendor_count": number(
            get_value(
                row,
                "UNIQUE_VENDOR_COUNT"
            )
        ),

        "payments_per_30_days": number(
            get_value(
                row,
                "PAYMENTS_PER_30_DAYS"
            )
        ),

        # Timeline
        "completion_duration_days": number(
            get_value(
                row,
                "COMPLETION_DURATION_DAYS"
            )
        ),

        "payment_after_completion_days": number(
            get_value(
                row,
                "PAYMENT_AFTER_REPORTED_COMPLETION_DAYS"
            )
        ),

        "completion_before_last_payment": get_value(
            row,
            "COMPLETION_BEFORE_LAST_PAYMENT"
        ),

        # Peer
        "peer_count": number(
            get_value(
                row,
                "PEER_COUNT"
            )
        ),

        "peer_median_sanction": money(
            get_value(
                row,
                "PEER_MEDIAN_SANCTION"
            )
        ),

        "sanction_to_peer_median": number(
            get_value(
                row,
                "SANCTION_TO_PEER_MEDIAN"
            )
        ),

        # Data quality
        "missing_field_count": number(
            get_value(
                row,
                "MISSING_FIELD_COUNT"
            )
        ),

        "attachment_id": get_value(
            row,
            "ATTACH_ID"
        ),
    }


# ============================================================
# SELECT 100 CASES
# ============================================================


def select_llm_cases(df):

    work = df.copy()

    if "HYBRID_RISK_LEVEL" not in work.columns:

        raise KeyError(
            "HYBRID_RISK_LEVEL not found.\n"
            f"Available columns:\n{list(work.columns)}"
        )

    work["_RISK"] = (
        work["HYBRID_RISK_LEVEL"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    numeric_columns = [
        "HYBRID_RISK_SCORE",
        "INDEPENDENT_SIGNAL_COUNT",
        "ML_PERCENTILE",
        "PAYMENT_COUNT",
        "UNIQUE_VENDOR_COUNT",
        "RULE_SCORE",
        "STAT_SCORE",
    ]

    for column in numeric_columns:

        if column in work.columns:

            work[column] = pd.to_numeric(
                work[column],
                errors="coerce"
            ).fillna(0)

        else:

            work[column] = 0

    # --------------------------------------------------------
    # Selection score
    #
    # This does NOT change the actual FundGuard risk score.
    # It only ranks cases for optional LLM review.
    # --------------------------------------------------------

    work["_LLM_SELECTION_SCORE"] = (

        work["HYBRID_RISK_SCORE"] * 100

        + work["INDEPENDENT_SIGNAL_COUNT"] * 20

        + work["RULE_SCORE"]

        + work["STAT_SCORE"]

        + work["ML_PERCENTILE"] * 0.5

        + work["PAYMENT_COUNT"].clip(
            upper=50
        ) * 0.5

        + work["UNIQUE_VENDOR_COUNT"].clip(
            upper=30
        ) * 0.5
    )

    selected = []

    for risk, limit in [

        ("CRITICAL", CRITICAL_LIMIT),
        ("HIGH", HIGH_LIMIT),
        ("MEDIUM", MEDIUM_LIMIT),

    ]:

        subset = work[
            work["_RISK"] == risk
        ].copy()

        subset = subset.sort_values(
            "_LLM_SELECTION_SCORE",
            ascending=False
        )

        selected.append(
            subset.head(limit)
        )

    result = pd.concat(
        selected,
        ignore_index=True
    )

    result = result.drop_duplicates(
        subset=["WORK_ID"]
    )

    return result.head(
        MAX_LLM_WORKS
    )


# ============================================================
# LLM PROMPT
# ============================================================


SYSTEM_PROMPT = """
You are FundGuard AI's optional reasoning assistant.

Your job is to explain why an already-detected investigation candidate
may deserve human review.

STRICT RULES:

- Never conclude fraud, corruption, guilt, or misconduct.
- Never accuse an MP, vendor, contractor, or government department.
- The case is an investigation candidate only.
- Rules, statistics, and ML are screening signals.
- Risk score is investigation priority, not fraud probability.
- Peer count below 10 means weak peer evidence.
- Payment-per-30-days is a derived concentration feature, not a recurring
  monthly payment schedule.
- Payment after reported completion is a verification issue and may reflect
  settlement or reporting timing.
- Missing attachment IDs mean the identifier is absent from the dataset;
  do not claim the physical document does not exist.
- Never invent information.
- Use only supplied evidence.

Return ONLY JSON:

{
  "summary": "maximum 2 sentences",
  "signals": ["signal 1", "signal 2", "signal 3"],
  "verify": ["verification 1", "verification 2", "verification 3"],
  "confidence": "LOW | MEDIUM | HIGH"
}
"""


# ============================================================
# GROQ CALL
# ============================================================


def call_groq(
    evidence,
    api_key
):

    prompt = f"""
Review this FundGuard investigation candidate.

Evidence:

{json.dumps(
    evidence,
    ensure_ascii=False,
    separators=(",", ":"),
    default=str
)}

Return only the requested JSON.
"""

    payload = {

        "model": MODEL,

        "messages": [

            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },

            {
                "role": "user",
                "content": prompt
            }
        ],

        "temperature": 0.1,

        "max_tokens": 450,

        "response_format": {
            "type": "json_object"
        }
    }

    headers = {

        "Authorization":
            f"Bearer {api_key}",

        "Content-Type":
            "application/json"
    }

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            response = requests.post(
                API_URL,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            # ------------------------------------------------
            # Rate limit
            # ------------------------------------------------

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "retry-after",
                    "10"
                )

                try:
                    wait = float(
                        retry_after
                    )
                except Exception:
                    wait = 10

                print(
                    f"  Rate limited. "
                    f"Waiting {wait:.1f}s..."
                )

                time.sleep(wait)

                continue

            # ------------------------------------------------
            # Error
            # ------------------------------------------------

            if response.status_code >= 400:

                print(
                    f"  Attempt {attempt} failed: "
                    f"HTTP {response.status_code}: "
                    f"{response.text[:500]}"
                )

                if attempt < MAX_RETRIES:
                    time.sleep(2)
                    continue

                return None

            # ------------------------------------------------
            # Parse
            # ------------------------------------------------

            data = response.json()

            content = (
                data["choices"][0]["message"]["content"]
            )

            content = clean_json(
                content
            )

            result = json.loads(
                content
            )

            required = [
                "summary",
                "signals",
                "verify",
                "confidence",
            ]

            for field in required:

                if field not in result:

                    raise ValueError(
                        f"Missing field: {field}"
                    )

            return result

        except Exception as exc:

            print(
                f"  Attempt {attempt} failed: "
                f"{exc}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(2)

    return None


# ============================================================
# MAIN
# ============================================================


def main():

    # ========================================================
    # 1. LOAD
    # ========================================================

    print("=" * 78)
    print("1. LOADING INVESTIGATION QUEUE")
    print("=" * 78)

    if not QUEUE_FILE.exists():

        raise FileNotFoundError(
            f"Queue not found:\n{QUEUE_FILE}"
        )

    df = pd.read_csv(
        QUEUE_FILE
    )

    print(
        f"Rows : {len(df):,}"
    )

    # ========================================================
    # 2. CONFIG
    # ========================================================

    print()
    print("=" * 78)
    print("2. CHECKING GROQ CONFIGURATION")
    print("=" * 78)

    load_dotenv(
        BASE_DIR / ".env"
    )

    api_key = os.getenv(
        "GROQ_API_KEY"
    )

    if not api_key:

        raise RuntimeError(
            "GROQ_API_KEY not found."
        )

    global MODEL

    MODEL = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-120b"
    )

    print(
        f"Model : {MODEL}"
    )

    print(
        "Groq API key : FOUND"
    )

    # ========================================================
    # 3. CACHE
    # ========================================================

    print()
    print("=" * 78)
    print("3. LOADING CACHE")
    print("=" * 78)

    if CACHE_FILE.exists():

        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            cache = json.load(f)

    else:

        cache = {}

    print(
        f"Cached explanations : "
        f"{len(cache):,}"
    )

    # ========================================================
    # 4. SELECT
    # ========================================================

    print()
    print("=" * 78)
    print("4. SELECTING HIGH-VALUE CASES")
    print("=" * 78)

    selected = select_llm_cases(
        df
    )

    print(
        f"Selected for LLM : "
        f"{len(selected):,}"
    )

    print()
    print("Selection:")

    counts = (
        selected["_RISK"]
        .value_counts()
    )

    print(
        f"  CRITICAL : "
        f"{counts.get('CRITICAL', 0)}"
    )

    print(
        f"  HIGH     : "
        f"{counts.get('HIGH', 0)}"
    )

    print(
        f"  MEDIUM   : "
        f"{counts.get('MEDIUM', 0)}"
    )

    print(
        "  LOW      : 0"
    )

    # ========================================================
    # 5. GENERATE
    # ========================================================

    print()
    print("=" * 78)
    print("5. GENERATING LLM EXPLANATIONS")
    print("=" * 78)

    results = []

    new_calls = 0
    cached_count = 0
    failed_count = 0

    for index, (_, row) in enumerate(
        selected.iterrows(),
        start=1
    ):

        work_id = str(
            row["WORK_ID"]
        )

        print(
            f"[{index}/{len(selected)}] "
            f"WORK_ID={work_id}"
        )

        # ----------------------------------------------------
        # Cached
        # ----------------------------------------------------

        if work_id in cache:

            print(
                "  Cached."
            )

            result = cache[
                work_id
            ]

            cached_count += 1

        # ----------------------------------------------------
        # New call
        # ----------------------------------------------------

        else:

            evidence = build_evidence(
                row
            )

            result = call_groq(
                evidence,
                api_key
            )

            if result is None:

                print(
                    "  FAILED."
                )

                failed_count += 1

                continue

            print(
                "  Generated."
            )

            cache[
                work_id
            ] = result

            # Save after EVERY successful call.
            with open(
                CACHE_FILE,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    cache,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            new_calls += 1

        results.append({

            "WORK_ID":
                work_id,

            "LLM_STATUS":
                "GENERATED",

            "LLM_MODEL":
                MODEL,

            "LLM_RISK_SUMMARY":
                result.get(
                    "summary",
                    ""
                ),

            "LLM_OBSERVED_SIGNALS":
                json.dumps(
                    result.get(
                        "signals",
                        []
                    ),
                    ensure_ascii=False
                ),

            "LLM_WHY_FLAGGED":
                result.get(
                    "summary",
                    ""
                ),

            "LLM_LIMITATIONS":
                "[]",

            "LLM_WHAT_TO_VERIFY":
                json.dumps(
                    result.get(
                        "verify",
                        []
                    ),
                    ensure_ascii=False
                ),

            "LLM_CONFIDENCE":
                result.get(
                    "confidence",
                    "LOW"
                ),
        })

    # ========================================================
    # 6. NOT SELECTED
    # ========================================================

    selected_ids = set(
        selected["WORK_ID"]
        .astype(str)
    )

    for _, row in df.iterrows():

        work_id = str(
            row["WORK_ID"]
        )

        if work_id in selected_ids:
            continue

        results.append({

            "WORK_ID":
                work_id,

            "LLM_STATUS":
                "NOT_SELECTED",

            "LLM_MODEL":
                MODEL,

            "LLM_RISK_SUMMARY":
                "",

            "LLM_OBSERVED_SIGNALS":
                "[]",

            "LLM_WHY_FLAGGED":
                "",

            "LLM_LIMITATIONS":
                "[]",

            "LLM_WHAT_TO_VERIFY":
                "[]",

            "LLM_CONFIDENCE":
                "",
        })

    # ========================================================
    # 7. SAVE OUTPUT
    # ========================================================

    print()
    print("=" * 78)
    print("6. SAVING")
    print("=" * 78)

    output_df = pd.DataFrame(
        results
    )

    output_df = (
        output_df
        .drop_duplicates(
            subset=["WORK_ID"],
            keep="last"
        )
    )

    output_df = output_df.sort_values(
        "WORK_ID"
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"Saved: {OUTPUT_FILE}"
    )

    # ========================================================
    # 8. SUMMARY
    # ========================================================

    print()
    print("=" * 78)
    print("7. SUMMARY")
    print("=" * 78)

    print(
        f"Investigation candidates : "
        f"{len(df):,}"
    )

    print(
        f"LLM selected             : "
        f"{len(selected):,}"
    )

    print(
        f"New API calls            : "
        f"{new_calls:,}"
    )

    print(
        f"Cached                   : "
        f"{cached_count:,}"
    )

    print(
        f"Failed                   : "
        f"{failed_count:,}"
    )

    print(
        f"Total output rows        : "
        f"{len(output_df):,}"
    )

    print()
    print("LLM status:")

    print(
        output_df[
            "LLM_STATUS"
        ]
        .value_counts()
        .to_string()
    )

    # ========================================================
    # COMPLETE
    # ========================================================

    print()
    print("=" * 78)
    print("LLM REASONING LAYER COMPLETE")
    print("=" * 78)

    print(
        "FundGuard detection does not depend on the LLM."
    )

    print(
        "All investigation candidates retain "
        "their deterministic evidence."
    )

    print(
        "LLM reasoning is an optional enhancement "
        "for selected high-priority cases."
    )

    print(
        "Do not interpret any output as a finding "
        "of fraud or corruption."
    )


if __name__ == "__main__":
    main()