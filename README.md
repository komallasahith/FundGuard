# 🛡️ FundGuard AI

### AI-Powered Anomaly Detection for MPLADS Implementation

> **Smart India Hackathon 2026 — Team Being-X**

FundGuard AI is an intelligent financial monitoring platform designed to identify unusual spending patterns, implementation anomalies, and potential inefficiencies in the **Members of Parliament Local Area Development Scheme (MPLADS)**.

Instead of relying on a single fraud-detection technique, FundGuard combines **rule-based analysis, peer-based statistical analysis, machine learning, structured evidence generation, and LLM-powered reasoning** to prioritize works that deserve human investigation.

---

## 🎯 Problem

Large-scale public development programs generate thousands of financial and implementation records.

Traditional monitoring approaches can make it difficult to quickly identify:

- Unusually high project costs
- Spending patterns that differ significantly from comparable works
- Unusual transaction structures
- Multiple vendors or transactions requiring review
- Works with incomplete implementation information
- Combinations of signals that may indicate an anomaly

FundGuard AI addresses this by continuously analyzing available MPLADS work and expenditure data and converting large datasets into a prioritized investigation queue.

---

# 💡 Our Solution

FundGuard AI follows a layered detection architecture:

```text
                 MPLADS DATA
                     │
                     ▼
             Data Collection
                     │
                     ▼
          Validation & Cleaning
                     │
                     ▼
             Work Master Data
                     │
                     ▼
            Feature Engineering
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       Rules     Statistics   ML Model
          │          │          │
          └──────────┼──────────┘
                     ▼
              Hybrid Risk Score
                     │
                     ▼
              Evidence Builder
                     │
                     ▼
             LLM Reasoning Layer
                     │
                     ▼
             Investigation Queue
                     │
                     ▼
             Human Investigator
```
The system does **not** automatically label a work as fraudulent.

Instead, it identifies **risk/anomaly candidates for human investigation**.

---

# 🔍 Detection Architecture

## 1. Rule-Based Detection
Deterministic rules identify known patterns such as:

- Extreme peer-group cost
- High peer-group cost
- Multiple vendors
- Multiple transactions
- Sanctioned works without expenditure records
- Sanctioned works not marked completed
- Recommended works not yet sanctioned
- Financial consistency violations
Rules provide transparent and explainable signals.

---

## 2. Peer-Based Statistical Analysis
Every work is compared with similar works.

Peer groups are constructed hierarchically using:

```
State
   ↓
Work Category
   ↓
Activity
```
Fallback groups are used when sufficiently similar peers are unavailable.

The system uses the **peer-group median sanction amount** as a robust benchmark.

A work's relative cost can then be evaluated against comparable projects.

For example:

```
Work Sanction Amount
        ÷
Peer Group Median
        =
Peer Cost Ratio
```
A very large ratio becomes a strong anomaly signal.

---

## 3. Isolation Forest
FundGuard uses **Isolation Forest**, an unsupervised machine-learning algorithm.

This is useful because reliable labelled fraud datasets are generally unavailable.

The model analyzes combinations of features including:

- Recommended amount
- Sanction amount
- Actual amount
- Actual-to-sanction ratio
- Disbursement-to-sanction ratio
- Peer cost ratio
- Transaction count
- Vendor count
- Maximum transaction amount
- Minimum transaction amount
- Log-transformed financial values
- Data completeness
The model identifies observations that are unusual compared with the overall dataset.

Isolation Forest is used as an additional signal rather than as a standalone fraud classifier.

---

# 🧠 Hybrid Risk Engine
The three detection systems are combined into a single risk score.

```
Rule Score          35%
Statistical Score   35%
ML Score            30%
                     │
                     ▼
             Hybrid Risk Score
```
The system also calculates **detector agreement**.

### Detector Agreement

```
3/3 detectors
     ↓
STRONG

2/3 detectors
     ↓
MODERATE

1 detector
     ↓
SINGLE DETECTOR
```
This allows investigators to distinguish between:

