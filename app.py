"""
ClearLedger AI - AI-Powered Personal Finance Analyzer
Powered by Plex Automation
"""

from __future__ import annotations

import io
import os
import re
import zipfile
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# Page config & theme
# ============================================================
st.set_page_config(
    page_title="ClearLedger AI · Smart Money Coach",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

PLEX_DARK = "#0f0f23"
PLEX_PANEL = "#15153a"
PLEX_ACCENT = "#7c3aed"
PLEX_GREEN = "#10b981"
PLEX_RED = "#ef4444"
PLEX_AMBER = "#f59e0b"
PLEX_TEXT = "#ffffff"
PLEX_SUB = "#a78bfa"

PLOTLY_TEMPLATE = "plotly_dark"

st.markdown(
    f"""
    <style>
        .stApp {{ background-color: {PLEX_DARK}; color: {PLEX_TEXT}; }}
        section[data-testid="stSidebar"] {{ background-color: #0c0c1f; }}
        h1, h2, h3, h4, h5, h6, p, label, span, div {{ color: {PLEX_TEXT}; }}
        [data-testid="stMetricValue"] {{ color: {PLEX_TEXT} !important; font-weight:700; }}
        [data-testid="stMetricLabel"] {{ color: {PLEX_SUB} !important; font-weight:600; }}
        [data-testid="stMetricDelta"] svg {{ display:none; }}
        .stTabs [data-baseweb="tab-list"] {{ gap:6px; }}
        .stTabs [data-baseweb="tab"] {{
            background:{PLEX_PANEL}; border-radius:10px 10px 0 0; padding:10px 18px;
            color:{PLEX_SUB}; font-weight:600;
        }}
        .stTabs [aria-selected="true"] {{ background:{PLEX_ACCENT}; color:white; }}
        .footer {{
            text-align:center; padding:1.5rem 0 .5rem 0;
            color:#9ca3af !important; font-size:.85rem;
        }}
        .badge {{
            display:inline-block; padding:.25rem .75rem; border-radius:999px;
            background:{PLEX_ACCENT}; color:white !important;
            font-weight:600; font-size:.8rem;
        }}
        .insight-card {{
            background: linear-gradient(135deg, rgba(124,58,237,.18), rgba(124,58,237,.05));
            border:1px solid rgba(124,58,237,.4);
            border-radius:14px; padding:1rem 1.25rem; margin-bottom:.75rem;
        }}
        .insight-card.warn {{
            background: linear-gradient(135deg, rgba(239,68,68,.18), rgba(239,68,68,.05));
            border:1px solid rgba(239,68,68,.4);
        }}
        .insight-card.good {{
            background: linear-gradient(135deg, rgba(16,185,129,.18), rgba(16,185,129,.05));
            border:1px solid rgba(16,185,129,.4);
        }}
        .insight-card.info {{
            background: linear-gradient(135deg, rgba(245,158,11,.18), rgba(245,158,11,.05));
            border:1px solid rgba(245,158,11,.4);
        }}
        .stDownloadButton button, .stButton button {{
            background:{PLEX_ACCENT}; color:white; border:0; font-weight:600;
            border-radius:10px;
        }}
        .stDownloadButton button:hover, .stButton button:hover {{
            background:#9333ea; color:white;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Parsers — Excel, CSV, OFX, QFX/QBO
# ============================================================
DATE_HINTS = ["date", "posted", "transaction date", "trans date", "post date", "posting date"]
AMOUNT_HINTS = ["amount", "amt", "value", "total"]
DEBIT_HINTS = ["debit", "withdrawal", "withdrawals"]
CREDIT_HINTS = ["credit", "deposit", "deposits"]
PAYEE_HINTS = ["payee", "description", "memo", "merchant", "name", "details", "transaction"]


def _detect_col(cols: list[str], hints: list[str]) -> Optional[str]:
    lowered = {c.lower().strip(): c for c in cols}
    for hint in hints:
        for low, orig in lowered.items():
            if hint == low:
                return orig
    for hint in hints:
        for low, orig in lowered.items():
            if hint in low:
                return orig
    return None


def _frame_from_tabular(raw: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Convert any tabular DataFrame (Excel/CSV) to standardized schema."""
    cols = list(raw.columns.astype(str))
    date_c = _detect_col(cols, DATE_HINTS)
    amt_c = _detect_col(cols, AMOUNT_HINTS)
    debit_c = _detect_col(cols, DEBIT_HINTS)
    credit_c = _detect_col(cols, CREDIT_HINTS)
    payee_c = _detect_col(cols, PAYEE_HINTS)

    if not date_c:
        raise ValueError(f"Could not detect Date column in {source_name}. Found: {cols}")

    if amt_c:
        amount = pd.to_numeric(raw[amt_c], errors="coerce")
    elif debit_c or credit_c:
        deb = pd.to_numeric(raw[debit_c], errors="coerce").fillna(0) if debit_c else 0
        cre = pd.to_numeric(raw[credit_c], errors="coerce").fillna(0) if credit_c else 0
        amount = cre - deb
    else:
        raise ValueError(f"Could not detect Amount column in {source_name}. Found: {cols}")

    df = pd.DataFrame(
        {
            "date": pd.to_datetime(raw[date_c], errors="coerce"),
            "amount": amount,
            "payee": raw[payee_c].astype(str).str.strip() if payee_c else "Unknown",
            "source": source_name,
        }
    )
    return df.dropna(subset=["date", "amount"]).reset_index(drop=True)


def parse_excel(file) -> pd.DataFrame:
    raw = pd.read_excel(file, engine="openpyxl" if file.name.endswith("xlsx") else None)
    return _frame_from_tabular(raw, file.name)


def parse_csv(file) -> pd.DataFrame:
    file.seek(0)
    # try multiple encodings/delimiters
    raw_bytes = file.read()
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = raw_bytes.decode(enc)
            for sep in (",", ";", "\t", "|"):
                try:
                    df = pd.read_csv(io.StringIO(text), sep=sep, engine="python")
                    if df.shape[1] >= 2:
                        return _frame_from_tabular(df, file.name)
                except Exception:
                    continue
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not parse CSV: {file.name}")


def _parse_ofx_text(text: str, source_name: str) -> pd.DataFrame:
    """Parse OFX/QFX/QBO content via ofxparse (with regex fallback)."""
    try:
        from ofxparse import OfxParser

        ofx = OfxParser.parse(io.BytesIO(text.encode("utf-8")))
        rows = []
        for account in ofx.accounts:
            for t in account.statement.transactions:
                rows.append(
                    {
                        "date": pd.to_datetime(t.date),
                        "amount": float(t.amount),
                        "payee": (t.payee or t.memo or "Unknown").strip(),
                        "source": source_name,
                    }
                )
        if rows:
            return pd.DataFrame(rows)
    except Exception:
        pass

    # Regex fallback for malformed SGML
    rows: list[dict] = []
    pattern = re.compile(r"<STMTTRN>(.*?)</STMTTRN>", re.DOTALL | re.IGNORECASE)
    for block in pattern.findall(text):

        def grab(tag: str) -> str:
            m = re.search(rf"<{tag}>([^<\r\n]+)", block, re.IGNORECASE)
            return m.group(1).strip() if m else ""

        date_raw, amount_raw = grab("DTPOSTED"), grab("TRNAMT")
        payee = grab("NAME") or grab("MEMO") or "Unknown"
        if not date_raw or not amount_raw:
            continue
        try:
            dt = pd.to_datetime(date_raw[:8], format="%Y%m%d", errors="coerce")
            amt = float(amount_raw)
        except Exception:
            continue
        rows.append({"date": dt, "amount": amt, "payee": payee, "source": source_name})
    if not rows:
        raise ValueError(f"No transactions parsed from {source_name}")
    return pd.DataFrame(rows).dropna(subset=["date"])


def parse_ofx(file) -> pd.DataFrame:
    file.seek(0)
    raw = file.read()
    text = raw.decode("utf-8", "ignore") if isinstance(raw, bytes) else raw
    return _parse_ofx_text(text, file.name)


def parse_qfx(file) -> pd.DataFrame:
    file.seek(0)
    raw = file.read()
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                if name.lower().endswith((".qfx", ".qbo", ".ofx", ".xml")):
                    with z.open(name) as f:
                        return _parse_ofx_text(
                            f.read().decode("utf-8", "ignore"), file.name
                        )
        raise ValueError(f"No QFX/OFX file inside zip {file.name}")
    return _parse_ofx_text(raw.decode("utf-8", "ignore"), file.name)


def parse_any(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith((".xlsx", ".xls")):
        return parse_excel(file)
    if name.endswith(".csv"):
        return parse_csv(file)
    if name.endswith(".ofx"):
        return parse_ofx(file)
    if name.endswith((".qbo", ".qfx")):
        return parse_qfx(file)
    raise ValueError(f"Unsupported file type: {file.name}")


# ============================================================
# Categorization
# ============================================================
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Income", ["salary", "payroll", "deposit", "direct dep", "paycheck", "venmo cashout",
                "stripe", "interest", "dividend", "refund"]),
    ("Housing", ["rent", "mortgage", "hoa", "property tax", "landlord"]),
    ("Utilities", ["electric", "gas company", "pg&e", "water", "sewer", "internet",
                   "comcast", "xfinity", "at&t", "verizon", "t-mobile", "spectrum",
                   "cellular"]),
    ("Groceries", ["whole foods", "trader joe", "safeway", "kroger", "costco", "wegmans",
                   "publix", "aldi", "sprouts", "albertsons", "grocery", "supermarket",
                   "walmart", "target"]),
    ("Dining", ["starbucks", "mcdonald", "chipotle", "doordash", "uber eats", "grubhub",
                "restaurant", "cafe", "coffee", "pizza", "sushi", "kitchen", "diner",
                "panera", "chick-fil-a", "subway"]),
    ("Transport", ["uber", "lyft", "shell", "chevron", "exxon", "bp gas", "gas station",
                   "parking", "transit", "metro", "amtrak", "airline", "delta", "united",
                   "southwest", "american air"]),
    ("Subscriptions", ["netflix", "spotify", "hulu", "disney", "hbo", "max ", "youtube",
                       "apple.com/bill", "icloud", "adobe", "github", "openai", "claude",
                       "anthropic", "chatgpt", "notion", "dropbox", "patreon"]),
    ("Shopping", ["amazon", "ebay", "etsy", "best buy", "apple store", "nike", "nordstrom",
                  "macy", "ikea", "home depot", "lowe", "wayfair"]),
    ("Health", ["pharmacy", "cvs", "walgreens", "doctor", "clinic", "hospital", "dental",
                "vision", "medical", "blue cross", "aetna", "kaiser"]),
    ("Fitness", ["gym", "peloton", "equinox", "planet fitness", "yoga", "crossfit"]),
    ("Entertainment", ["movie", "amc", "regal", "theater", "concert", "ticketmaster",
                       "stubhub", "steam", "playstation", "xbox", "nintendo"]),
    ("Personal Care", ["salon", "barber", "spa", "nails", "sephora", "ulta"]),
    ("Insurance", ["geico", "progressive", "state farm", "allstate", "insurance"]),
    ("Education", ["tuition", "udemy", "coursera", "school", "university", "college"]),
    ("Travel", ["hotel", "airbnb", "marriott", "hilton", "expedia", "booking"]),
    ("Fees & Interest", ["fee", "interest charge", "overdraft", "atm", "service charge"]),
    ("Transfers", ["transfer", "zelle", "venmo", "cash app", "paypal"]),
]


