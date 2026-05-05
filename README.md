# 🪐 Iron Star Ledger

> **Personal finance analyzer — interstellar 3D edition.**
> Powered by Plex Automation.

A photoreal **starship-cockpit dashboard** for your money. Upload Excel / OFX / QFX statements,
fly into the cockpit, and chart your financial galaxy in a 360° sci-fi HUD.

---

## ✨ What's inside

- 🚀 **3D cockpit** — Next.js + React Three Fiber + postprocessing (bloom, chromatic, vignette)
- 🪐 Procedural planets, layered starfields, comets with motion trails, atmospheric scattering
- 🎬 Cinematic **fly-into-cockpit** sequence after first analysis
- 🖱️ **360° look-around** in the cockpit (mouse parallax)
- 📊 **HUD-style 2D dashboards** overlaid on the 3D scene (Recharts)
  - Cashflow trend · Running balance · Spend donut · Top categories · Top expenses
- 🏥 **Financial Health Score (0–100)** with 4-component reasoning
- 🤖 **AI Coach** — Ollama-powered narrative briefing (with rule-based fallback)
- 🔁 **Subscription detector** — cadence + keyword fallback
- 💡 Insights engine: anomaly detection, category dominance, day-of-week patterns
- 📥 Multi-file upload: `.csv`, `.xlsx`, `.xls`, `.ofx`, `.qbo`, `.qfx`

---

## 🏗️ Architecture

Two services, deployed independently to Railway:

```
.
├── api/          ← FastAPI · Python 3.12  (parsers + analytics + AI coach)
│   ├── app/
│   │   ├── main.py       (REST endpoints)
│   │   ├── parsers.py    (CSV / Excel / OFX / QFX)
│   │   ├── analytics.py  (categorize · subs · health · insights)
│   │   └── coach.py      (Ollama narrative + fallback)
│   ├── requirements.txt
│   ├── Procfile · runtime.txt · railway.json
│
├── web/          ← Next.js 14 · React 18 · R3F · Tailwind  (3D cockpit UI)
│   ├── app/      (page.tsx · layout.tsx · globals.css)
│   ├── components/
│   │   ├── Scene.tsx          (R3F scene · planets · cockpit · camera rig)
│   │   ├── Dashboard.tsx      (tabbed HUD panel)
│   │   ├── HealthGauge.tsx    (animated SVG gauge)
│   │   ├── MetricStrip.tsx    (6 KPI tiles)
│   │   ├── Charts.tsx         (Recharts visualizations)
│   │   ├── CoachPanel.tsx     (AI coach markdown render)
│   │   └── …
│   ├── lib/      (api · store · types · format)
│   ├── package.json · railway.json · Procfile
│
└── app.py        ← Original Streamlit app (kept as fallback)
```

---

## 🧪 Local Development

### 1. API — FastAPI on http://localhost:8000

```bash
cd api
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Quick smoke test: `curl http://localhost:8000/api/demo | head -c 300`

### 2. Web — Next.js on http://localhost:3000

```bash
cd web
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

Open http://localhost:3000 → click **Launch Demo** → cinematic fly-into-cockpit.

---

## ☁️ Deploy to Railway

This monorepo deploys as **two services** in the same Railway project.

### Service A — API

1. Railway → **New Service → Deploy from GitHub** → pick `ThaGuff/ClearLedgerAI`
2. Settings → **Root Directory** = `api`
3. Variables:
   - `ALLOWED_ORIGINS` = `https://<your-web-domain>.up.railway.app,*`
   - `OLLAMA_URL` (optional — defaults to localhost so falls back to rule-based memo if unset)
4. **Generate Domain** → e.g. `iron-star-api.up.railway.app`

### Service B — Web

1. Railway → **New Service → Deploy from GitHub** → same repo
2. Settings → **Root Directory** = `web`
3. Variables:
   - `NEXT_PUBLIC_API_URL` = `https://iron-star-api.up.railway.app`
4. **Generate Domain** → public URL of the cockpit UI

`railway.json` and `Procfile` files are committed for both services — Nixpacks auto-detects.

### Existing project

Project ID: `8873e3f9-c09f-4add-97dd-b0a3cf3f2715`

```bash
railway login
railway link   # select the project above
# inside api/ or web/:
railway up
railway domain
```

---

## 🤖 AI Coach (optional)

The `/api/coach` endpoint will call a local or remote **Ollama** server if configured:

```bash
OLLAMA_URL=http://localhost:11434 OLLAMA_MODEL=llama3:latest \
  uvicorn app.main:app --host 0.0.0.0 --port 8000
```

If Ollama is unreachable, the coach returns a structured rule-based memo automatically.

---

## 💳 SaaS Hooks

- **Stripe** checkout slot — drop your URL into the upgrade button
- **GoHighLevel** webhook placeholder — POST score + metrics after each analysis

---

## 🛟 Fallback: Streamlit version

The original single-file Streamlit dashboard is preserved at `app.py`:

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 📝 License

© 2026 Plex Automation. All rights reserved.
