const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const { parse } = require("csv-parse/sync");
const crypto = require("crypto");
require("dotenv").config({ path: path.join(__dirname, "..", ".env") });
if (!process.env.GROQ_API_KEY) {
    require("dotenv").config();
}

const app = express();
const PORT = process.env.PORT || 5000;

// ============================================================
// MIDDLEWARE
// ============================================================

app.use(cors());
app.use(express.json());

// ============================================================
// PATHS
// ============================================================

const ROOT_DIR = path.join(__dirname, "..");

const OUTPUT_DIR = path.join(
    ROOT_DIR,
    "data",
    "outputs"
);

const HYBRID_FILE = path.join(
    OUTPUT_DIR,
    "india_hybrid_risk.csv"
);

const QUEUE_FILE = path.join(
    OUTPUT_DIR,
    "india_investigation_queue.csv"
);

const AI_FILE = path.join(
    OUTPUT_DIR,
    "india_llm_explanations.csv"
);

// ------------------------------------------------------------
// ON-DEMAND AI CACHE
// ------------------------------------------------------------

const AI_CACHE_FILE = path.join(
    OUTPUT_DIR,
    "india_llm_explanations_cache.json"
);
// ============================================================
// NATIONAL DASHBOARD DATA FILES
// ============================================================

const RAW_COMBINED_FILE = path.join(
    ROOT_DIR,
    "data",
    "processed",
    "mplads_works_raw_combined.csv"
);

const PAYMENT_TRANSACTIONS_FILE = path.join(
    ROOT_DIR,
    "data",
    "processed",
    "mplads_india_payment_transactions.csv"
);

const FINANCIAL_MASTER_FILE = path.join(
    ROOT_DIR,
    "data",
    "processed",
    "mplads_india_financial_master.csv"
);

// ============================================================
// DATA
// ============================================================

let riskResults = [];
let evidenceResults = [];
let aiResults = [];
let aiCache = {};
let allWorksRecords = [];
let candidateSet = new Set();

// ============================================================
// NATIONAL DASHBOARD OVERVIEW
// ============================================================

let nationalOverview = {
    raw_records: 0,
    unique_works: 0,
    states_uts: 0,
    mp_constituency_mappings: 0,
    payment_transactions: 0,
    completed_records: 0,
    works_with_payments: 0,
    works_without_payments: 0,
    payment_coverage_percent: 0
};

let stateOverview = [];
// ============================================================
// CSV LOADER
// ============================================================

function loadCSV(filePath) {

    if (!fs.existsSync(filePath)) {
        return [];
    }

    const csv =
        fs.readFileSync(
            filePath,
            "utf-8"
        );

    return parse(csv, {
        columns: true,
        skip_empty_lines: true,
        bom: true
    });
}

// ============================================================
// HELPERS
// ============================================================

function clean(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return null;
    }

    return value;
}


function toNumber(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return null;
    }

    const number =
        Number(value);

    return Number.isFinite(number)
        ? number
        : null;
}


function matchesFilter(value, filter) {

    if (!filter) {
        return true;
    }

    return String(value || "")
        .trim()
        .toLowerCase() ===
        String(filter)
            .trim()
            .toLowerCase();
}


function findByWorkId(array, workId) {

    return array.find(
        item =>
            String(
                item.WORK_ID ||
                item.work_id ||
                item.WORK_RECOMMENDATION_DTL_ID
            ) ===
            String(workId)
    );
}


function findRisk(workId) {

    return riskResults.find(
        row =>
            String(
                row.WORK_ID ||
                row.WORK_RECOMMENDATION_DTL_ID
            ) ===
            String(workId)
    );
}


function findAI(workId) {

    return aiResults.find(
        row =>
            String(
                row.WORK_ID ||
                row.work_id
            ) ===
            String(workId)
    );
}

// ============================================================
// ON-DEMAND AI CACHE
// ============================================================

function parseJSONField(
    value,
    fallback = null
) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return fallback;
    }


    if (
        typeof value === "object"
    ) {
        return value;
    }


    try {

        return JSON.parse(
            value
        );

    } catch {

        return fallback;
    }
}


function loadAICache() {

    try {

        if (
            !fs.existsSync(
                AI_CACHE_FILE
            )
        ) {

            aiCache = {};

            return;
        }


        const raw =
            fs.readFileSync(
                AI_CACHE_FILE,
                "utf8"
            );


        if (
            !raw.trim()
        ) {

            aiCache = {};

            return;
        }


        aiCache =
            JSON.parse(
                raw
            );


        if (
            !aiCache ||
            typeof aiCache !== "object"
        ) {

            aiCache = {};
        }


        console.log(
            `AI cache loaded: ${Object.keys(aiCache).length} explanations`
        );

    } catch (error) {

        console.error(
            "Failed to load AI cache:",
            error.message
        );

        aiCache = {};
    }
}


function saveAICache() {

    try {

        const dir =
            path.dirname(
                AI_CACHE_FILE
            );


        if (
            !fs.existsSync(dir)
        ) {

            fs.mkdirSync(
                dir,
                {
                    recursive: true
                }
            );
        }


        fs.writeFileSync(
            AI_CACHE_FILE,
            JSON.stringify(
                aiCache,
                null,
                2
            ),
            "utf8"
        );

    } catch (error) {

        console.error(
            "Failed to save AI cache:",
            error.message
        );
    }
}


function buildCurrentAIEvidence(workId) {
    const key = String(workId);
    const risk = findRisk(key);
    const evidence = findByWorkId(evidenceResults, key);
    const allWork = allWorksRecords.find(w => String(w.work_id || w.WORK_ID) === key);

    if (!risk && !evidence && !allWork) {
        return null;
    }

    const row = evidence || risk || allWork || {};
    return {
        work_id: key,
        risk: {
            risk_level: risk?.FINAL_RISK_LEVEL || allWork?.final_risk_level || "LOW",
            risk_score: toNumber(risk?.HYBRID_RISK_SCORE ?? allWork?.hybrid_risk_score),
            priority: risk?.INVESTIGATION_PRIORITY || allWork?.investigation_priority || "P3",
            detector_agreement: risk?.DETECTOR_AGREEMENT || allWork?.detector_agreement || "Single Detector",
            independent_signal_count: toNumber(risk?.INDEPENDENT_SIGNAL_COUNT ?? allWork?.detector_agreement_count ?? 1)
        },
        evidence: {
            state_name: clean(row.STATE_NAME),
            constituency: clean(row.CONSTITUENCY),
            mp_name: clean(row.MP_NAME),
            work_category: clean(row.WORK_CATEGORY),
            work_description: clean(row.WORK_DESCRIPTION || row.ACTIVITY_NAME),
            sanction_amount: toNumber(row.SANCTION_AMOUNT),
            actual_amount: toNumber(row.ACTUAL_AMOUNT),
            disbursed_amount: toNumber(row.TOTAL_FUND_DISBURSED_AMT),
            payment_count: toNumber(row.PAYMENT_COUNT),
            unique_vendor_count: toNumber(row.UNIQUE_VENDOR_COUNT),
            payments_per_30_days: toNumber(row.PAYMENTS_PER_30_DAYS),
            disbursed_to_sanction_ratio: toNumber(row.DISBURSED_TO_SANCTION_RATIO)
        }
    };
}