def categorize(payee: str, amount: float) -> str:
    p = (payee or "").lower()
    if amount > 0:
        # positive amounts are typically income unless they're a refund/transfer
        for cat, kw in CATEGORY_RULES:
            if cat == "Income" and any(k in p for k in kw):
                return "Income"
        if any(k in p for k in ["transfer", "zelle", "venmo", "cash app", "paypal"]):
            return "Transfers"
        return "Income"
    for cat, kw in CATEGORY_RULES:
        if cat == "Income":
            continue
        if any(k in p for k in kw):
            return cat
    return "Other"


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["category"] = [categorize(p, a) for p, a in zip(df["payee"], df["amount"])]
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["weekday"] = df["date"].dt.day_name()
    df["abs_amount"] = df["amount"].abs()
    df["type"] = np.where(df["amount"] > 0, "Income", "Expense")
    return df


# ============================================================
# Subscription / recurring detector
# ============================================================
def detect_subscriptions(df: pd.DataFrame) -> pd.DataFrame:
    """Detect recurring charges by payee with stable monthly cadence."""
    exp = df[df["amount"] < 0].copy()
    if exp.empty:
        return pd.DataFrame()
    exp["payee_norm"] = exp["payee"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True).str.strip()
    out = []
    for payee, g in exp.groupby("payee_norm"):
        if len(g) < 2:
            continue
        g = g.sort_values("date")
        deltas = g["date"].diff().dt.days.dropna()
        if deltas.empty:
            continue
        median_gap = deltas.median()
        # accept ~7d (weekly), ~14d (biweekly), ~30d (monthly), ~90d (quarterly)
        if not (5 <= median_gap <= 35 or 85 <= median_gap <= 95):
            continue
        amts = g["amount"].abs()
        if amts.std() / (amts.mean() + 1e-9) > 0.25:  # too variable -> not subscription
            continue
        cadence = (
            "Weekly" if median_gap < 10
            else "Bi-Weekly" if median_gap < 20
            else "Monthly" if median_gap < 40
            else "Quarterly"
        )
        out.append(
            {
                "Merchant": g["payee"].iloc[-1],
                "Cadence": cadence,
                "Avg Charge": amts.mean(),
                "Last Charged": g["date"].max(),
                "Charges": len(g),
                "Annual Cost": amts.mean() * (52 if cadence == "Weekly"
                                              else 26 if cadence == "Bi-Weekly"
                                              else 12 if cadence == "Monthly"
                                              else 4),
            }
        )
    return (
        pd.DataFrame(out).sort_values("Annual Cost", ascending=False).reset_index(drop=True)
        if out else pd.DataFrame()
    )