- isolated anomalies
- statistically unusual works
- anomalies supported by multiple independent detectors

---

# 📊 Current Dataset
The current Telangana dataset contains:

MetricValueRaw records collected13,887Unique analytical works5,279Engineered features per work98Rule anomaly candidates102Statistical anomaly candidates99Isolation Forest candidates103Strong detector agreement62High-risk works6Medium-risk works110Low-risk works5,163The analytical dataset is consolidated using:

```
WORK_RECOMMENDATION_DTL_ID
```
as the canonical work-level key.

---

# 🧾 Evidence Builder
A major component of FundGuard AI is the **Evidence Builder**.

The detection models generate scores, but scores alone are not enough for an investigator.

The Evidence Builder converts analytical signals into structured evidence.

For each work it organizes:

### Identity

- MP
- Constituency
- Work category
- Activity
- Work ID

### Risk

- Hybrid risk score
- Risk level
- Detector agreement
- Investigation priority

### Financial Evidence

- Recommended amount
- Sanction amount
- Actual amount
- Disbursed amount
- Peer cost ratio

### Transaction Evidence

- Transaction count
- Vendor count
- Maximum transaction amount

### Timeline Evidence

- Recommendation date
- Sanction date
- Completion date
- Implementation durations where available
This creates a controlled bridge between analytics and AI reasoning.

---

# 🤖 AI Investigation Reasoning
FundGuard uses an LLM reasoning layer to explain detected anomalies.

The LLM does not receive the entire raw dataset.

Instead:

```
Detection Results
       ↓
Structured Evidence
       ↓
LLM
       ↓
Investigation Explanation
```
The AI explanation can provide:

- Why the work was flagged
- Key evidence
- Recommended investigation checks
- Risk assessment
- Data limitations
Example investigation checks may include:

- Compare sanction with actual expenditure
- Validate the peer benchmark
- Review vendor selection and contract records
- Obtain completion documentation
- Verify implementation timelines
- Cross-check underlying financial records
The AI explanation is designed to assist investigators rather than replace them.

---

# 🖥️ Dashboard
FundGuard AI provides an investigator-focused command center.

The dashboard provides:

### Command Center

- Total works analyzed
- Risk distribution
- Detector agreement
- Average hybrid risk score
- AI explanation availability

### Investigation Queue
Investigators can:

- Search by work ID
- Search by MP
- Filter by risk level
- Filter by MP
- Filter by work category
- Review prioritized works

### Investigation Drawer
Selecting a work provides:

- Work identity
- Risk score
- Detector scores
- Financial evidence
- Transaction profile
- Implementation timeline
- Structured evidence
- AI investigation reasoning
- Investigation guidance

---

# 🏗️ Technology Stack

## Frontend

- React
- Vite
- Tailwind CSS / CSS
- Recharts
- Lucide React

## Backend

- Node.js
- Express.js
- REST APIs

## Data & Analytics

- Python
- Pandas
- NumPy
- Scikit-learn
- Statistical analysis

## Machine Learning

- Isolation Forest
- Robust scaling
- Median imputation

## AI

- Groq API
- OpenAI-compatible Chat Completions API
- `openai/gpt-oss-120b`

## Data Storage

- PostgreSQL / Supabase architecture
- CSV / JSON analytical outputs

---

# 📁 Project Structure

```
FundGuard/
│
├── backend/
│   ├── server.js
│   ├── package.json
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── scripts/
│   ├── collect_all.py
│   ├── validate_new_data.py
│   ├── build_work_master.py
│   ├── build_expenditure_dataset.py
│   ├── build_features.py
│   ├── validate_features.py
│   ├── detect_rules.py
│   ├── detect_statistical.py
│   ├── detect_isolation_forest.py
│   ├── build_hybrid_risk.py
│   ├── build_evidence.py
│   └── explain_with_llm.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── outputs/
│
├── models/
│   ├── isolation_forest.pkl
│   ├── isolation_forest_imputer.pkl
│   └── isolation_forest_scaler.pkl
│
├── .env.example
├── .gitignore
└── README.md
```