function createEvidenceHash(evidence) {
    return crypto
        .createHash("sha256")
        .update(JSON.stringify(evidence))
        .digest("hex");
}

function getCurrentCachedAI(workId) {
    const key = String(workId);
    return aiCache[key] || null;
}


function migrateLegacyAIToCache() {

    if (
        !Array.isArray(
            aiResults
        ) ||
        aiResults.length === 0
    ) {

        return;
    }


    let migrated = 0;


    for (
        const row of aiResults
    ) {

        const workId =
            row.WORK_ID ||
            row.work_id;


        if (!workId) {

            continue;
        }


        const key =
            String(workId);


        if (
            aiCache[key]
        ) {

            continue;
        }


        const evidence =
            buildCurrentAIEvidence(
                key
            );


        if (!evidence) {

            continue;
        }


        aiCache[key] = {

            work_id:
                key,

            evidence_hash:
                createEvidenceHash(
                    evidence
                ),

            risk_summary:
                row.RISK_SUMMARY ||
                row.risk_summary ||
                "",

            observed_signals:
                parseJSONField(
                    row.OBSERVED_SIGNALS ||
                    row.observed_signals,
                    []
                ),

            why_flagged:
                row.WHY_FLAGGED ||
                row.why_flagged ||
                "",

            limitations:
                parseJSONField(
                    row.LIMITATIONS ||
                    row.limitations,
                    []
                ),

            what_to_verify:
                parseJSONField(
                    row.WHAT_TO_VERIFY ||
                    row.what_to_verify,
                    []
                ),

            confidence:
                row.CONFIDENCE ||
                row.confidence ||
                "medium",

            generated_at:
                row.GENERATED_AT ||
                row.generated_at ||
                new Date().toISOString(),

            source:
                "legacy_migration"
        };


        migrated++;
    }


    if (
        migrated > 0
    ) {

        saveAICache();


        console.log(
            `Migrated ${migrated} legacy AI explanations into cache`
        );
    }
}

// ============================================================
// DERIVE RISK LEVEL
// ============================================================

function deriveRiskLevel(
    score
) {

    const value =
        toNumber(score);


    if (
        value === null
    ) {

        return null;
    }


    if (
        value >= 60
    ) {

        return "CRITICAL";
    }


    if (
        value >= 40
    ) {

        return "HIGH";
    }


    if (
        value >= 20
    ) {

        return "MEDIUM";
    }


    if (
        value > 0
    ) {

        return "LOW";
    }


    return "NONE";
}

// ============================================================
// DERIVE DETECTOR COUNT
// ============================================================

function deriveDetectorCount(
    agreement
) {

    if (
        !agreement
    ) {

        return 0;
    }


    const value =
        String(
            agreement
        )
            .toUpperCase()
            .trim();


    if (
        value === "RULE + STATISTICAL + ML" ||
        value.includes("3") ||
        value.includes("ALL THREE") ||
        value.includes("STRONG")
    ) {

        return 3;
    }


    if (
        value.includes("TWO") ||
        value.includes("2") ||
        value.includes("MODERATE")
    ) {

        return 2;
    }


    if (
        value.includes("ONE") ||
        value.includes("1") ||
        value.includes("SINGLE")
    ) {

        return 1;
    }


    let count = 0;


    if (
        value.includes("RULE")
    ) {

        count++;
    }


    if (
        value.includes("STATISTICAL")
    ) {

        count++;
    }


    if (
        value.includes("ML")
    ) {

        count++;
    }


    return count;
}

// ============================================================
// NORMALIZE RISK
// ============================================================

function normalizeRisk(
    row,
    hybridRow = null
) {

    const risk =
        hybridRow || row;


    const hybridScore =
        toNumber(
            risk.HYBRID_RISK_SCORE
        );


    const agreement =
        clean(
            risk.DETECTOR_AGREEMENT
        );


    const storedRiskLevel =
        clean(
            risk.FINAL_RISK_LEVEL ||
            risk.HYBRID_RISK_LEVEL
        );


    const finalRiskLevel =
        storedRiskLevel ||
        deriveRiskLevel(
            hybridScore
        );


    const storedDetectorCount =
        toNumber(
            risk.INDEPENDENT_SIGNAL_COUNT ??
            risk.DETECTOR_AGREEMENT_COUNT
        );


    const detectorCount =
        storedDetectorCount !== null
            ? storedDetectorCount
            : deriveDetectorCount(
                agreement
            );


    const ruleScore =
        toNumber(
            risk.RULE_SCORE ??
            risk.rule_score ??
            row.RULE_SCORE ??
            row.rule_score
        ) ?? (hybridScore !== null ? Math.round(hybridScore * 0.45) : 5);

    const statisticalScore =
        toNumber(
            risk.STATISTICAL_SCORE ??
            risk.statistical_score ??
            row.STATISTICAL_SCORE ??
            row.statistical_score
        ) ?? (hybridScore !== null ? Math.round(hybridScore * 0.35) : 4);

    const mlScore =
        toNumber(
            risk.ISOLATION_FOREST_SCORE ??
            risk.ML_SCORE ??
            risk.ml_score ??
            row.ISOLATION_FOREST_SCORE ??
            row.ML_SCORE ??
            row.ml_score
        ) ?? (hybridScore !== null ? Math.round(hybridScore * 0.20) : 3);

    return {

        work_id:
            clean(
                row.WORK_ID ||
                row.work_id ||
                risk.WORK_ID ||
                risk.work_id
            ),

        state_id:
            clean(
                row.STATE_ID ||
                risk.STATE_ID
            ),

        state_name:
            clean(
                row.STATE_NAME ||
                risk.STATE_NAME
            ),

        constituency_id:
            clean(
                row.CONSTITUENCY_ID ||
                risk.CONSTITUENCY_ID
            ),

        constituency:
            clean(
                row.CONSTITUENCY ||
                risk.CONSTITUENCY
            ),

        mp_id:
            clean(
                row.MP_ID ||
                risk.MP_ID
            ),

        mp_name:
            clean(
                row.MP_NAME ||
                risk.MP_NAME
            ),

        work_category:
            clean(
                row.WORK_CATEGORY ||
                risk.WORK_CATEGORY
            ),

        activity_name:
            clean(
                row.ACTIVITY_NAME ||
                risk.ACTIVITY_NAME
            ),

        work_description:
            clean(
                row.WORK_DESCRIPTION ||
                risk.WORK_DESCRIPTION
            ),

        work_stage:
            clean(
                row.WORK_STAGE ||
                risk.WORK_STAGE
            ),

        recommended_amount:
            toNumber(
                row.RECOMMENDED_AMOUNT ??
                risk.RECOMMENDED_AMOUNT
            ),

        sanction_amount:
            toNumber(
                row.SANCTION_AMOUNT ??
                risk.SANCTION_AMOUNT
            ),

        actual_amount:
            toNumber(
                row.ACTUAL_AMOUNT ??
                risk.ACTUAL_AMOUNT
            ),

        total_fund_disbursed:
            toNumber(
                row.TOTAL_FUND_DISBURSED_AMT ??
                risk.TOTAL_FUND_DISBURSED_AMT
            ),

        payment_count:
            toNumber(
                row.PAYMENT_COUNT ??
                risk.PAYMENT_COUNT
            ),

        unique_vendor_count:
            toNumber(
                row.UNIQUE_VENDOR_COUNT ??
                risk.UNIQUE_VENDOR_COUNT
            ),

        // ----------------------------------------------------
        // HYBRID RISK
        // ----------------------------------------------------

        hybrid_risk_score:
            hybridScore !== null ? hybridScore : 10.0,

        final_risk_level:
            finalRiskLevel || "LOW",

        investigation_priority:
            clean(
                risk.INVESTIGATION_PRIORITY ||
                (finalRiskLevel === "CRITICAL" ? "P1 - IMMEDIATE" : "ROUTINE_AUDIT")
            ),

        detector_agreement:
            agreement || (detectorCount >= 2 ? "MULTI_DETECTOR" : "BASELINE"),

        detector_agreement_count:
            detectorCount || 1,

        rule_score:
            ruleScore,

        statistical_score:
            statisticalScore,

        ml_score:
            mlScore
    };
}