# ============================================================
# Health Score (with detailed reasoning)
# ============================================================
def compute_health(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"score": 0, "components": {}, "metrics": {}, "reasoning": []}

    income = df.loc[df["amount"] > 0, "amount"].sum()
    expenses = -df.loc[df["amount"] < 0, "amount"].sum()
    net = income - expenses
    monthly = df.set_index("date").resample("ME")["amount"].sum()
    months = max(1, len(monthly))
    monthly_expense = expenses / months if months else expenses

    # 1) Expense Ratio (40%)
    ratio = expenses / income if income > 0 else 1.0
    if ratio <= 0.5:
        e_score = 1.0
    elif ratio >= 1.0:
        e_score = 0.0
    else:
        e_score = 1.0 - (ratio - 0.5) / 0.5

    # 2) Savings Rate (30%)
    savings_rate = (net / income) if income > 0 else 0.0
    s_score = 1.0 if savings_rate >= 0.15 else max(0.0, savings_rate / 0.15)

    # 3) Cashflow Stability (20%)
    if len(monthly) >= 2 and monthly.abs().mean() > 0:
        cv = monthly.std() / (monthly.abs().mean() + 1e-9)
        st_score = max(0.0, 1.0 - min(cv, 1.0))
    else:
        st_score = 0.5
        cv = 0.0

    # 4) Runway (10%) — cumulative net / monthly expense
    runway = (net / monthly_expense) if monthly_expense > 0 else 0
    r_score = 1.0 if runway >= 3 else max(0.0, runway / 3)

    score = round((0.40 * e_score + 0.30 * s_score + 0.20 * st_score + 0.10 * r_score) * 100, 1)

    reasoning = [
        {
            "name": "Expense Ratio",
            "weight": 40,
            "score": round(e_score * 100, 1),
            "metric": f"{ratio*100:.1f}%",
            "ideal": "< 50%",
            "explanation": (
                f"You're spending **{ratio*100:.1f}%** of your income. "
                + ("Excellent — well under the 50% ceiling." if ratio < 0.5
                   else "Above the 50% danger line — every dollar of income is being consumed by expenses."
                   if ratio >= 1.0
                   else f"Above the 50% target. Cutting expenses by ~${(expenses-income*0.5):,.0f} would hit the ideal ratio.")
            ),
        },
        {
            "name": "Savings Rate",
            "weight": 30,
            "score": round(s_score * 100, 1),
            "metric": f"{savings_rate*100:.1f}%",
            "ideal": "≥ 15%",
            "explanation": (
                f"Net savings rate is **{savings_rate*100:.1f}%** of income. "
                + ("On track — you're building wealth." if savings_rate >= 0.15
                   else f"Need to free up an extra ${(income*0.15 - net):,.0f} to hit the 15% target.")
            ),
        },
        {
            "name": "Cashflow Stability",
            "weight": 20,
            "score": round(st_score * 100, 1),
            "metric": f"CV {cv:.2f}",
            "ideal": "low variance",
            "explanation": (
                f"Monthly cashflow coefficient of variation is **{cv:.2f}** "
                + ("(very stable)." if cv < 0.3
                   else "(some swings — consider a buffer fund)." if cv < 0.7
                   else "(highly volatile — irregular income or lumpy expenses).")
            ),
        },
        {
            "name": "Runway Months",
            "weight": 10,
            "score": round(r_score * 100, 1),
            "metric": f"{runway:.1f} months",
            "ideal": "≥ 3 months",
            "explanation": (
                f"Net cash buffer covers **{runway:.1f} months** of expenses. "
                + ("Solid cushion." if runway >= 3
                   else "Below the 3-month emergency-fund minimum.")
            ),
        },
    ]

    return {
        "score": score,
        "components": {r["name"]: r["score"] for r in reasoning},
        "metrics": {
            "income": income,
            "expenses": expenses,
            "net": net,
            "monthly_expense": monthly_expense,
            "savings_rate": savings_rate,
            "expense_ratio": ratio,
            "runway_months": runway,
            "monthly_count": months,
        },
        "reasoning": reasoning,
    }