---

# 🔄 Data Pipeline

```
Official MPLADS API
        │
        ▼
Python Data Collector
        │
        ▼
Validation & Deduplication
        │
        ▼
Work Master
        │
        ▼
Expenditure Dataset
        │
        ▼
Feature Engineering
        │
        ▼
┌───────┼────────┐
│       │        │
Rules  Stats    ML
│       │        │
└───────┼────────┘
        ▼
Hybrid Risk Engine
        │
        ▼
Evidence Builder
        │
        ▼
LLM Explanation
        │
        ▼
JSON / CSV Outputs
        │
        ▼
Node.js API
        │
        ▼
React Dashboard
        │
        ▼
Human Investigator
```

---

# 🚀 Running the Project

## 1. Clone the repository

```
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd FundGuard
```

---

## 2. Python Environment
Create the virtual environment:

```
python -m venv .venv
```
Activate it on Windows:

```
.venv\Scripts\Activate.ps1
```
Install required Python dependencies according to the project environment.

---

# 🔐 Environment Variables
Create:

```
.env
```
Do NOT commit this file.

Example:

```
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```
A safe template is provided in:

```
.env.example
```

---

# 🖥️ Start Backend

```
cd backend
npm install
npm start
```
Backend:

```
http://localhost:5000
```
Health check:

```
GET /api/health
```

---

# 🌐 Start Frontend
Open another terminal:

```
cd frontend
npm install
npm run dev
```
Vite will provide the local frontend URL.

The frontend communicates with:

```
http://localhost:5000/api
```

---

# 🔌 Backend API
The current backend provides:

```
GET  /api/health

GET  /api/dashboard/summary

GET  /api/filters

GET  /api/anomalies

GET  /api/anomalies/:workId

GET  /api/anomalies/:workId/explanation

POST /api/reload
```

---

# 🧪 Example Investigation
A high-priority candidate can contain signals such as:

```
Sanction Amount
₹10,000,000

Peer Median
~₹250,000

Peer Cost Ratio
40×

Rule Signal
Detected

Statistical Signal
Detected

Isolation Forest
Detected

Detector Agreement
3/3 — STRONG

Hybrid Risk
52.75 — HIGH
```
The system then converts these signals into structured evidence and generates an investigation-oriented explanation.

---

# ⚠️ Important Interpretation
FundGuard AI is an **anomaly and risk identification system**.

A high-risk work does **not** mean fraud has occurred.

The system is designed to:

```
Detect
  ↓
Prioritize
  ↓
Explain
  ↓
Investigate
```
Final decisions remain with authorized human investigators.

---

# 🌱 Future Scope
Potential future improvements include:

- Expansion from Telangana to nationwide MPLADS data
- Automated periodic data refresh
- More sophisticated peer-group modelling
- Temporal anomaly detection
- Vendor-level network analysis
- Cross-project relationship analysis
- Geographic anomaly visualization
- Advanced expenditure pattern detection
- Investigator feedback loops
- Model monitoring and drift detection
- Role-based access control
- Audit trails
- PostgreSQL-backed production deployment
- Automated investigation workflows

---

# 🏆 Smart India Hackathon 2026
**Problem Statement:** SIH26102

**Ministry:** Ministry of Statistics and Programme Implementation (MoSPI)

**Theme:** AI-powered detection of anomalies, fraud and inefficiencies in MPLADS implementation

**Team:** Being-X

**Project:** FundGuard AI

---

# 👥 Team

### Being-X
Built for **Smart India Hackathon 2026**.

---

# ⚖️ Disclaimer
FundGuard AI identifies anomaly and risk candidates for investigation.

It does **not** establish fraud, corruption, misconduct, or wrongdoing.

All flagged works require appropriate human verification and investigation using authoritative records.

---

## ⭐ FundGuard AI

### From public-fund data to explainable investigation intelligence.

```
DATA → DETECTION → RISK → EVIDENCE → AI REASONING → INVESTIGATION
```