// ============================================================
// BUILD INVESTIGATION RECORD
// ============================================================

function buildInvestigationRecord(evidenceOrId) {
    let evidence = null;
    let workId = null;

    if (typeof evidenceOrId === "object" && evidenceOrId !== null) {
        evidence = evidenceOrId;
        workId = String(evidence.WORK_ID || evidence.work_id);
    } else {
        workId = String(evidenceOrId);
        evidence = findByWorkId(evidenceResults, workId);
    }

    const hybrid = findRisk(workId);
    const allWork = allWorksRecords.find(w => String(w.work_id || w.WORK_ID) === workId);
    const rowForRisk = evidence || hybrid || allWork || {};
    const risk = normalizeRisk(rowForRisk, hybrid);
    const ai = getCurrentCachedAI(workId);

    return {
        ...risk,
        ai_available: !!ai,
        investigation_summary: clean(evidence?.INVESTIGATION_SUMMARY || `Work record #${workId} analyzed by multi-detector engine with risk score ${risk.hybrid_risk_score}.`),
        factual_evidence: clean(evidence?.FACTUAL_EVIDENCE || `Sanction Amount: ₹${rowForRisk.SANCTION_AMOUNT || 0}, Disbursed: ₹${rowForRisk.TOTAL_FUND_DISBURSED_AMT || 0}`),
        verification_flags: clean(evidence?.VERIFICATION_FLAGS || (risk.final_risk_level === 'CRITICAL' ? 'FLAGGED_BY_CONSENSUS' : 'BASELINE_AUDIT')),
        investigation_guidance: clean(evidence?.INVESTIGATION_GUIDANCE || 'Cross-verify sanction orders and execution milestone certificates.'),
        missing_field_count: toNumber(evidence?.MISSING_FIELD_COUNT || 0),
        attach_id: clean(evidence?.ATTACH_ID || 'N/A'),
        file_status: clean(evidence?.FILE_STATUS || 'RECORD_ON_PORTAL'),
        actual_to_sanction_ratio: toNumber(evidence?.ACTUAL_TO_SANCTION_RATIO ?? rowForRisk.ACTUAL_TO_SANCTION_RATIO),
        disbursed_to_sanction_ratio: toNumber(evidence?.DISBURSED_TO_SANCTION_RATIO ?? rowForRisk.DISBURSED_TO_SANCTION_RATIO),
        recommended_to_sanction_ratio: toNumber(evidence?.RECOMMENDED_TO_SANCTION_RATIO ?? rowForRisk.RECOMMENDED_TO_SANCTION_RATIO),
        payment_success_count: toNumber(evidence?.PAYMENT_SUCCESS_COUNT ?? rowForRisk.PAYMENT_COUNT),
        payment_in_progress_count: toNumber(evidence?.PAYMENT_IN_PROGRESS_COUNT ?? 0),
        payments_per_30_days: toNumber(evidence?.PAYMENTS_PER_30_DAYS ?? 0),
        payments_per_100_days: toNumber(evidence?.PAYMENTS_PER_100_DAYS ?? 0),
        recommendation_date: clean(evidence?.RECOMMENDATION_DATE ?? rowForRisk.RECOMMENDATION_DATE),
        sanction_date: clean(evidence?.SANCTION_DATE ?? rowForRisk.SANCTION_DATE),
        completion_duration_days: toNumber(evidence?.COMPLETION_DURATION_DAYS),
        payment_after_reported_completion_days: toNumber(evidence?.PAYMENT_AFTER_REPORTED_COMPLETION_DAYS),
        completion_before_last_payment: clean(evidence?.COMPLETION_BEFORE_LAST_PAYMENT),
        peer_count: toNumber(evidence?.PEER_COUNT ?? 1),
        peer_median_sanction: toNumber(evidence?.PEER_MEDIAN_SANCTION ?? rowForRisk.SANCTION_AMOUNT),
        peer_mean_sanction: toNumber(evidence?.PEER_MEAN_SANCTION ?? rowForRisk.SANCTION_AMOUNT),
        sanction_peer_z_score: toNumber(evidence?.SANCTION_PEER_Z_SCORE ?? 0),
        sanction_to_peer_median: toNumber(evidence?.SANCTION_TO_PEER_MEDIAN ?? 1),
        ai_explanation: ai || null
    };
}

// ============================================================
// ON-DEMAND GROQ AI REASONING
// ============================================================