def score_band(score: float) -> tuple[str, str]:
    if score < 40:
        return "🚨 CRITICAL", PLEX_RED
    if score < 70:
        return "⚠️ FAIR", PLEX_AMBER
    return "✅ GOOD", PLEX_GREEN


# ============================================================
# Insights engine
# ============================================================
def build_insights(df: pd.DataFrame, subs: pd.DataFrame, health: dict) -> list[dict]:
    insights: list[dict] = []
    metrics = health["metrics"]

    # Top expense category share
    cats = df[df["amount"] < 0].groupby("category")["amount"].sum().abs().sort_values(ascending=False)
    if not cats.empty and metrics["expenses"] > 0:
        top_cat, top_val = cats.index[0], cats.iloc[0]
        share = top_val / metrics["expenses"] * 100
        if share > 35:
            insights.append({
                "type": "warn",
                "title": f"⚠️ {top_cat} dominates your spending",
                "body": f"**{share:.0f}%** of expenses (${top_val:,.0f}) go to **{top_cat}**. "
                        f"Reducing this category by 15% saves **${top_val*0.15:,.0f}**.",
            })

    # Subscription burden
    if not subs.empty:
        annual = subs["Annual Cost"].sum()
        monthly_sub = annual / 12
        if metrics["expenses"] > 0 and monthly_sub > 0:
            insights.append({
                "type": "info",
                "title": f"🔁 {len(subs)} recurring subscriptions detected",
                "body": f"You're paying **${monthly_sub:,.0f}/mo** (${annual:,.0f}/year) "
                        f"in recurring charges. Top: **{subs.iloc[0]['Merchant']}** "
                        f"(${subs.iloc[0]['Annual Cost']:,.0f}/yr).",
            })

    # Anomalies — unusually large expenses (z-score > 2)
    exp = df[df["amount"] < 0].copy()
    if len(exp) >= 10:
        amts = exp["amount"].abs()
        z = (amts - amts.mean()) / (amts.std() + 1e-9)
        outliers = exp[z > 2.5].sort_values("amount").head(3)
        if not outliers.empty:
            lines = [f"- ${row['amount']:,.2f} · {row['payee']} · {row['date']:%b %d}"
                     for _, row in outliers.iterrows()]
            insights.append({
                "type": "info",
                "title": f"🔍 {len(outliers)} unusually large transactions",
                "body": "These purchases are >2.5σ above your average:\n\n" + "\n".join(lines),
            })

    # Savings rate
    if metrics["income"] > 0:
        sr = metrics["savings_rate"]
        if sr < 0:
            insights.append({
                "type": "warn",
                "title": "🛑 Spending exceeds income",
                "body": f"You spent **${-metrics['net']:,.0f} more** than you earned. "
                        "Trim discretionary categories first (Dining, Subscriptions, Shopping).",
            })
        elif sr >= 0.20:
            insights.append({
                "type": "good",
                "title": f"💪 Strong savings rate ({sr*100:.0f}%)",
                "body": f"Saving **${metrics['net']:,.0f}**. Consider auto-investing into "
                        "a low-cost index fund or maxing tax-advantaged accounts.",
            })

    # Day-of-week pattern
    dow = exp.groupby(exp["date"].dt.day_name())["amount"].sum().abs()
    if not dow.empty:
        worst_day = dow.idxmax()
        if dow[worst_day] > dow.mean() * 1.4:
            insights.append({
                "type": "info",
                "title": f"📅 {worst_day}s are your highest-spend day",
                "body": f"You spend **${dow[worst_day]:,.0f}** on {worst_day}s — "
                        f"{(dow[worst_day]/dow.mean() - 1)*100:.0f}% above your weekly average.",
            })

    # Net positive
    score = health["score"]
    if score >= 70:
        insights.append({
            "type": "good",
            "title": "✅ Financially healthy",
            "body": f"Score **{score}/100**. Focus shifts from defense to offense: "
                    "increase investment contributions and explore tax optimization.",
        })

    return insights


