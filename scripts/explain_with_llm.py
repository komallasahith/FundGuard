import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# FUNDGUARD AI - LLM REASONING LAYER
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "outputs" / "fundguard_evidence.json"
OUTPUT_FILE = BASE_DIR / "data" / "outputs" / "fundguard_ai_explanations.json"

load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

if not API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY not found in D:\\FundGuard\\.env"
    )

client = Groq(api_key=API_KEY)


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are the AI reasoning layer of FundGuard AI.

FundGuard AI detects anomaly and risk candidates in MPLADS
implementation data using deterministic rules, statistical
analysis, and Isolation Forest machine learning.

Your job is to EXPLAIN the supplied evidence for a human
investigator.

STRICT RULES:

1. Never say that fraud, corruption, theft, manipulation,
   or wrongdoing has been proven.

2. Use terms such as:
   - anomaly candidate
   - risk indicator
   - unusual pattern
   - requires investigation
   - warrants verification

3. Do NOT calculate or modify the hybrid risk score.

4. Do NOT change the supplied risk level.

5. Do NOT invent facts, amounts, dates, vendors, locations,
   reasons, or relationships.

6. Every factual statement must be supported by the supplied
   evidence.

7. If information is missing or null, say that it is unavailable.
   Do not guess.

8. Explain why the work was flagged.

9. Identify the strongest evidence signals.

10. Give practical investigation checks based only on the
    available evidence.

11. Clearly distinguish an anomaly indicator from proof of fraud.

12. Keep the explanation concise and suitable for a government
    investigation dashboard.

Return ONLY valid JSON in exactly this structure:

{
  "why_flagged": "string",
  "key_evidence": [
    "string"
  ],
  "investigation_checks": [
    "string"
  ],
  "assessment": "string",
  "data_limitations": [
    "string"
  ]
}
"""


# ============================================================
# BUILD PROMPT
# ============================================================

def build_prompt(record):

    identity = record.get("identity", {})
    risk = record.get("risk", {})
    detector_scores = record.get("detector_scores", {})
    financial = record.get("financial", {})
    statistical = record.get("statistical", {})
    transactions = record.get("transactions", {})
    timeline = record.get("timeline", {})
    evidence = record.get("evidence", {})

    structured_data = {
        "work_id": record.get("work_id"),

        "identity": {
            "mp_name": identity.get("mp_name"),
            "constituency": identity.get("constituency"),
            "work_category": identity.get("work_category"),
            "activity_name": identity.get("activity_name")
        },

        "risk": {
            "hybrid_score": risk.get("hybrid_score"),
            "risk_level": risk.get("risk_level"),
            "detector_agreement": risk.get("detector_agreement"),
            "detector_agreement_count": risk.get(
                "detector_agreement_count"
            ),
            "investigation_priority": risk.get(
                "investigation_priority"
            )
        },

        "detector_scores": detector_scores,

        "financial": financial,

        "statistical": statistical,

        "transactions": transactions,

        "timeline": timeline,

        "evidence": evidence,

        "summary": record.get("summary"),

        "investigation_guidance": record.get(
            "investigation_guidance"
        )
    }

    return f"""
Analyze this FundGuard AI anomaly candidate.

IMPORTANT:
- Do not perform new calculations.
- Do not change the supplied risk score or risk level.
- Do not call this fraud.
- Do not invent missing information.
- Use only the supplied evidence.

STRUCTURED EVIDENCE:

