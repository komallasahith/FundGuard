# 🛡️ FundGuard AI — National Financial Intelligence & Forensic Triage Platform

> **GovTech Financial Integrity & Anomaly Triage for the Members of Parliament Local Area Development Scheme (MPLADS)**  
> *Built for transparency, audit efficiency, and forensic triage across 36 States/UTs and 543 Parliamentary Constituencies.*

[![Official MPLADS Portal](https://img.shields.io/badge/Official_Portal-mplads.gov.in-1d4ed8.svg?style=flat&logo=gov.uk)](https://mplads.gov.in/)
[![Engine Status](https://img.shields.io/badge/Tri--Detector-Operational-16a34a.svg?style=flat)]()
[![LLM Reasoning](https://img.shields.io/badge/LLM_Reasoning-Groq_Llama_3.3_70B-purple.svg?style=flat)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat)]()

---

## 🏛️ Executive Summary

**FundGuard AI** is an end-to-end national financial intelligence and multi-detector anomaly detection platform designed to audit public development expenditures under MPLADS. 

Instead of relying on simplistic threshold alerts or opaque "black-box" models, FundGuard combines **Deterministic Policy Rules**, **Peer-Cohort Statistical IQR / Z-Score Analysis**, **Unsupervised Isolation Forest Machine Learning**, and **Generative LLM Forensic Reasoning** to triage millions of public funds across India.

Every flagged record is backed by **objective mathematical evidence**, **investigation guidance**, and **factual policy references** to assist human auditors and parliamentary monitoring committees.

---

## 📊 National Data Telemetry

| Metric | Official Count | Description |
| :--- | :--- | :--- |
| 📥 **Raw Source Records** | **297,398** | Ingested across state-wise recommendations, sanctions, completions, and expenditures. |
| 🏗️ **Canonical Works Audited** | **104,517** | Deduplicated, cross-verified unique developmental works. |
| 🚩 **Flagged Investigation Queue** | **7,521** | High & critical anomaly candidates identified by consensus detection. |
| 💳 **Payment Transactions Analyzed** | **82,320** | Disbursed milestone tranches and vendor payment ledger records. |
| 🏛️ **States & Union Territories** | **36** | Complete national geospatial coverage (all 6 geographic zones). |
| 📍 **Parliamentary Constituencies** | **529** | MP-to-constituency allocation records indexed. |
| 🔗 **Official Data Source** | [mplads.gov.in](https://mplads.gov.in/) | Ministry of Statistics and Programme Implementation (MoSPI). |

---

## ⚙️ Layered Detection Architecture

```
                                OFFICIAL MPLADS DATA (MoSPI)
                                            │
                                            ▼
                              Data Collection & Ingestion
                                (297,398 Raw Records)
                                            │
                                            ▼
                              Validation & Deduplication
                                (104,517 Canonical Works)
                                            │
                                            ▼
                              Forensic Feature Engineering
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
         [1] Deterministic Rules   [2] Statistical Cohorts  [3] ML Isolation Forest
           - Split Billing Rules     - Peer-Median Deviation   - Outlier Anomaly Score
           - Negative Timelines      - Sanction Z-Score (IQR)  - High-Dim Variance
           - Milestone Disconnects   - Regional Cost Skew      - Multi-Feature Density
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            ▼
                                Hybrid Consensus Scoring
                                 (0 – 100 Multi-Signal)
                                            │
                                            ▼
                                Structured Evidence Dossier
                                            │
                                            ▼
                              Groq LLM Forensic Reasoning
                          (Llama-3.3-70B + Deterministic Fallback)
                                            │
                                            ▼
                                Human Investigation Queue
```

---

## 🌟 Key Features & Modules

### 1. 🇮🇳 High-Performance Geo-Spatial Survey India Map (60 FPS)
- **Authentic Survey-Grade Geometry**: Accurate national boundaries (Jammu & Kashmir/Ladakh, North-Eastern states, Gujarat coastline, Southern peninsula).
- **6 Zonal Palettes**: Northern (`#E06D53`), Central (`#E9BA62`), Eastern (`#DDE662`), Western (`#9FCB96`), Southern (`#DF6797`), and North Eastern (`#A779B4`).
- **State Deep-Dive & Parliamentary Constituencies**: Clicking any state opens a dedicated sub-panel detailing each parliamentary seat, MP name, sanctioned budget (₹ Cr), flagged anomaly count, and direct link to audit records.
- **Optimized Performance**: Vector paths compressed to <160KB, running at zero-lag 60 FPS.

### 2. 🤖 Zero-Cost Generative LLM Forensic Reasoning
- **Groq Cloud API Integration**: Instantaneous generation of executive synthesis, policy violation breakdowns, and auditor recommendations using `llama-3.3-70b-versatile` / `openai/gpt-oss-120b`.
- **Dual In-Memory & Disk Caching**: Explanations are cached in memory and saved to `india_llm_explanations_cache.json` so repeated queries never incur token costs.
- **Deterministic Synthetic Engine (100% Offline Fallback)**: If offline or rate-limited, the backend dynamically constructs a complete forensic report using rule and statistical metrics.

### 3. 📈 Visual Analytics & Diagnostic Suite
- **6 Real-time Analytical Charts**:
  - Risk Level Distribution (Critical, High, Medium, Low)
  - Multi-Detector Signal Agreement Matrix
  - Top 10 High-Risk States
  - Cost vs Peer-Cohort Median Scatter
  - Disbursement-to-Sanction Ratio Histogram
  - Transaction Volume vs Value Distribution

### 4. 📋 Investigation Queue & Works Explorer
- Instant search and filtering across **104,517** canonical works.
- Filter by State, Risk Level, Detector Agreement, Work Category, and Search keywords.
- Detailed Anomaly Dossier Drawer with timeline visualizer, peer comparison, vendor analytics, and one-click JSON/CSV export.

---

## 🚀 Quickstart — Running Locally

### Prerequisites
- Node.js (v18 or higher)
- Python (v3.9 or higher)

### 1. Clone the Repository
```bash
git clone https://github.com/komallasahith/FundGuard.git
cd FundGuard
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
PORT=5000
NODE_ENV=development
GROQ_API_KEY=gsk_your_groq_api_key_here
```
*(Get a free Groq API key with zero credit card at [console.groq.com](https://console.groq.com/))*

### 3. Start the Backend Server
```bash
cd backend
npm install
node server.js
```
*Backend runs on `http://localhost:5000`.*

### 4. Start the Frontend Development Server
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`.*

---

## 🧮 Multi-Detector Calibration & Scoring Formula

To ensure semantic compatibility across all three detection engines, raw detector signals are calibrated into **uniform percentile ranks [0, 100]** prior to consensus combination:

$$\text{Rule}_{\text{cal}} = \text{PercentileRank}_{\text{firing}}(\text{Rule Score}) \times 100 \quad (\text{if } \text{Rule Score} > 0, 0 \text{ otherwise})$$
$$\text{Stat}_{\text{cal}} = \text{PercentileRank}_{\text{firing}}(\text{Stat Score}) \times 100 \quad (\text{if } \text{Stat Score} > 0, 0 \text{ otherwise})$$
$$\text{ML}_{\text{cal}} = \text{PercentileRank}_{\text{all}}(\text{Anomaly Strength}) \times 100 \quad [0, 100]$$

> [!NOTE]
> **Calibration Subset Definition**: Percentile ranks for Rules and Statistics are computed strictly within their respective **detector-firing subsets** ($\text{Score} > 0$), and non-firing works receive $0.0$. This ensures calibration stability independent of downstream queue filtering.

### Unbiased Multi-Detector Fusion (Option B Score Regimes)
To prevent systematic cross-region ranking distortion and avoid artificially over-rewarding sparse-cohort works:
$$\text{Hybrid Risk Score} = 0.35 \times \text{Rule}_{\text{cal}} + 0.35 \times \text{Stat}_{\text{cal}} + 0.30 \times \text{ML}_{\text{cal}} + \text{Agreement Bonus}$$
*Where Agreement Bonus = $+10.0$ if all 3 detectors agree, $+5.0$ if 2 detectors agree. Score is capped at 100.*

- **Standard Regime (`SCORE_REGIME="STANDARD"`, $\ge 10$ peers)**: Full 3-detector consensus analysis.
- **Sparse Peer Regime (`SCORE_REGIME="SPARSE_PEER"`, $< 10$ peers)**: Statistical peer comparisons are suppressed ($\text{Stat}_{\text{cal}} = 0$) **without** renormalizing the remaining weights — Rules and ML retain their fixed 0.35 and 0.30 weights, preserving cross-region comparability at the cost of a lower maximum achievable score for sparse-peer works.
- **ML Isolation Forest Contamination**:
  Configured with `contamination="auto"` (the established heuristic threshold from Liu et al., 2008), ensuring unconstrained outlier scoring on the multidimensional feature matrix.

### Batch 4 Pyramid Tier Thresholds & Framing (Option B Calibration)
Grid-search calibrated thresholds across 7,521 investigation candidates to establish an operational triage pyramid:

| Tier | Primary Driver & Assignment Rule | Count | % | Signal Composition |
|:-----|:---------------------------------|------:|--:|:-------------------|
| **P1 — Critical** | **3-Engine Consensus** (597) **+ Score ≥ 90.4 Tail** (87) | 684 | 9.1% | 597 3-signal + 87 2-signal |
| **P2 — High** | Score 56.5–90.4 (High dual-engine deviations) | 1,302 | 17.3% | 1,250 2-signal + 52 1-signal |
| **P3 — Medium** | Score 35.0–56.5 (Balanced anomaly signals) | 2,415 | 32.1% | 1,119 2-signal + 1,296 1-signal |
| **P4 — Low** | Score 0.1–35.0 (Single-detector baseline signals) | 3,120 | 41.5% | 17 2-signal + 3,103 1-signal |

> [!NOTE]
> **Architectural Framing (Option B)**:
> P1 is defined primarily by **3-engine detector consensus** (all 597 works where Rules, Statistical, and ML engines concur are elevated unconditionally via a hard-override constraint). The 90.4 score threshold applies specifically to the non-consensus tail: works firing fewer than 3 detectors cannot reach this score without extreme dual-engine statistical and rule outlier values, contributing 87 additional high-priority candidates. This separation preserves score-based discrimination for future detector extensions while guaranteeing consensus works top priority.

---

## 🔬 Peer Cohort Methodology & Limitations

- **Grouping Hierarchy**: Works are categorized by `State` $\rightarrow$ `Work Category`.
- **Sample Sufficiency**: Statistical IQR and Z-scores require $\ge 10$ peer records (`PEER_DATA_SUFFICIENT = True`). Works with $<10$ peers are categorized into `SPARSE_PEER` and evaluated via verified rule and ML signals.
- **Data Quality Tiers**: Records are classified as `HIGH` (0 missing fields), `MEDIUM` (1 missing field), or `LOW` ($\ge 2$ missing fields) to signal data completeness to investigators.
- **Methodological Limitation**: Peer comparisons do not dynamically model district-level construction cost index (CPWD DSR) or remote hill terrain material transport surcharges.

---

## 🧪 Automated Unit & Golden Regression Test Suite

FundGuard includes an automated 19-test suite with CI validation covering score calibration, generalized deduplication, peer sufficiency, data quality tiers, consensus P1 override, and golden snapshot regression:

```bash
python -m unittest discover tests/ -v
```
*(All 19 test cases pass with 100% coverage).*

- **Golden Snapshot Tests**:
  - **Top-10 Flagged Works**: Asserts snapshot integrity (`313337`, `312966`, `284190`, `298370`, `300408`, `290133`, `238085`, `301697`, `298371`, `166142`).
  - **Tier Distribution (Batch 4 Pyramid)**: Freezes candidate volume (7,521) and priority tiers: **P1** (684 — 9.1%), **P2** (1,302 — 17.3%), **P3** (2,415 — 32.1%), **P4** (3,120 — 41.5%).
  - **Consensus Hard Constraint**: Asserts all 597 three-engine consensus works are in P1.
- **Continuous Integration**: `.github/workflows/ci.yml` runs automated test matrix on Python 3.10/3.11/3.12 and verifies Vite frontend production builds on every push/PR.

---

## 🌐 Production Cloud Deployment

FundGuard AI supports zero-cost deployment on Render. See [`DEPLOYMENT_GUIDE.md`](./DEPLOYMENT_GUIDE.md) for full walkthroughs.

### Option A: Free Web Service on Render.com (Recommended)
1. Fork / push this repository to your GitHub account.
2. Go to [render.com](https://render.com/) → **New Web Service** → Select `FundGuard`.
3. Configure:
   - **Build Command**: `cd frontend && npm install && npm run build && cd ../backend && npm install`
   - **Start Command**: `node backend/server.js`
   - **Environment Variables**: `NODE_ENV=production`, `GROQ_API_KEY=gsk_...`
4. Deploy! The backend automatically serves both the API and the React SPA on your custom Render URL.

---

## 📚 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Healthcheck, memory telemetry, and dataset counts |
| `GET` | `/api/overview` | National summary KPIs (297k records, coverage, works) |
| `GET` | `/api/summary` | Risk distributions, detector agreement, and priority queue |
| `GET` | `/api/investigation-queue` | Filterable paginated investigation queue candidates |
| `GET` | `/api/works-explorer` | Complete search and filter across all 104,517 works |
| `GET` | `/api/anomalies/:workId` | Complete forensic dossier for a specific work ID |
| `POST` | `/api/anomalies/:workId/explanation/generate` | Generate on-demand LLM reasoning for any work |
| `GET` | `/api/states-summary` | State-by-state anomaly metrics and risk counts |

---

## ⚖️ Legal Disclaimer

> **Notice**: FundGuard AI is an automated data analytics and forensic screening tool designed to prioritize records for human review. Identifying a work as an "investigation candidate" or "anomaly" does **not** constitute a finding of fraud, corruption, or legal wrongdoing. All findings must be verified against original physical records, sanction orders, and field inspection certificates on the official [MPLADS Portal](https://mplads.gov.in/).

---

## 👥 Contributors & Acknowledgements

- **Repository**: [github.com/komallasahith/FundGuard](https://github.com/komallasahith/FundGuard)
- **Data Source**: Ministry of Statistics and Programme Implementation (MoSPI), Government of India ([mplads.gov.in](https://mplads.gov.in/))
- **Built with**: React, Vite, Node.js, Express, D3.js, Leaflet, Lucide Icons, and Groq Cloud.
