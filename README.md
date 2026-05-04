# 💰 ClearLedger AI

**Personal finance analyzer — built for the $9/mo SaaS launch.**
Powered by Plex Automation.

Upload Excel, OFX, or QFX statements → get instant insights, a 0–100 financial health score, and tiered AI advice.

---

## ✨ Features

- 📥 Multi-file upload: `.xlsx`, `.xls`, **`.csv`**, `.ofx`, `.qbo`, `.qfx`
- 🔍 Auto-detects Date / Amount / Payee (and Debit/Credit) columns
- 🏷️ **Auto-categorization** of transactions (16 categories)
- 🔁 **Subscription / recurring detector** + cancellation simulator
- 📊 **Interactive Plotly dashboards** — drill from category → merchant → transaction
- 📈 Monthly income/expense/net trend bars + line
- 🥧 Spending pie · 🔝 top merchants · 🌳 treemap drill-down
- 📅 Day-of-week × week spending heatmap
- 🏥 Financial Health Score with **deep per-component reasoning**
- 💡 Insights engine: anomalies, category dominance, day-of-week patterns
- 🤖 **AI Coach** powered by Claude (set `ANTHROPIC_API_KEY`) with rule-based fallback
- 🔎 Filters: date range · source · category · payee search
- ⬇️ Filtered CSV export
- 🌙 Plex Automation dark theme
- 🔌 Stripe + GoHighLevel webhook hooks ready

---

## 🚀 Local Development

```bash
git clone https://github.com/ThaGuff/ClearLedgerAI.git
cd ClearLedgerAI
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501

---

## ☁️ Deploy to Railway (1-click)

### Option A — CLI (already configured here)

```bash
railway login
railway link    # select project: 8873e3f9-c09f-4add-97dd-b0a3cf3f2715
railway up
railway domain  # generate public URL
```

### Option B — GitHub auto-deploy

1. Push this repo to GitHub.
2. In Railway → **New Service → Deploy from GitHub** → pick `ThaGuff/ClearLedgerAI`.
3. Railway detects `requirements.txt` + `Procfile` automatically.
4. Add env vars in Railway → **Variables**:
   - `GHL_WEBHOOK_URL` (optional)
   - `STRIPE_SECRET_KEY` (optional)
5. Click **Generate Domain**.

Railway sets `$PORT` automatically; the `Procfile` binds Streamlit to it.

---

## 💳 SaaS Hooks (placeholders)

- **Stripe:** "Upgrade to Pro" button in sidebar — wire it to a Stripe Checkout URL.
- **GoHighLevel:** set `GHL_WEBHOOK_URL` to POST `{score, income, expenses, net}` after each analysis.

---

## 📁 Project Structure

```
.
├── app.py              # Streamlit app (parsers + analytics + UI)
├── requirements.txt    # Pinned deps
├── Procfile            # Railway/Heroku entrypoint
├── runtime.txt         # Python 3.12
├── .env.example        # Optional env vars
├── .gitignore
├── samples/
│   ├── sample_transactions.xlsx
│   └── sample_statement.ofx
└── README.md
```

---

## 🧪 Sample Data

Drop the files in `samples/` into the uploader to test instantly, or toggle **"Use demo data"** in the sidebar.

---

## 📝 License

© 2026 Plex Automation. All rights reserved.