{json.dumps(
    structured_data,
    indent=2,
    ensure_ascii=False
)}
"""


# ============================================================
# PARSE RESPONSE
# ============================================================

def parse_json_response(text):

    text = text.strip()

    # Remove accidental markdown JSON fences
    if text.startswith("```"):

        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    return json.loads(text)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("FUNDGUARD AI - LLM REASONING LAYER")
print("=" * 70)

print(f"Input : {INPUT_FILE}")
print(f"Model : {MODEL}")

with open(
    INPUT_FILE,
    "r",
    encoding="utf-8"
) as f:

    evidence_records = json.load(f)


if not isinstance(evidence_records, list):
    raise ValueError(
        "fundguard_evidence.json must contain a list."
    )


print(
    f"Evidence records: {len(evidence_records):,}"
)


# ============================================================
# FIRST DEMO RUN
# ============================================================

# Start with 10 highest-risk records.
# After validation, change this to None to process everything.

DEMO_LIMIT = 10

if DEMO_LIMIT:
    records_to_process = evidence_records[:DEMO_LIMIT]
else:
    records_to_process = evidence_records


print(
    f"Processing: {len(records_to_process)} records"
)

print()


# ============================================================
# LLM PROCESSING
# ============================================================

results = []

for index, record in enumerate(
    records_to_process,
    start=1
):

    work_id = record.get(
        "work_id",
        "UNKNOWN"
    )

    identity = record.get(
        "identity",
        {}
    )

    mp_name = identity.get(
        "mp_name",
        "Unknown"
    )

    risk = record.get(
        "risk",
        {}
    )

    risk_level = risk.get(
        "risk_level",
        "UNKNOWN"
    )

    print(
        f"[{index}/{len(records_to_process)}] "
        f"Work {work_id} | "
        f"{mp_name} | "
        f"{risk_level}"
    )

    try:

        prompt = build_prompt(record)

        response = client.chat.completions.create(

            model=MODEL,

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],

            temperature=0.1,

            max_completion_tokens=1200,

            response_format={
                "type": "json_object"
            }
        )

        raw_response = (
            response
            .choices[0]
            .message
            .content
        )

        explanation = parse_json_response(
            raw_response
        )

        # ----------------------------------------------------
        # STORE RESULT
        # ----------------------------------------------------

        result = {

            "work_id": work_id,

            "mp_name": mp_name,

            "constituency": identity.get(
                "constituency"
            ),

            "work_category": identity.get(
                "work_category"
            ),

            "activity_name": identity.get(
                "activity_name"
            ),

            "hybrid_risk_score": risk.get(
                "hybrid_score"
            ),

            "risk_level": risk.get(
                "risk_level"
            ),

            "detector_agreement": risk.get(
                "detector_agreement"
            ),

            "detector_agreement_count": risk.get(
                "detector_agreement_count"
            ),

            "investigation_priority": risk.get(
                "investigation_priority"
            ),

            "detector_scores": detector_scores
            if (detector_scores := record.get(
                "detector_scores",
                {}
            ))
            else {},

            "why_flagged": explanation.get(
                "why_flagged",
                ""
            ),

            "key_evidence": explanation.get(
                "key_evidence",
                []
            ),

            "investigation_checks": explanation.get(
                "investigation_checks",
                []
            ),

            "assessment": explanation.get(
                "assessment",
                ""
            ),

            "data_limitations": explanation.get(
                "data_limitations",
                []
            ),

            "disclaimer": (
                "This system identifies anomaly/risk "
                "candidates for investigation. It does "
                "not establish fraud or wrongdoing."
            ),

            "model": MODEL
        }

        results.append(result)

        print("  ✓ Explanation generated")

    except Exception as e:

        print(
            f"  ✗ Failed: {str(e)}"
        )

        results.append({

            "work_id": work_id,

            "mp_name": mp_name,

            "constituency": identity.get(
                "constituency"
            ),

            "work_category": identity.get(
                "work_category"
            ),

            "activity_name": identity.get(
                "activity_name"
            ),

            "hybrid_risk_score": risk.get(
                "hybrid_score"
            ),

            "risk_level": risk.get(
                "risk_level"
            ),

            "detector_agreement": risk.get(
                "detector_agreement"
            ),

            "detector_agreement_count": risk.get(
                "detector_agreement_count"
            ),

            "investigation_priority": risk.get(
                "investigation_priority"
            ),

            "detector_scores": record.get(
                "detector_scores",
                {}
            ),

            "why_flagged": "",

            "key_evidence": [],

            "investigation_checks": [],

            "assessment": "",

            "data_limitations": [
                f"LLM generation failed: {str(e)}"
            ],

            "disclaimer": (
                "This system identifies anomaly/risk "
                "candidates for investigation. It does "
                "not establish fraud or wrongdoing."
            ),

            "model": MODEL
        })

    # Small delay between requests
    time.sleep(0.2)


# ============================================================
# SAVE OUTPUT
# ============================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# SUMMARY
# ============================================================

successful = sum(
    1
    for r in results
    if r.get("why_flagged")
)

failed = len(results) - successful


print()
print("=" * 70)
print("LLM OUTPUT")
print("=" * 70)

print(
    f"Generated : {successful}"
)

print(
    f"Failed    : {failed}"
)

print(
    f"Output    : {OUTPUT_FILE}"
)


# ============================================================
# SHOW SAMPLE
# ============================================================

print()
print("=" * 70)
print("SAMPLE AI EXPLANATIONS")
print("=" * 70)


for record in results[:3]:

    print("-" * 70)

    print(
        f"Work ID : {record.get('work_id')}"
    )

    print(
        f"MP      : {record.get('mp_name')}"
    )

    print(
        f"Risk    : {record.get('risk_level')}"
    )

    print(
        f"Score   : {record.get('hybrid_risk_score')}"
    )

    print()

    print(
        "Why flagged:"
    )

    print(
        record.get(
            "why_flagged",
            ""
        )
    )

    print()

    print(
        "Key evidence:"
    )

    for item in record.get(
        "key_evidence",
        []
    ):

        print(
            f"  • {item}"
        )

    print()

    print(
        "Investigation checks:"
    )

    for item in record.get(
        "investigation_checks",
        []
    ):

        print(
            f"  • {item}"
        )

    print()

    print(
        "Assessment:"
    )

    print(
        record.get(
            "assessment",
            ""
        )
    )

    print()

    print(
        "Data limitations:"
    )

    for item in record.get(
        "data_limitations",
        []
    ):

        print(
            f"  • {item}"
        )


print()
print(
    "LLM reasoning layer completed successfully."
)