# ============================================================
# AI Coach (Anthropic API w/ rule-based fallback)
# ============================================================
def ai_coach_narrative(df: pd.DataFrame, subs: pd.DataFrame, health: dict) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    metrics = health["metrics"]
    cats = df[df["amount"] < 0].groupby("category")["amount"].sum().abs().sort_values(ascending=False).head(5)
    summary = {
        "score": health["score"],
        "income": round(metrics["income"], 2),
        "expenses": round(metrics["expenses"], 2),
        "net": round(metrics["net"], 2),
        "savings_rate_pct": round(metrics["savings_rate"] * 100, 1),
        "expense_ratio_pct": round(metrics["expense_ratio"] * 100, 1),
        "runway_months": round(metrics["runway_months"], 1),
        "top_categories": {k: round(float(v), 2) for k, v in cats.to_dict().items()},
        "subscription_monthly": round(float(subs["Annual Cost"].sum()) / 12, 2) if not subs.empty else 0,
    }

    if api_key:
        try:
            import anthropic  # type: ignore

            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                max_tokens=900,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "You are a CFP-level personal finance coach. Given the user's "
                            "financial summary JSON, write a punchy, specific, actionable "
                            "coaching memo in markdown (≤350 words). Use bullet sections: "
                            "**Where you stand**, **Top 3 wins this month**, **Risks**, "
                            "**90-day game plan**. Reference specific dollar figures.\n\n"
                            f"Data: {summary}"
                        ),
                    }
                ],
            )
            return msg.content[0].text
        except Exception as e:  # noqa: BLE001
            return _fallback_narrative(summary, error=str(e))

    return _fallback_narrative(summary)


def _fallback_narrative(s: dict, error: Optional[str] = None) -> str:
    band, _ = score_band(s["score"])
    sr = s["savings_rate_pct"]
    er = s["expense_ratio_pct"]
    top = list(s["top_categories"].items())[:3]
    note = f"\n\n_AI fallback (set `ANTHROPIC_API_KEY` env var for live coach{f' — {error}' if error else ''})._"

    lines = [
        f"### {band} · Score {s['score']}/100",
        "",
        "**Where you stand**",
        f"- Income: **${s['income']:,.0f}** · Expenses: **${s['expenses']:,.0f}** · Net: **${s['net']:,.0f}**",
        f"- Savings rate: **{sr:.1f}%** (target ≥15%) · Expense ratio: **{er:.1f}%** (target <50%)",
        f"- Runway: **{s['runway_months']:.1f} months** (target ≥3)",
        f"- Subscriptions: **${s['subscription_monthly']:,.0f}/mo**",
        "",
        "**Top 3 wins this month**",
    ]
    if top:
        for cat, val in top:
            lines.append(
                f"- Trim **{cat}** by 15% → save **${val*0.15:,.0f}/mo** "
                f"(**${val*0.15*12:,.0f}/yr**)"
            )
    if s["subscription_monthly"] > 50:
        lines.append(f"- Audit subscriptions — cancelling 25% saves **${s['subscription_monthly']*0.25*12:,.0f}/yr**")

    lines += ["", "**Risks**"]
    if sr < 10:
        lines.append("- ⚠️ Savings rate is below 10% — vulnerable to any income shock.")
    if s["runway_months"] < 3:
        lines.append("- ⚠️ Emergency fund below 3 months — single expense can destabilize.")
    if er > 90:
        lines.append("- 🚨 You're spending nearly all you earn. Lifestyle creep is the #1 culprit.")
    if not any("⚠️" in line or "🚨" in line for line in lines[-5:]):
        lines.append("- No critical risks — focus on optimization, not defense.")

    lines += [
        "",
        "**90-day game plan**",
        "- **Days 1–14:** List every recurring charge. Cancel anything unused in 30 days.",
        f"- **Days 15–45:** Set up auto-transfer of {max(10, int(sr+5))}% of every paycheck to a HYSA.",
        "- **Days 46–90:** Move savings beyond the emergency fund into a tax-advantaged "
        "investment account (Roth IRA, 401k match, HSA).",
        note,
    ]
    return "\n".join(lines)