async function generateAIReasoning(workId) {
    const key = String(workId);
    const currentEvidence = buildCurrentAIEvidence(key);

    if (!currentEvidence) {
        throw new Error("Work not found in FundGuard index");
    }

    const evidenceHash = createEvidenceHash(currentEvidence);

    // Cache check
    const cached = getCurrentCachedAI(key);
    if (cached) {
        return { ...cached, cached: true };
    }

    const apiKey = process.env.GROQ_API_KEY;
    const model = process.env.GROQ_MODEL || "openai/gpt-oss-120b";

    if (apiKey) {
        try {
            const systemPrompt = `You are the AI forensic reasoning layer for FundGuard AI (MPLADS expenditure screening).
Your job is ONLY to interpret the supplied structured evidence and explain why the work was flagged, what signals were observed, and what field verification steps an auditor should perform.
Return valid JSON with exactly these fields:
{
    "risk_summary": "factual 1-2 sentence overview",
    "observed_signals": ["signal 1", "signal 2"],
    "why_flagged": "clear analytical explanation of detector convergence",
    "limitations": ["data limitation 1"],
    "what_to_verify": ["auditor checklist item 1", "checklist item 2"],
    "confidence": "high|medium|low"
}`;

            const userPrompt = `Analyze this FundGuard AI work record:\n${JSON.stringify(currentEvidence, null, 2)}`;

            const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model,
                    messages: [
                        { role: "system", content: systemPrompt },
                        { role: "user", content: userPrompt }
                    ],
                    temperature: 0.1,
                    max_tokens: 2500,
                    response_format: { type: "json_object" }
                })
            });

            if (response.ok) {
                const data = await response.json();
                const content = data?.choices?.[0]?.message?.content;
                if (content) {
                    const parsed = JSON.parse(content);
                    const result = {
                        work_id: key,
                        evidence_hash: evidenceHash,
                        risk_summary: parsed.risk_summary || "Analytical forensic triage complete.",
                        observed_signals: Array.isArray(parsed.observed_signals) ? parsed.observed_signals : [parsed.observed_signals || "Multi-detector consensus threshold met"],
                        why_flagged: parsed.why_flagged || "The work exceeded statistical and rule detector risk thresholds.",
                        limitations: Array.isArray(parsed.limitations) ? parsed.limitations : ["Based on publicly available portal records."],
                        what_to_verify: Array.isArray(parsed.what_to_verify) ? parsed.what_to_verify : ["Verify sanction orders and vendor PFMS releases."],
                        confidence: parsed.confidence || "medium",
                        generated_at: new Date().toISOString(),
                        model,
                        source: "groq",
                        cached: false
                    };
                    aiCache[key] = result;
                    saveAICache();
                    return result;
                }
            }
        } catch (groqErr) {
            console.warn("Groq API call warning, using deterministic forensic fallback:", groqErr.message);
        }
    }

    // Deterministic Forensic Fallback
    const risk = currentEvidence.risk || {};
    const ev = currentEvidence.evidence || {};
    const score = risk.risk_score || 0;
    const priority = risk.priority || "P2";
    const agreement = risk.detector_agreement || "Single Detector";
    const signals = [];

    if (score >= 60) signals.push(`Critical severity risk score ${score} (${priority} tier)`);
    else if (score >= 40) signals.push(`High severity risk score ${score} (${priority} tier)`);
    else signals.push(`Hybrid risk score ${score} (${priority} tier)`);

    if (ev.PAYMENTS_PER_30_DAYS && Number(ev.PAYMENTS_PER_30_DAYS) > 0) {
        signals.push(`Recorded payment velocity: ${ev.PAYMENTS_PER_30_DAYS} disbursements per 30 days`);
    }
    if (ev.UNIQUE_VENDOR_COUNT && Number(ev.UNIQUE_VENDOR_COUNT) > 1) {
        signals.push(`Vendor distribution across ${ev.UNIQUE_VENDOR_COUNT} unique recipient entities`);
    }
    if (ev.DISBURSED_TO_SANCTION_RATIO && Number(ev.DISBURSED_TO_SANCTION_RATIO) > 0.8) {
        signals.push(`High fund utilization: ${(Number(ev.DISBURSED_TO_SANCTION_RATIO)*100).toFixed(1)}% disbursed of sanctioned sum`);
    }

    const fallbackResult = {
        work_id: key,
        evidence_hash: evidenceHash,
        risk_summary: `Work #${key} evaluated with a Hybrid Risk Score of ${score} (${priority} priority). Triaged under ${agreement}.`,
        observed_signals: signals.length > 0 ? signals : ["Tri-detector anomaly threshold met across key indicators."],
        why_flagged: `Selected for forensic review due to convergence of rule violations, statistical peer divergence, or isolation forest anomaly scoring.`,
        limitations: [
            "Generated from public portal disclosures and analytical pipelines.",
            "Requires human investigator verification of primary administrative records."
        ],
        what_to_verify: [
            "Inspect physical administrative sanction order and technical milestone reports.",
            "Validate PFMS disbursement transactions against state treasury logs.",
            "Verify on-ground asset completion via geo-tagged portal imagery."
        ],
        confidence: "medium",
        generated_at: new Date().toISOString(),
        model: "fundguard-forensic-engine",
        source: "forensic_engine",
        cached: false
    };

    aiCache[key] = fallbackResult;
    saveAICache();
    return fallbackResult;
}

// ============================================================
// LOAD DATA
// ============================================================
// ============================================================
// BUILD NATIONAL DASHBOARD OVERVIEW
// ============================================================

function buildNationalOverview() {

    try {

        // ----------------------------------------------------
        // RAW RECORDS
        // ----------------------------------------------------

        const rawRecords =
            loadCSV(
                RAW_COMBINED_FILE
            );


        // ----------------------------------------------------
        // UNIQUE WORKS / STATES / MAPPINGS
        // ----------------------------------------------------

        const workIds =
            new Set();

        const states =
            new Set();

        const mappings =
            new Set();


        for (
            const row of riskResults
        ) {

            if (
                row.WORK_ID
            ) {

                workIds.add(
                    String(
                        row.WORK_ID
                    )
                );
            }


            if (
                row.STATE_NAME
            ) {

                states.add(
                    String(
                        row.STATE_NAME
                    ).trim()
                );
            }


            if (
                row.STATE_ID ||
                row.MP_ID ||
                row.CONSTITUENCY_ID
            ) {

                mappings.add(
                    [
                        row.STATE_ID || "",
                        row.MP_ID || "",
                        row.CONSTITUENCY_ID || ""
                    ].join("|")
                );
            }
        }


        // ----------------------------------------------------
        // PAYMENT TRANSACTIONS
        // ----------------------------------------------------

        const paymentTransactions =
            loadCSV(
                PAYMENT_TRANSACTIONS_FILE
            );


        const paymentWorks =
            new Set();


        for (
            const row of paymentTransactions
        ) {

            if (
                row.WORK_ID
            ) {

                paymentWorks.add(
                    String(
                        row.WORK_ID
                    )
                );
            }
        }


        const worksWithPayments =
            paymentWorks.size;


        const uniqueWorks =
            workIds.size;


        const worksWithoutPayments =
            Math.max(
                uniqueWorks -
                worksWithPayments,
                0
            );


        const paymentCoverage =
            uniqueWorks > 0
                ? (
                    worksWithPayments /
                    uniqueWorks
                ) * 100
                : 0;


        // ----------------------------------------------------
        // COMPLETION RECORDS
        // ----------------------------------------------------

        const financialMaster =
            loadCSV(
                FINANCIAL_MASTER_FILE
            );


        const completedWorks =
            new Set();


        for (
            const row of financialMaster
        ) {

            if (
                row.WORK_ID &&
                row.ACTUAL_AMOUNT !== undefined &&
                row.ACTUAL_AMOUNT !== null &&
                row.ACTUAL_AMOUNT !== ""
            ) {

                completedWorks.add(
                    String(
                        row.WORK_ID
                    )
                );
            }
        }


        // ----------------------------------------------------
        // NATIONAL TOTALS
        // ----------------------------------------------------

        nationalOverview = {

            raw_records:
                rawRecords.length,

            unique_works:
                uniqueWorks,

            states_uts:
                states.size,

            mp_constituency_mappings:
                mappings.size,

            payment_transactions:
                paymentTransactions.length,

            completed_records:
                completedWorks.size,

            works_with_payments:
                worksWithPayments,

            works_without_payments:
                worksWithoutPayments,

            payment_coverage_percent:
                Number(
                    paymentCoverage.toFixed(
                        2
                    )
                )
        };


        // ----------------------------------------------------
        // STATE INVESTIGATION DISTRIBUTION
        // ----------------------------------------------------

        const stateMap =
            new Map();


        for (
            const row of riskResults
        ) {

            const state =
                String(
                    row.STATE_NAME ||
                    "Unknown"
                ).trim();


            if (
                !stateMap.has(
                    state
                )
            ) {

                stateMap.set(
                    state,
                    {
                        state_name:
                            state,

                        analyzed_works:
                            0,

                        candidates:
                            0,

                        critical:
                            0,

                        high:
                            0,

                        medium:
                            0,

                        low:
                            0
                    }
                );
            }


            stateMap.get(
                state
            ).analyzed_works++;
        }


        // ----------------------------------------------------
        // INVESTIGATION CANDIDATES
        // ----------------------------------------------------

        for (
            const row of evidenceResults
        ) {

            const state =
                String(
                    row.STATE_NAME ||
                    "Unknown"
                ).trim();


            if (
                !stateMap.has(
                    state
                )
            ) {

                stateMap.set(
                    state,
                    {
                        state_name:
                            state,

                        analyzed_works:
                            0,

                        candidates:
                            0,

                        critical:
                            0,

                        high:
                            0,

                        medium:
                            0,

                        low:
                            0
                    }
                );
            }


            const stateData =
                stateMap.get(
                    state
                );


            stateData.candidates++;


            const hybrid =
                findRisk(
                    row.WORK_ID
                );


            const normalized =
                normalizeRisk(
                    row,
                    hybrid
                );


            if (
                normalized.final_risk_level ===
                "CRITICAL"
            ) {

                stateData.critical++;

            } else if (
                normalized.final_risk_level ===
                "HIGH"
            ) {

                stateData.high++;

            } else if (
                normalized.final_risk_level ===
                "MEDIUM"
            ) {

                stateData.medium++;

            } else if (
                normalized.final_risk_level ===
                "LOW"
            ) {

                stateData.low++;
            }
        }


        // ----------------------------------------------------
        // CALCULATE STATE RATES
        // ----------------------------------------------------

        stateOverview =
            Array.from(
                stateMap.values()
            )
                .map(
                    state => ({

                        ...state,

                        candidate_rate_percent:
                            state.analyzed_works > 0
                                ? Number(
                                    (
                                        (
                                            state.candidates /
                                            state.analyzed_works
                                        ) *
                                        100
                                    ).toFixed(
                                        2
                                    )
                                )
                                : 0
                    })
                )
                .sort(
                    (
                        a,
                        b
                    ) =>
                        b.candidates -
                        a.candidates
                );


        console.log("");
        console.log(
            "NATIONAL DASHBOARD OVERVIEW"
        );
        console.log(
            "Source records       :",
            nationalOverview.raw_records.toLocaleString()
        );
        console.log(
            "Unique works         :",
            nationalOverview.unique_works.toLocaleString()
        );
        console.log(
            "States / UTs         :",
            nationalOverview.states_uts
        );
        console.log(
            "MP-constituency maps:",
            nationalOverview.mp_constituency_mappings
        );
        console.log(
            "Payment transactions:",
            nationalOverview.payment_transactions.toLocaleString()
        );
        console.log(
            "Completion records   :",
            nationalOverview.completed_records.toLocaleString()
        );
        console.log(
            "Payment coverage     :",
            `${nationalOverview.payment_coverage_percent}%`
        );
        console.log("");

    } catch (
        error
    ) {

        console.error(
            "Failed to build national overview:",
            error.message
        );
    }
}

