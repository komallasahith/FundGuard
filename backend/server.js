const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");
const { parse } = require("csv-parse/sync");

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

const RISK_FILE = path.join(
    OUTPUT_DIR,
    "fundguard_risk_results.csv"
);

const EVIDENCE_FILE = path.join(
    OUTPUT_DIR,
    "fundguard_evidence.json"
);

const AI_FILE = path.join(
    OUTPUT_DIR,
    "fundguard_ai_explanations.json"
);

// ============================================================
// IN-MEMORY DATA
// ============================================================

let riskResults = [];
let evidenceResults = [];
let aiResults = [];

// ============================================================
// LOAD DATA
// ============================================================

function loadData() {

    console.log("");
    console.log("Loading FundGuard data...");

    // --------------------------------------------------------
    // Risk results CSV
    // --------------------------------------------------------

    if (!fs.existsSync(RISK_FILE)) {
        throw new Error(
            `Risk file not found: ${RISK_FILE}`
        );
    }

    const riskCsv = fs.readFileSync(
        RISK_FILE,
        "utf-8"
    );

    riskResults = parse(
        riskCsv,
        {
            columns: true,
            skip_empty_lines: true,
            bom: true
        }
    );

    // --------------------------------------------------------
    // Evidence JSON
    // --------------------------------------------------------

    if (!fs.existsSync(EVIDENCE_FILE)) {
        throw new Error(
            `Evidence file not found: ${EVIDENCE_FILE}`
        );
    }

    evidenceResults = JSON.parse(
        fs.readFileSync(
            EVIDENCE_FILE,
            "utf-8"
        )
    );

    // --------------------------------------------------------
    // AI explanations
    // --------------------------------------------------------

    if (fs.existsSync(AI_FILE)) {

        aiResults = JSON.parse(
            fs.readFileSync(
                AI_FILE,
                "utf-8"
            )
        );

    } else {

        console.log(
            "AI explanation file not found."
        );

        aiResults = [];
    }

    console.log(
        `Risk results : ${riskResults.length.toLocaleString()}`
    );

    console.log(
        `Evidence     : ${evidenceResults.length.toLocaleString()}`
    );

    console.log(
        `AI results   : ${aiResults.length.toLocaleString()}`
    );

    console.log("Data loaded successfully.");
    console.log("");
}

// ============================================================
// HELPERS
// ============================================================

function toNumber(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return null;
    }

    const number = Number(value);

    return Number.isFinite(number)
        ? number
        : null;
}


function findEvidence(workId) {

    return evidenceResults.find(
        item =>
            String(item.work_id) ===
            String(workId)
    );
}


function findAI(workId) {

    return aiResults.find(
        item =>
            String(item.work_id) ===
            String(workId)
    );
}


function normalizeRisk(row) {

    return {

        work_id:
            row.WORK_RECOMMENDATION_DTL_ID,

        hybrid_risk_score:
            toNumber(
                row.HYBRID_RISK_SCORE
            ),

        final_risk_level:
            row.FINAL_RISK_LEVEL,

        detector_agreement:
            row.DETECTOR_AGREEMENT,

        detector_agreement_count:
            toNumber(
                row.DETECTOR_AGREEMENT_COUNT
            ),

        investigation_priority:
            toNumber(
                row.INVESTIGATION_PRIORITY
            ),

        rule_score:
            toNumber(
                row.RULE_SCORE
            ),

        statistical_score:
            toNumber(
                row.STATISTICAL_SCORE
            ),

        ml_score:
            toNumber(
                row.ML_SCORE
            )
    };
}


// ============================================================
// HEALTH
// ============================================================

app.get(
    "/api/health",
    (req, res) => {

        res.json({

            status: "ok",

            service:
                "FundGuard AI Backend",

            timestamp:
                new Date().toISOString(),

            data_loaded: true,

            records: {
                risk_results:
                    riskResults.length,

                evidence:
                    evidenceResults.length,

                ai_explanations:
                    aiResults.length
            }
        });
    }
);


// ============================================================
// DASHBOARD SUMMARY
// ============================================================