# ============================================================
# Demo data
# ============================================================
def load_demo() -> pd.DataFrame:
    rng = pd.date_range(end=datetime.today(), periods=180, freq="D")
    np.random.seed(7)
    rows = []
    payees_disc = [("Whole Foods", "groc"), ("Trader Joe's", "groc"), ("Amazon", "shop"),
                   ("Starbucks", "din"), ("Doordash", "din"), ("Uber", "tx"),
                   ("Shell Gas", "tx"), ("Costco", "groc"), ("Target", "shop"),
                   ("Chipotle", "din"), ("Best Buy", "shop"), ("CVS Pharmacy", "hlth")]
    for d in rng:
        if d.day in (1, 15):
            rows.append({"date": d, "amount": 3400.0, "payee": "Acme Corp Payroll", "source": "demo"})
        if d.day == 3:
            rows.append({"date": d, "amount": -1850.0, "payee": "Property Management Rent", "source": "demo"})
        if d.day == 5:
            rows.append({"date": d, "amount": -89.99, "payee": "AT&T Wireless", "source": "demo"})
            rows.append({"date": d, "amount": -15.49, "payee": "Netflix", "source": "demo"})
            rows.append({"date": d, "amount": -11.99, "payee": "Spotify", "source": "demo"})
        if d.day == 12:
            rows.append({"date": d, "amount": -42.00, "payee": "Planet Fitness Gym", "source": "demo"})
        # discretionary
        for _ in range(np.random.poisson(2)):
            p, _ = payees_disc[np.random.randint(len(payees_disc))]
            amt = -float(np.round(np.random.uniform(8, 140), 2))
            rows.append({"date": d, "amount": amt, "payee": p, "source": "demo"})
    return pd.DataFrame(rows)


# ============================================================
# Sidebar — uploads + filters
# ============================================================
with st.sidebar:
    st.markdown(f"<h2>💰 ClearLedger AI</h2><span class='badge'>SMART MONEY COACH</span>",
                unsafe_allow_html=True)
    st.divider()
    st.markdown("### 📥 Upload Statements")
    uploaded = st.file_uploader(
        "Excel · CSV · OFX · QFX",
        type=["xlsx", "xls", "csv", "ofx", "qbo", "qfx"],
        accept_multiple_files=True,
    )
    use_demo = st.toggle("🧪 Use demo data", value=not uploaded)
    st.divider()
    st.caption("🔒 Files processed in-memory — never stored.")
    st.caption("💳 **Pro · $9/mo** — AI coach, alerts, exports")
    st.markdown(
        f"<a href='#' target='_blank' style='display:block;text-align:center;"
        f"padding:.65rem 1rem;background:{PLEX_ACCENT};color:white;border-radius:10px;"
        "text-decoration:none;font-weight:700;'>🚀 Upgrade to Pro</a>",
        unsafe_allow_html=True,
    )

# ============================================================
# Header
# ============================================================
st.markdown(
    f"<h1 style='margin-bottom:0;'>💰 ClearLedger AI</h1>"
    f"<p style='color:{PLEX_SUB};margin-top:.25rem;'>"
    "Your AI-powered money coach · drill down · spot leaks · grow wealth</p>",
    unsafe_allow_html=True,
)

# ============================================================
# Load + parse
# ============================================================
frames: list[pd.DataFrame] = []
errors: list[str] = []
if uploaded:
    for f in uploaded:
        try:
            frames.append(parse_any(f))
        except Exception as e:  # noqa: BLE001
            errors.append(f"❌ {f.name}: {e}")

if use_demo and not frames:
    frames.append(load_demo())

for err in errors:
    st.error(err)

if not frames:
    st.info("👈 Upload statements or enable demo data to begin.")
    st.markdown('<div class="footer">⚡ Powered by <b>Plex Automation</b></div>', unsafe_allow_html=True)
    st.stop()

raw_df = pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)
df_all = enrich(raw_df)

# ============================================================
# Filter bar
# ============================================================
fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
min_d, max_d = df_all["date"].min().date(), df_all["date"].max().date()
with fc1:
    date_range = st.date_input("📅 Date range", value=(min_d, max_d),
                               min_value=min_d, max_value=max_d)
with fc2:
    sources = st.multiselect("🏦 Source", sorted(df_all["source"].unique()),
                             default=sorted(df_all["source"].unique()))
with fc3:
    cats = sorted(df_all["category"].unique())
    selected_cats = st.multiselect("🏷️ Category", cats, default=cats)
with fc4:
    search = st.text_input("🔎 Search payee", "")

start_d = pd.to_datetime(date_range[0]) if isinstance(date_range, tuple) else pd.to_datetime(date_range)
end_d = pd.to_datetime(date_range[1]) if isinstance(date_range, tuple) and len(date_range) > 1 else pd.to_datetime(max_d)

df = df_all[
    (df_all["date"] >= start_d)
    & (df_all["date"] <= end_d + timedelta(days=1))
    & (df_all["source"].isin(sources))
    & (df_all["category"].isin(selected_cats))
]
if search.strip():
    df = df[df["payee"].str.contains(search.strip(), case=False, na=False)]

if df.empty:
    st.warning("No transactions match current filters.")
    st.stop()

# ============================================================
# Compute everything
# ============================================================
health = compute_health(df)
subs = detect_subscriptions(df)
metrics = health["metrics"]
band, band_color = score_band(health["score"])

# ============================================================
# Top metrics
# ============================================================
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("💵 Income", f"${metrics['income']:,.0f}")
m2.metric("💸 Expenses", f"${metrics['expenses']:,.0f}")
m3.metric("📈 Net", f"${metrics['net']:,.0f}",
          delta=f"{metrics['savings_rate']*100:.1f}% saved")
m4.metric("🔁 Subs/mo", f"${(subs['Annual Cost'].sum()/12) if not subs.empty else 0:,.0f}")
m5.metric("🏥 Health", f"{health['score']}/100", delta=band)