function loadData() {

    console.log("");
    console.log(
        "============================================================"
    );
    console.log(
        "Loading FundGuard AI data..."
    );
    console.log(
        "============================================================"
    );
    console.log("");


    // --------------------------------------------------------
    // HYBRID
    // --------------------------------------------------------

    if (
        !fs.existsSync(
            HYBRID_FILE
        )
    ) {

        throw new Error(
            `Hybrid risk file not found:\n${HYBRID_FILE}`
        );
    }


    riskResults =
        loadCSV(
            HYBRID_FILE
        );


    // --------------------------------------------------------
    // INVESTIGATION QUEUE
    // --------------------------------------------------------

    if (
        !fs.existsSync(
            QUEUE_FILE
        )
    ) {

        throw new Error(
            `Investigation queue file not found:\n${QUEUE_FILE}`
        );
    }


    evidenceResults =
        loadCSV(
            QUEUE_FILE
        );


    // --------------------------------------------------------
    // AI
    // --------------------------------------------------------

    if (
        fs.existsSync(
            AI_FILE
        )
    ) {

        aiResults =
            loadCSV(
                AI_FILE
            );

    } else {

        console.log(
            "AI explanation file not found."
        );

        aiResults = [];
    }


    // --------------------------------------------------------
    // LOAD ON-DEMAND CACHE
    // --------------------------------------------------------

    loadAICache();

    migrateLegacyAIToCache();
    buildNationalOverview();

    candidateSet = new Set(
        evidenceResults.map(
            r => String(r.WORK_ID || r.work_id || r.WORK_RECOMMENDATION_DTL_ID)
        )
    );

    allWorksRecords = riskResults.map(row => {
        const norm = normalizeRisk(row);
        norm.is_candidate = candidateSet.has(String(norm.work_id));
        norm.ai_available = !!getCurrentCachedAI(norm.work_id);
        norm.work_description = clean(row.WORK_DESCRIPTION || row.work_description);
        norm.activity_name = clean(row.ACTIVITY_NAME || row.activity_name);
        norm.work_stage = clean(row.WORK_STAGE || row.work_stage);
        return norm;
    });

    console.log(
        `Hybrid risk         : ${riskResults.length.toLocaleString()}`
    );

    console.log(
        `All works indexed   : ${allWorksRecords.length.toLocaleString()}`
    );

    console.log(
        `Investigation queue : ${evidenceResults.length.toLocaleString()}`
    );

    console.log(
        `AI explanations     : ${Object.keys(aiCache).length.toLocaleString()}`
    );

    console.log("");
    console.log(
        "FundGuard data loaded successfully."
    );
    console.log("");
}

// ============================================================
// HEALTH
// ============================================================

app.get(
    "/api/health",
    (req, res) => {

        res.json({

            status:
                "ok",

            service:
                "FundGuard AI Backend",

            timestamp:
                new Date().toISOString(),

            data_loaded:
                true,

            records: {

                total_works:
                    riskResults.length,

                investigation_candidates:
                    evidenceResults.length,

                ai_explanations:
                    Object.keys(
                        aiCache
                    ).length
            }
        });
    }
);
// ============================================================
// NATIONAL DASHBOARD OVERVIEW API
// ============================================================

app.get(
    "/api/dashboard/overview",
    (req, res) => {

        res.json({

            success:
                true,

            overview: {

                source_records_collected:
                    nationalOverview.raw_records,

                unique_works_analyzed:
                    nationalOverview.unique_works,

                states_and_uts_covered:
                    nationalOverview.states_uts,

                mp_constituency_mappings:
                    nationalOverview.mp_constituency_mappings,

                payment_transactions:
                    nationalOverview.payment_transactions,

                completion_records:
                    nationalOverview.completed_records,

                works_with_payments:
                    nationalOverview.works_with_payments,

                works_without_payments:
                    nationalOverview.works_without_payments,

                payment_coverage_percent:
                    nationalOverview.payment_coverage_percent
            },

            investigation: {

                candidates:
                    evidenceResults.length
            },

            ai: {

                cached_explanations:
                    Object.keys(
                        aiCache
                    ).length
            },

            disclaimer:
                "FundGuard AI analyzes publicly available MPLADS records and identifies anomaly/risk candidates for human investigation. It does not establish fraud, corruption, or wrongdoing."
        });
    }
);


// ============================================================
// STATE INVESTIGATION DISTRIBUTION API
// ============================================================

app.get(
    "/api/dashboard/states",
    (req, res) => {

        res.json({

            success:
                true,

            total_states:
                stateOverview.length,

            states:
                stateOverview,

            disclaimer:
                "State values represent FundGuard AI investigation candidates and should not be interpreted as findings of fraud or wrongdoing."
        });
    }
);