app.get(
    "/api/dashboard/summary",
    (req, res) => {

        const total =
            riskResults.length;


        const high =
            riskResults.filter(
                row =>
                    String(
                        row.FINAL_RISK_LEVEL
                    ).toUpperCase() === "HIGH"
            ).length;


        const medium =
            riskResults.filter(
                row =>
                    String(
                        row.FINAL_RISK_LEVEL
                    ).toUpperCase() === "MEDIUM"
            ).length;


        const low =
            riskResults.filter(
                row =>
                    String(
                        row.FINAL_RISK_LEVEL
                    ).toUpperCase() === "LOW"
            ).length;


        const strongAgreement =
            riskResults.filter(
                row =>
                    String(
                        row.DETECTOR_AGREEMENT
                    ).toUpperCase() === "STRONG"
            ).length;


        const moderateAgreement =
            riskResults.filter(
                row =>
                    String(
                        row.DETECTOR_AGREEMENT
                    ).toUpperCase() === "MODERATE"
            ).length;


        const singleDetector =
            riskResults.filter(
                row =>
                    String(
                        row.DETECTOR_AGREEMENT
                    ).toUpperCase() ===
                    "SINGLE_DETECTOR"
            ).length;


        const averageRisk =
            total > 0
                ? riskResults.reduce(
                    (sum, row) =>
                        sum +
                        (
                            toNumber(
                                row.HYBRID_RISK_SCORE
                            ) || 0
                        ),
                    0
                ) / total
                : 0;


        res.json({

            total_works_analyzed:
                total,

            risk_distribution: {

                high,

                medium,

                low
            },

            detector_agreement: {

                strong:
                    strongAgreement,

                moderate:
                    moderateAgreement,

                single_detector:
                    singleDetector
            },

            average_hybrid_risk_score:
                Number(
                    averageRisk.toFixed(2)
                ),

            ai_explanations_available:
                aiResults.length,

            last_loaded:
                new Date().toISOString(),

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

        const riskLevels = [
            ...new Set(
                riskResults
                    .map(
                        row =>
                            row.FINAL_RISK_LEVEL
                    )
                    .filter(Boolean)
            )
        ];


        const agreements = [
            ...new Set(
                riskResults
                    .map(
                        row =>
                            row.DETECTOR_AGREEMENT
                    )
                    .filter(Boolean)
            )
        ];


        res.json({

            risk_levels:
                riskLevels,

            detector_agreements:
                agreements
        });
    }
);


// ============================================================
// ANOMALIES LIST
// ============================================================

app.get(
    "/api/anomalies",
    (req, res) => {

        const {
            risk,
            agreement,
            limit = 50,
            offset = 0
        } = req.query;


        let results =
            riskResults.map(
                normalizeRisk
            );


        // ----------------------------------------------------
        // Risk filter
        // ----------------------------------------------------

        if (risk) {

            results =
                results.filter(
                    item =>
                        String(
                            item.final_risk_level
                        ).toUpperCase() ===
                        String(
                            risk
                        ).toUpperCase()
                );
        }


        // ----------------------------------------------------
        // Agreement filter
        // ----------------------------------------------------

        if (agreement) {

            results =
                results.filter(
                    item =>
                        String(
                            item.detector_agreement
                        ).toUpperCase() ===
                        String(
                            agreement
                        ).toUpperCase()
                );
        }


        // ----------------------------------------------------
        // Sort highest risk first
        // ----------------------------------------------------

        results.sort(
            (a, b) =>
                (b.hybrid_risk_score || 0) -
                (a.hybrid_risk_score || 0)
        );


        const total =
            results.length;


        const parsedLimit =
            Math.min(
                Math.max(
                    Number(limit) || 50,
                    1
                ),
                500
            );


        const parsedOffset =
            Math.max(
                Number(offset) || 0,
                0
            );


        const paginated =
            results.slice(
                parsedOffset,
                parsedOffset + parsedLimit
            );


        // ----------------------------------------------------
        // Add evidence identity
        // ----------------------------------------------------

        const enriched =
            paginated.map(
                item => {

                    const evidence =
                        findEvidence(
                            item.work_id
                        );


                    return {

                        ...item,

                        mp_name:
                            evidence?.identity?.mp_name
                            || null,

                        constituency:
                            evidence?.identity?.constituency
                            || null,

                        work_category:
                            evidence?.identity?.work_category
                            || null,

                        activity_name:
                            evidence?.identity?.activity_name
                            || null,

                        summary:
                            evidence?.summary
                            || null
                    };
                }
            );


        res.json({

            total,

            limit:
                parsedLimit,

            offset:
                parsedOffset,

            results:
                enriched
        });
    }
);


// ============================================================
// SINGLE ANOMALY
// ============================================================

app.get(
    "/api/anomalies/:workId",
    (req, res) => {

        const workId =
            req.params.workId;


        const risk =
            riskResults.find(
                row =>
                    String(
                        row.WORK_RECOMMENDATION_DTL_ID
                    ) ===
                    String(workId)
            );


        if (!risk) {

            return res.status(404).json({

                error:
                    "Work not found",

                work_id:
                    workId
            });
        }


        const evidence =
            findEvidence(
                workId
            );


        const ai =
            findAI(
                workId
            );


        res.json({

            work_id:
                workId,

            risk:
                normalizeRisk(
                    risk
                ),

            identity:
                evidence?.identity
                || null,

            financial:
                evidence?.financial
                || null,

            statistical:
                evidence?.statistical
                || null,

            transactions:
                evidence?.transactions
                || null,

            timeline:
                evidence?.timeline
                || null,

            evidence:
                evidence?.evidence
                || null,

            summary:
                evidence?.summary
                || null,

            investigation_guidance:
                evidence?.investigation_guidance
                || null,

            ai_explanation:
                ai
                || null,

            disclaimer:
                evidence?.disclaimer
                ||
                "This system identifies anomaly/risk candidates for investigation. It does not establish fraud or wrongdoing."
        });
    }
);


// ============================================================
// AI EXPLANATION
// ============================================================

app.get(
    "/api/anomalies/:workId/explanation",
    (req, res) => {

        const workId =
            req.params.workId;


        const ai =
            findAI(
                workId
            );


        if (!ai) {

            return res.status(404).json({

                error:
                    "AI explanation not available",

                work_id:
                    workId
            });
        }


        res.json(
            ai
        );
    }
);


// ============================================================
// RELOAD DATA
// ============================================================

app.post(
    "/api/reload",
    (req, res) => {

        try {

            loadData();

            res.json({

                success: true,

                message:
                    "FundGuard data reloaded successfully.",

                records: {

                    risk_results:
                        riskResults.length,

                    evidence:
                        evidenceResults.length,

                    ai_explanations:
                        aiResults.length
                }
            });

        } catch (error) {

            console.error(error);

            res.status(500).json({

                success: false,

                error:
                    error.message
            });
        }
    }
);


// ============================================================
// 404 HANDLER
// ============================================================

app.use(
    (req, res) => {

        res.status(404).json({

            error:
                "Endpoint not found",

            path:
                req.originalUrl
        });
    }
);


// ============================================================
// ERROR HANDLER
// ============================================================

app.use(
    (error, req, res, next) => {

        console.error(
            "Server error:",
            error
        );

        res.status(500).json({

            error:
                "Internal server error",

            message:
                error.message
        });
    }
);


// ============================================================
// LOAD + START
// ============================================================

try {

    loadData();

    app.listen(
        PORT,
        () => {

            console.log(
                "============================================================"
            );

            console.log(
                "FUNDGUARD AI BACKEND"
            );

            console.log(
                "============================================================"
            );

            console.log(
                `Server running on http://localhost:${PORT}`
            );

            console.log(
                "============================================================"
            );
        }
    );

} catch (error) {

    console.error("");
    console.error(
        "FAILED TO START FUNDGUARD BACKEND"
    );
    console.error("");
    console.error(
        error.message
    );
    console.error("");

    process.exit(1);
}