st.divider()

# ============================================================
# TABS
# ============================================================
tab_overview, tab_spend, tab_subs, tab_insights, tab_coach, tab_data = st.tabs(
    ["📊 Overview", "🍔 Spending", "🔁 Subscriptions", "💡 Insights", "🤖 AI Coach", "🧾 Transactions"]
)

# -------------------- Overview --------------------
with tab_overview:
    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown("#### 📈 Monthly Cashflow")
        monthly = (
            df.set_index("date")
            .resample("ME")["amount"]
            .agg(income=lambda s: s[s > 0].sum(),
                 expenses=lambda s: -s[s < 0].sum())
            .reset_index()
        )
        monthly["net"] = monthly["income"] - monthly["expenses"]
        monthly["month_label"] = monthly["date"].dt.strftime("%b %Y")
        fig = go.Figure()
        fig.add_bar(name="Income", x=monthly["month_label"], y=monthly["income"],
                    marker_color=PLEX_GREEN)
        fig.add_bar(name="Expenses", x=monthly["month_label"], y=monthly["expenses"],
                    marker_color=PLEX_RED)
        fig.add_scatter(name="Net", x=monthly["month_label"], y=monthly["net"],
                        mode="lines+markers", line=dict(color=PLEX_ACCENT, width=3),
                        marker=dict(size=10))
        fig.update_layout(template=PLOTLY_TEMPLATE, barmode="group",
                          height=380, margin=dict(t=20, b=20),
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### 🏥 Health Score")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health["score"],
            number={"font": {"size": 56, "color": band_color}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": PLEX_TEXT},
                "bar": {"color": band_color, "thickness": 0.3},
                "bgcolor": PLEX_PANEL,
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "rgba(239,68,68,.25)"},
                    {"range": [40, 70], "color": "rgba(245,158,11,.25)"},
                    {"range": [70, 100], "color": "rgba(16,185,129,.25)"},
                ],
            },
        ))
        fig.update_layout(template=PLOTLY_TEMPLATE, height=300,
                          margin=dict(t=10, b=10, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<div style='text-align:center;font-weight:700;color:{band_color};"
                    f"font-size:1.2rem;'>{band}</div>", unsafe_allow_html=True)

    st.markdown("#### 🔬 Why this score?")
    rcols = st.columns(4)
    for i, comp in enumerate(health["reasoning"]):
        with rcols[i]:
            comp_color = PLEX_GREEN if comp["score"] >= 70 else PLEX_AMBER if comp["score"] >= 40 else PLEX_RED
            st.markdown(
                f"""
                <div class='insight-card' style='border-color:{comp_color}66;'>
                    <div style='display:flex;justify-content:space-between;'>
                        <span style='font-weight:700;'>{comp['name']}</span>
                        <span style='color:{PLEX_SUB};'>{comp['weight']}%</span>
                    </div>
                    <div style='font-size:1.8rem;font-weight:800;color:{comp_color};margin:.25rem 0;'>
                        {comp['score']}/100
                    </div>
                    <div style='color:{PLEX_SUB};font-size:.85rem;'>
                        {comp['metric']} · ideal {comp['ideal']}
                    </div>
                    <div style='margin-top:.5rem;font-size:.9rem;'>{comp['explanation']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# -------------------- Spending (drill-down) --------------------
with tab_spend:
    exp = df[df["amount"] < 0].copy()
    if exp.empty:
        st.info("No expenses in current filter.")
    else:
        sc1, sc2 = st.columns(2)

        with sc1:
            st.markdown("#### 🥧 Spending by Category")
            cat_sum = exp.groupby("category")["abs_amount"].sum().sort_values(ascending=False).reset_index()
            fig = px.pie(cat_sum, values="abs_amount", names="category", hole=0.55,
                         color_discrete_sequence=px.colors.qualitative.Vivid)
            fig.update_traces(textposition="outside", textinfo="label+percent")
            fig.update_layout(template=PLOTLY_TEMPLATE, height=400,
                              margin=dict(t=10, b=10), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with sc2:
            st.markdown("#### 🔝 Top Merchants")
            top_merch = exp.groupby("payee")["abs_amount"].sum().nlargest(12).sort_values().reset_index()
            fig = px.bar(top_merch, x="abs_amount", y="payee", orientation="h",
                         color="abs_amount", color_continuous_scale="Plasma",
                         labels={"abs_amount": "Total Spent", "payee": ""})
            fig.update_layout(template=PLOTLY_TEMPLATE, height=400,
                              margin=dict(t=10, b=10), coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        # Treemap (rich drill-down)
        st.markdown("#### 🌳 Drill-down: Category → Merchant")
        tree = exp.groupby(["category", "payee"])["abs_amount"].sum().reset_index()
        fig = px.treemap(tree, path=["category", "payee"], values="abs_amount",
                         color="abs_amount", color_continuous_scale="Plasma")
        fig.update_layout(template=PLOTLY_TEMPLATE, height=480, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # Category drill
        st.markdown("#### 🔎 Drill into a category")
        drill_cat = st.selectbox("Pick a category", cat_sum["category"].tolist())
        drill_df = exp[exp["category"] == drill_cat].sort_values("date", ascending=False)
        d1, d2, d3 = st.columns(3)
        d1.metric("Total", f"${drill_df['abs_amount'].sum():,.2f}")
        d2.metric("Transactions", f"{len(drill_df):,}")
        d3.metric("Avg / txn", f"${drill_df['abs_amount'].mean():,.2f}")

        trend = drill_df.set_index("date").resample("W")["abs_amount"].sum().reset_index()
        fig = px.area(trend, x="date", y="abs_amount",
                      title=f"Weekly spend · {drill_cat}",
                      color_discrete_sequence=[PLEX_ACCENT])
        fig.update_layout(template=PLOTLY_TEMPLATE, height=280, margin=dict(t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            drill_df[["date", "payee", "amount", "source"]].rename(
                columns={"date": "Date", "payee": "Payee",
                         "amount": "Amount", "source": "Source"}
            ),
            hide_index=True, use_container_width=True,
            column_config={
                "Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
                "Amount": st.column_config.NumberColumn(format="$%.2f"),
            },
        )

# -------------------- Subscriptions --------------------
with tab_subs:
    if subs.empty:
        st.info("No recurring subscriptions detected. Try a longer date range.")
    else:
        annual = subs["Annual Cost"].sum()
        monthly_sub = annual / 12
        s1, s2, s3 = st.columns(3)
        s1.metric("Subscriptions", len(subs))
        s2.metric("Monthly cost", f"${monthly_sub:,.2f}")
        s3.metric("Annual cost", f"${annual:,.2f}")

        st.markdown("#### Recurring charges")
        st.dataframe(
            subs,
            hide_index=True, use_container_width=True,
            column_config={
                "Avg Charge": st.column_config.NumberColumn(format="$%.2f"),
                "Annual Cost": st.column_config.NumberColumn(format="$%.2f"),
                "Last Charged": st.column_config.DateColumn(format="YYYY-MM-DD"),
            },
        )

        st.markdown("#### 💡 Cancellation simulator")
        to_cancel = st.multiselect(
            "Select subs you'd cancel:", subs["Merchant"].tolist()
        )
        if to_cancel:
            saved = subs[subs["Merchant"].isin(to_cancel)]["Annual Cost"].sum()
            st.success(f"💰 You'd save **${saved/12:,.2f}/mo** · **${saved:,.2f}/yr** · "
                       f"**${saved*10:,.0f}** over 10 years (no investment growth).")

# -------------------- Insights --------------------
with tab_insights:
    insights = build_insights(df, subs, health)
    if not insights:
        st.info("No notable insights yet — upload more data for richer analysis.")
    for ins in insights:
        st.markdown(
            f"<div class='insight-card {ins['type']}'>"
            f"<h4 style='margin:0 0 .5rem 0;'>{ins['title']}</h4>"
            f"<div>{ins['body']}</div>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### 📅 Spending heatmap (day-of-week × week)")
    exp = df[df["amount"] < 0].copy()
    if not exp.empty:
        exp["dow"] = exp["date"].dt.day_name()
        exp["week"] = exp["date"].dt.to_period("W").dt.start_time
        heat = exp.pivot_table(index="dow", columns="week",
                               values="abs_amount", aggfunc="sum", fill_value=0)
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        heat = heat.reindex([d for d in order if d in heat.index])
        fig = px.imshow(heat, aspect="auto", color_continuous_scale="Plasma",
                        labels=dict(color="$ spent"))
        fig.update_layout(template=PLOTLY_TEMPLATE, height=320, margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

# -------------------- AI Coach --------------------
with tab_coach:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.info("💡 Set `ANTHROPIC_API_KEY` env var in Railway to unlock the **live AI coach**. "
                "Showing rule-based coaching memo below.")
    if st.button("🧠 Generate coaching memo", type="primary"):
        with st.spinner("Analyzing your finances…"):
            st.session_state["coach_memo"] = ai_coach_narrative(df, subs, health)
    memo = st.session_state.get("coach_memo")
    if not memo:
        memo = ai_coach_narrative(df, subs, health)
    st.markdown(memo)

# -------------------- Transactions --------------------
with tab_data:
    st.markdown(f"#### 🧾 {len(df):,} transactions")
    show = df.sort_values("date", ascending=False)[
        ["date", "payee", "category", "amount", "source"]
    ].rename(columns={"date": "Date", "payee": "Payee", "category": "Category",
                      "amount": "Amount", "source": "Source"})
    st.dataframe(
        show,
        hide_index=True, use_container_width=True, height=520,
        column_config={
            "Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Amount": st.column_config.NumberColumn(format="$%.2f"),
        },
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export filtered set (CSV)", csv_bytes,
        file_name=f"clearledger_{datetime.today():%Y%m%d}.csv",
        mime="text/csv",
    )

# ============================================================
# Optional GHL webhook (fire-and-forget)
# ============================================================
ghl_url = os.environ.get("GHL_WEBHOOK_URL")
if ghl_url:
    try:
        import requests  # type: ignore

        requests.post(
            ghl_url,
            json={
                "score": health["score"],
                "income": metrics["income"],
                "expenses": metrics["expenses"],
                "net": metrics["net"],
                "savings_rate": metrics["savings_rate"],
            },
            timeout=3,
        )
    except Exception:
        pass

# ============================================================
# Footer
# ============================================================
st.markdown(
    f"<div class='footer'>⚡ Powered by <b>Plex Automation</b> · "
    f"<a href='https://github.com/ThaGuff/ClearLedgerAI' style='color:{PLEX_SUB};'>GitHub</a> · "
    "Bank-grade in-memory processing</div>",
    unsafe_allow_html=True,
)