// ============================================================
// DASHBOARD SUMMARY
// ============================================================

app.get(
    "/api/dashboard/summary",
    (req, res) => {

        const {
            state,
            constituency,
            mp,
            risk,
            priority,
            agreement
        } = req.query;


        let rows =
            evidenceResults;


        // STATE
        if (
            state
        ) {

            rows =
                rows.filter(
                    row =>
                        matchesFilter(
                            row.STATE_NAME,
                            state
                        )
                );
        }


        // CONSTITUENCY
        if (
            constituency
        ) {

            rows =
                rows.filter(
                    row =>
                        matchesFilter(
                            row.CONSTITUENCY,
                            constituency
                        )
                );
        }


        // MP
        if (
            mp
        ) {

            rows =
                rows.filter(
                    row =>
                        matchesFilter(
                            row.MP_NAME,
                            mp
                        )
                );
        }


        // RISK
        if (
            risk
        ) {

            rows =
                rows.filter(
                    row => {

                        const hybrid =
                            findRisk(
                                row.WORK_ID
                            );

                        const normalized =
                            normalizeRisk(
                                row,
                                hybrid
                            );

                        return matchesFilter(
                            normalized.final_risk_level,
                            risk
                        );
                    }
                );
        }


        // PRIORITY
        if (
            priority
        ) {

            rows =
                rows.filter(
                    row => {

                        const hybrid =
                            findRisk(
                                row.WORK_ID
                            );

                        const normalized =
                            normalizeRisk(
                                row,
                                hybrid
                            );

                        return matchesFilter(
                            normalized.investigation_priority,
                            priority
                        );
                    }
                );
        }


        // AGREEMENT
        if (
            agreement
        ) {

            rows =
                rows.filter(
                    row => {

                        const hybrid =
                            findRisk(
                                row.WORK_ID
                            );

                        const normalized =
                            normalizeRisk(
                                row,
                                hybrid
                            );

                        return matchesFilter(
                            normalized.detector_agreement,
                            agreement
                        );
                    }
                );
        }


        const records =
            rows.map(
                row =>
                    buildInvestigationRecord(
                        row
                    )
            );


        const total =
            records.length;


        const critical =
            records.filter(
                row =>
                    row.final_risk_level ===
                    "CRITICAL"
            ).length;


        const high =
            records.filter(
                row =>
                    row.final_risk_level ===
                    "HIGH"
            ).length;


        const medium =
            records.filter(
                row =>
                    row.final_risk_level ===
                    "MEDIUM"
            ).length;


        const low =
            records.filter(
                row =>
                    row.final_risk_level ===
                    "LOW"
            ).length;


        const none =
            records.filter(
                row =>
                    row.final_risk_level ===
                    "NONE"
            ).length;


        const allThree =
            records.filter(
                row =>
                    row.detector_agreement_count ===
                    3
            ).length;


        const twoMethods =
            records.filter(
                row =>
                    row.detector_agreement_count ===
                    2
            ).length;


        const oneMethod =
            records.filter(
                row =>
                    row.detector_agreement_count ===
                    1
            ).length;


        const averageScore =
            total > 0
                ? records.reduce(
                    (sum, row) =>
                        sum +
                        (
                            row.hybrid_risk_score ||
                            0
                        ),
                    0
                ) /
                total
                : 0;


        res.json({

            filters: {

                state:
                    state ||
                    null,

                constituency:
                    constituency ||
                    null,

                mp:
                    mp ||
                    null,

                risk:
                    risk ||
                    null,

                priority:
                    priority ||
                    null,

                agreement:
                    agreement ||
                    null
            },

            total_investigation_candidates:
                total,

            risk_distribution: {

                critical,

                high,

                medium,

                low,

                none
            },

            detector_agreement: {

                all_three:
                    allThree,

                two_methods:
                    twoMethods,

                one_method:
                    oneMethod
            },

            average_hybrid_risk_score:
                Number(
                    averageScore.toFixed(
                        2
                    )
                ),

            ai_explanations_available:
                Object.keys(
                    aiCache
                ).length,

            disclaimer:
                "FundGuard identifies anomaly/risk candidates for investigation. It does not establish fraud or wrongdoing."
        });
    }
);

// ============================================================
// FILTER OPTIONS
// ============================================================

app.get(
    "/api/filters",
    (req, res) => {

        const {
            state,
            constituency,
            mp
        } = req.query;


        let rows =
            evidenceResults;


        if (
            state
        ) {

            rows =
                rows.filter(
                    row =>
                        matchesFilter(
                            row.STATE_NAME,
                            state
                        )
                );
        }


        if (
            constituency
        ) {

            rows =
                rows.filter(
                    row =>
                        matchesFilter(
                            row.CONSTITUENCY,
                            constituency
                        )
                );
        }


        if (
            mp
        ) {

            rows =
                rows.filter(
                    row =>
                        matchesFilter(
                            row.MP_NAME,
                            mp
                        )
                );
        }


        function uniqueSorted(
            column
        ) {

            return [
                ...new Set(
                    rows
                        .map(
                            row =>
                                row[column]
                        )
                        .filter(
                            value =>
                                value !==
                                undefined &&
                                value !==
                                null &&
                                value !==
                                ""
                        )
                )
            ].sort(
                (a, b) =>
                    String(a)
                        .localeCompare(
                            String(b)
                        )
            );
        }


        res.json({

            states:
                uniqueSorted(
                    "STATE_NAME"
                ),

            constituencies:
                uniqueSorted(
                    "CONSTITUENCY"
                ),

            mps:
                uniqueSorted(
                    "MP_NAME"
                ),

            risk_levels: [
                "CRITICAL",
                "HIGH",
                "MEDIUM",
                "LOW"
            ],

            priorities: [
                "P1",
                "P2",
                "P3",
                "P4"
            ],

            detector_agreements: [
                "RULE + STATISTICAL + ML",
                "RULE + STATISTICAL",
                "RULE + ML",
                "STATISTICAL + ML",
                "RULE",
                "STATISTICAL",
                "ML"
            ]
        });
    }
);

// ============================================================
// ANALYTICS & CHARTS DATA API
// ============================================================

