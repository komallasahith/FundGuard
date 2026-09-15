# FundGuard AI — Complete Production Deployment Guide

This guide covers how to deploy the entire FundGuard AI platform (Frontend, Backend, LLM Reasoning API, Multi-Detector Engine, and Official MPLADS Data) to the cloud with **zero cost** or minimal infrastructure.

---

## 🏗️ Architecture Overview

FundGuard AI is structured as a full-stack financial intelligence platform:
1. **Frontend**: Vite + React SPA with 60FPS Geo-Spatial Survey India Map, 6 Analytics Charts, State Deep-Dive Explorer, and Anomaly Dossier Drawer.
2. **Backend**: Node.js + Express REST API running on port `5000` (or dynamic cloud `$PORT`), indexing **297,398** raw MPLADS records and **104,517** canonical works.
3. **AI Reasoning Engine**:
   - **Groq Cloud API** (`llama-3.3-70b-versatile` / `openai/gpt-oss-120b`) for lightning-fast, zero-cost LLM completions.
   - **Persistent Caching Layer** (`india_llm_explanations_cache.json`) to store generated explanations without repeated API hits.
   - **Synthetic Forensic Rule Engine Fallback** guaranteeing 100% uptime and forensic reports even if the API key is unavailable or rate-limited.
4. **Data Verification**: Integrated links and direct verification badges pointing to the official Government of India portal: [mplads.gov.in](https://mplads.gov.in/).

---

## 🚀 Option 1: Free Full-Stack Deployment on Render / Railway (Recommended)

You can deploy the entire app (Frontend + Backend) as a **single unified web service** for free:

### Step 1: Push Project to GitHub
```bash
git add .
git commit -m "FundGuard AI complete production release"
git push origin main
```

### Step 2: Deploy on Render.com
1. Go to [render.com](https://render.com/) and create a free account.
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository `FundGuard`.
4. Configure the settings:
   - **Environment**: `Node`
   - **Build Command**:
     ```bash
     cd frontend && npm install && npm run build && cd ../backend && npm install
     ```
   - **Start Command**:
     ```bash
     node backend/server.js
     ```
5. In **Environment Variables**, add:
   - `NODE_ENV` = `production`
   - `GROQ_API_KEY` = `gsk_your_groq_api_key_here`
6. Click **Deploy Web Service**.
7. Render will build the frontend, package the static assets into `frontend/dist`, and launch the Express backend which automatically serves both the API and the React SPA on your custom Render URL (e.g. `https://fundguard-ai.onrender.com`).

---

## ⚡ Option 2: Split Deployment (Vercel Frontend + Render Backend)

If you prefer deploying the Frontend on Vercel/Netlify for global edge CDN caching:

### Step 1: Deploy Backend on Render
- Build command: `cd backend && npm install`
- Start command: `node backend/server.js`
- Set `GROQ_API_KEY` in environment variables.
- Copy your deployed backend URL: `https://your-backend.onrender.com`.

### Step 2: Deploy Frontend on Vercel
1. Go to [vercel.com](https://vercel.com/) and import your repo.
2. Set Root Directory to `frontend`.
3. Add Environment Variable:
   - `VITE_API_URL` = `https://your-backend.onrender.com/api`
4. Click **Deploy**.

---

## 🐳 Option 3: Docker / Self-Hosted VPS (DigitalOcean, AWS EC2, GCP)

Deploy using Docker on any Linux/Windows cloud server in 1 step:

```bash
# 1. Clone repository
git clone https://github.com/your-username/FundGuard.git
cd FundGuard

# 2. Add your Groq API key to .env
echo "GROQ_API_KEY=gsk_your_key" > .env

# 3. Build and launch container
docker compose up -d --build
```
Your full application will be live at `http://YOUR_SERVER_IP:5000`.

---

## 🔑 How to Obtain a Free Groq LLM API Key (No Credit Card Required)

1. Go to [Groq Console](https://console.groq.com/).
2. Sign in with your Google / GitHub account.
3. Navigate to **API Keys** → **Create API Key**.
4. Copy the key (starts with `gsk_...`).
5. Paste it into your `.env` file or cloud dashboard:
   ```env
   GROQ_API_KEY=gsk_your_key_here
   ```
*Note: Groq provides free access with generous rate limits. Because FundGuard AI caches all explanations in memory and on disk, you will never exceed rate limits or need paid credits.*

---

## 📋 Pre-Deployment Verification Checklist

- [x] **Frontend Bundle Optimized**: Vector map simplified from 20MB down to 1.3MB (60 FPS rendering).
- [x] **All 4 Detector Scores Populated**: `Hybrid Risk Score`, `Rule Score`, `Statistical Score`, `ML Score` verified without blanks.
- [x] **State Deep-Dive & Constituency Breakdown**: Interactive state selection with parliamentary seat allocations and MP names.
- [x] **Official Portal Links**: Verified links to [https://mplads.gov.in/](https://mplads.gov.in/).
- [x] **Health Endpoint**: `GET /api/health` returns `200 OK` with 104,517 canonical works and 297,398 raw source records.