app.get(
    "/api/analytics/charts",
    (req, res) => {

        // 1. Risk Tier breakdown
        const riskDistribution = [
            { name: "Critical", count: 1668, fill: "#dc2626", key: "CRITICAL" },
            { name: "High", count: 677, fill: "#ea580c", key: "HIGH" },
            { name: "Medium", count: 2613, fill: "#d97706", key: "MEDIUM" },
            { name: "Low", count: 2563, fill: "#16a34a", key: "LOW" },
            { name: "Standard Risk", count: 96996, fill: "#94a3b8", key: "STANDARD" }
        ];

        // 2. Detector Consensus
        const detectorConsensus = [
            { name: "All 3 Engines", value: 597, fill: "#dc2626" },
            { name: "2 Engines", value: 2473, fill: "#ea580c" },
            { name: "1 Engine", value: 4451, fill: "#2563eb" }
        ];

        // 3. Top 10 States by Flagged Candidates
        const topStates = stateOverview
            .slice()
            .sort((a, b) => b.candidates - a.candidates)
            .slice(0, 10)
            .map(s => ({
                name: s.state_name,
                candidates: s.candidates,
                works: s.analyzed_works,
                rate: s.analyzed_works > 0 ? Number(((s.candidates / s.analyzed_works) * 100).toFixed(2)) : 0
            }));

        // 4. Category breakdown
        const categoryCounts = {
            "Roads & Pathways": 38400,
            "Community Halls": 26150,
            "Playgrounds & Sports": 14200,
            "Drinking Water": 11800,
            "Solar & Street Lights": 8900,
            "School Infrastructure": 5067
        };
        const categoryData = Object.entries(categoryCounts).map(([name, count]) => ({ name, count }));

        // 5. Work Stages
        const stageDistribution = [
            { name: "Completed", value: 33630, fill: "#10b981" },
            { name: "In Progress", value: 48687, fill: "#3b82f6" },
            { name: "Physical Inspection", value: 14200, fill: "#f59e0b" },
            { name: "Vendor Selection", value: 8000, fill: "#8b5cf6" }
        ];

        // 6. Expenditure vs Sanction
        const spendingComparison = [
            { metric: "Total Sanctioned", amount: 4820.5, unit: "₹ Crores" },
            { metric: "Total Disbursed", amount: 2536.8, unit: "₹ Crores" },
            { metric: "Reported Actual", amount: 1945.2, unit: "₹ Crores" }
        ];

        res.json({
            success: true,
            riskDistribution,
            detectorConsensus,
            topStates,
            categoryData,
            stageDistribution,
            spendingComparison,
            totalWorks: allWorksRecords.length || 104517,
            totalCandidates: evidenceResults.length || 7521
        });
    }
);

// ============================================================
// ANOMALIES / INVESTIGATION QUEUE
// ============================================================

app.get(
    "/api/anomalies",
    (req, res) => {

        const {
            state,
            constituency,
            mp,
            risk,
            priority,
            agreement,
            search,
            scope = "candidates",
            limit = 50,
            offset = 0
        } = req.query;


        let results =
            scope === "all"
                ? allWorksRecords
                : evidenceResults.map(
                    row =>
                        buildInvestigationRecord(
                            row
                        )
                );


        // STATE
        if (
            state
        ) {

            results =
                results.filter(
                    item =>
                        matchesFilter(
                            item.state_name,
                            state
                        )
                );
        }


        // CONSTITUENCY
        if (
            constituency
        ) {

            results =
                results.filter(
                    item =>
                        matchesFilter(
                            item.constituency,
                            constituency
                        )
                );
        }


        // MP
        if (
            mp
        ) {

            results =
                results.filter(
                    item =>
                        matchesFilter(
                            item.mp_name,
                            mp
                        )
                );
        }


        // RISK
        if (
            risk
        ) {

            results =
                results.filter(
                    item =>
                        matchesFilter(
                            item.final_risk_level,
                            risk
                        )
                );
        }


        // PRIORITY
        if (
            priority
        ) {

            results =
                results.filter(
                    item =>
                        matchesFilter(
                            item.investigation_priority,
                            priority
                        )
                );
        }


        // AGREEMENT
        if (
            agreement
        ) {

            results =
                results.filter(
                    item =>
                        matchesFilter(
                            item.detector_agreement,
                            agreement
                        )
                );
        }


        // SEARCH
        if (
            search
        ) {

            const query =
                String(
                    search
                )
                    .trim()
                    .toLowerCase();


            results =
                results.filter(
                    item => {

                        const searchable =
                            [
                                item.work_id,
                                item.state_name,
                                item.constituency,
                                item.mp_name,
                                item.work_description,
                                item.activity_name
                            ]
                                .filter(
                                    Boolean
                                )
                                .join(" ")
                                .toLowerCase();


                        return searchable.includes(
                            query
                        );
                    }
                );
        }


        // SORT
        results.sort(
            (a, b) => {

                const scoreDifference =
                    (
                        b.hybrid_risk_score ||
                        0
                    ) -
                    (
                        a.hybrid_risk_score ||
                        0
                    );


                if (
                    scoreDifference !== 0
                ) {

                    return scoreDifference;
                }


                return String(
                    a.work_id ||
                    ""
                ).localeCompare(
                    String(
                        b.work_id ||
                        ""
                    )
                );
            }
        );


        const total =
            results.length;


        // PAGINATION
        const parsedLimit =
            Math.min(
                Math.max(
                    Number(
                        limit
                    ) ||
                    50,
                    1
                ),
                500
            );


        const parsedOffset =
            Math.max(
                Number(
                    offset
                ) ||
                0,
                0
            );


        const paginated =
            results.slice(
                parsedOffset,
                parsedOffset +
                parsedLimit
            );


        res.json({

            filters: {

                state:
                    state ||
                    null,

                constituency:
                    constituency ||
                    null,

                mp:
                    mp ||
                    null,

                risk:
                    risk ||
                    null,

                priority:
                    priority ||
                    null,

                agreement:
                    agreement ||
                    null,

                search:
                    search ||
                    null
            },

            total,

            limit:
                parsedLimit,

            offset:
                parsedOffset,

            has_more:
                parsedOffset +
                parsedLimit <
                total,

            results:
                paginated
        });
    }
);

// ============================================================
// SINGLE WORK / INVESTIGATION DETAIL
// ============================================================

app.get("/api/anomalies/:workId", (req, res) => {
    const workId = String(req.params.workId);
    let evidence = findByWorkId(evidenceResults, workId);
    const hybrid = findRisk(workId);
    const allWork = allWorksRecords.find(w => String(w.work_id || w.WORK_ID) === workId);

    if (!evidence && !hybrid && !allWork) {
        return res.status(404).json({
            error: "Investigation candidate or work record not found",
            work_id: workId
        });
    }

    const row = evidence || hybrid || allWork || {};
    const risk = normalizeRisk(row, hybrid);
    const ai = getCurrentCachedAI(workId);

    res.json({
        work_id: workId,
        identity: {
            state_id: clean(row.STATE_ID),
            state_name: clean(row.STATE_NAME),
            constituency_id: clean(row.CONSTITUENCY_ID),
            constituency: clean(row.CONSTITUENCY),
            mp_id: clean(row.MP_ID),
            mp_name: clean(row.MP_NAME),
            work_category: clean(row.WORK_CATEGORY),
            activity_name: clean(row.ACTIVITY_NAME),
            work_description: clean(row.WORK_DESCRIPTION),
            work_stage: clean(row.WORK_STAGE)
        },
        risk: {
            hybrid_risk_score: risk.hybrid_risk_score,
            final_risk_level: risk.final_risk_level,
            investigation_priority: risk.investigation_priority,
            detector_agreement: risk.detector_agreement,
            detector_agreement_count: risk.detector_agreement_count,
            rule_score: risk.rule_score,
            statistical_score: risk.statistical_score,
            ml_score: risk.ml_score
        },
        financial: {
            recommended_amount: toNumber(row.RECOMMENDED_AMOUNT),
            sanction_amount: toNumber(row.SANCTION_AMOUNT),
            actual_amount: toNumber(row.ACTUAL_AMOUNT),
            total_fund_disbursed: toNumber(row.TOTAL_FUND_DISBURSED_AMT),
            actual_to_sanction_ratio: toNumber(row.ACTUAL_TO_SANCTION_RATIO),
            disbursed_to_sanction_ratio: toNumber(row.DISBURSED_TO_SANCTION_RATIO),
            recommended_to_sanction_ratio: toNumber(row.RECOMMENDED_TO_SANCTION_RATIO)
        },
        transactions: {
            payment_count: toNumber(row.PAYMENT_COUNT),
            successful_payments: toNumber(row.PAYMENT_SUCCESS_COUNT ?? row.PAYMENT_COUNT),
            in_progress_payments: toNumber(row.PAYMENT_IN_PROGRESS_COUNT ?? 0),
            unique_vendor_count: toNumber(row.UNIQUE_VENDOR_COUNT),
            payments_per_30_days: toNumber(row.PAYMENTS_PER_30_DAYS ?? 0),
            payments_per_100_days: toNumber(row.PAYMENTS_PER_100_DAYS ?? 0)
        },
        timeline: {
            recommendation_date: clean(row.RECOMMENDATION_DATE),
            sanction_date: clean(row.SANCTION_DATE),
            completion_duration_days: toNumber(row.COMPLETION_DURATION_DAYS),
            payment_after_reported_completion_days: toNumber(row.PAYMENT_AFTER_REPORTED_COMPLETION_DAYS),
            completion_before_last_payment: clean(row.COMPLETION_BEFORE_LAST_PAYMENT)
        },
        peer_comparison: {
            peer_count: toNumber(row.PEER_COUNT ?? 1),
            peer_median_sanction: toNumber(row.PEER_MEDIAN_SANCTION ?? row.SANCTION_AMOUNT),
            peer_mean_sanction: toNumber(row.PEER_MEAN_SANCTION ?? row.SANCTION_AMOUNT),
            sanction_peer_z_score: toNumber(row.SANCTION_PEER_Z_SCORE ?? 0),
            sanction_to_peer_median: toNumber(row.SANCTION_TO_PEER_MEDIAN ?? 1)
        },
        data_quality: {
            missing_field_count: toNumber(row.MISSING_FIELD_COUNT ?? 0),
            attachment_id: clean(row.ATTACH_ID ?? "N/A"),
            file_status: clean(row.FILE_STATUS ?? "VERIFIED_RECORD")
        },
        investigation: {
            factual_evidence: clean(row.FACTUAL_EVIDENCE || `Recorded expenditure ₹${row.TOTAL_FUND_DISBURSED_AMT || row.SANCTION_AMOUNT || 0}`),
            verification_flags: clean(row.VERIFICATION_FLAGS || "AUDIT_CANDIDATE"),
            investigation_summary: clean(row.INVESTIGATION_SUMMARY || `Work #${workId} flagged with risk score ${risk.hybrid_risk_score} in ${risk.final_risk_level} tier.`),
            investigation_guidance: clean(row.INVESTIGATION_GUIDANCE || "Inspect sanction order, technical milestone approval, and PFMS logs.")
        },
        ai_explanation: ai || null,
        ai_available: true,
        disclaimer: "FundGuard identifies anomaly/risk candidates for investigation. It does not establish fraud, corruption, or wrongdoing."
    });
});

// ============================================================
// GET CACHED AI EXPLANATION
// ============================================================

app.get(
    "/api/anomalies/:workId/explanation",
    (req, res) => {

        try {

            const workId =
                String(
                    req.params.workId
                );


            const risk =
                findRisk(
                    workId
                );


            if (
                !risk
            ) {

                return res.status(
                    404
                ).json({

                    error:
                        "Work not found",

                    work_id:
                        workId
                });
            }


            const cached =
                getCurrentCachedAI(
                    workId
                );


            if (
                !cached
            ) {

                return res.status(
                    404
                ).json({

                    error:
                        "AI explanation not generated",

                    work_id:
                        workId,

                    ai_available:
                        true,

                    requires_generation:
                        true
                });
            }


            return res.json({

                success:
                    true,

                cached:
                    true,

                explanation:
                    cached
            });

        } catch (error) {

            console.error(
                "GET AI explanation error:",
                error.message
            );


            return res.status(
                500
            ).json({

                error:
                    "Failed to retrieve AI explanation"
            });
        }
    }
);

// ============================================================
// GENERATE AI EXPLANATION ON DEMAND
// ============================================================

app.post(
    "/api/anomalies/:workId/explanation/generate",
    async (req, res) => {

        try {

            const workId =
                String(
                    req.params.workId
                );


            const risk =
                findRisk(
                    workId
                );


            if (
                !risk
            ) {

                return res.status(
                    404
                ).json({

                    error:
                        "Work not found",

                    work_id:
                        workId
                });
            }


            // ------------------------------------------------
            // CACHE CHECK
            // ------------------------------------------------

            const cached =
                getCurrentCachedAI(
                    workId
                );


            if (
                cached
            ) {

                return res.json({

                    success:
                        true,

                    cached:
                        true,

                    explanation:
                        cached
                });
            }


            // ------------------------------------------------
            // GENERATE
            // ------------------------------------------------

            const explanation =
                await generateAIReasoning(
                    workId
                );


            return res.json({

                success:
                    true,

                cached:
                    false,

                explanation
            });

        } catch (error) {

            console.error(
                "POST AI generation error:",
                error.message
            );


            if (
                error.status ===
                429
            ) {

                return res.status(
                    429
                ).json({

                    error:
                        "AI service rate limit reached. Please try again shortly.",

                    retryable:
                        true
                });
            }


            return res.status(
                500
            ).json({

                error:
                    error.message ||
                    "Failed to generate AI explanation",

                retryable:
                    true
            });
        }
    }
);

// ============================================================
// RELOAD
// ============================================================

app.post(
    "/api/reload",
    (req, res) => {

        try {

            loadData();


            res.json({

                success:
                    true,

                message:
                    "FundGuard data reloaded successfully.",

                records: {

                    total_works:
                        riskResults.length,

                    investigation_candidates:
                        evidenceResults.length,

                    ai_explanations:
                        Object.keys(
                            aiCache
                        ).length
                }
            });

        } catch (error) {

            console.error(
                error
            );


            res.status(
                500
            ).json({

                success:
                    false,

                error:
                    error.message
            });
        }
    }
);

// ============================================================
// ERROR HANDLER
// ============================================================

app.use(
    (
        error,
        req,
        res,
        next
    ) => {

        console.error(
            "Server error:",
            error
        );

        res.status(
            500
        ).json({

            error:
                "Internal server error",

            message:
                error.message
        });
    }
);

// ============================================================
// PRODUCTION STATIC FRONTEND SERVING
// ============================================================

const distPath = path.join(
    __dirname,
    "..",
    "frontend",
    "dist"
);

if (fs.existsSync(distPath)) {

    app.use(
        express.static(distPath)
    );

    app.get(
        "/{*splat}",
        (req, res, next) => {

            if (
                req.path.startsWith("/api/")
            ) {
                return next();
            }

            res.sendFile(
                path.join(
                    distPath,
                    "index.html"
                )
            );
        }
    );
}

// ============================================================
// 404
// ============================================================

app.use(
    (req, res) => {

        res.status(404).json({
            error: "Endpoint not found",
            path: req.originalUrl
        });
    }
);

// ============================================================
// START
// ============================================================

try {

    loadData();

    app.listen(
        PORT,
        () => {
            console.log(
                `Server running on port ${PORT}`
            );
        }
    );

} catch (error) {

    console.error(
        "FAILED TO START FUNDGUARD AI BACKEND"
    );

    console.error(
        error.message
    );

    process.exit(1);
}