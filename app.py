"""
ClearLedger AI - Personal Finance Analyzer
Powered by Plex Automation
"""

from __future__ import annotations

import io
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st

# ---------- Page config & branding ----------
st.set_page_config(
    page_title="ClearLedger AI - Financial Analyzer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

PLEX_DARK = "#0f0f23"
PLEX_ACCENT = "#7c3aed"

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {PLEX_DARK};
            color: #ffffff;
        }}
        section[data-testid="stSidebar"] {{
            background-color: #131336;
        }}
        h1, h2, h3, h4, h5, h6, p, label, div, span {{
            color: #ffffff !important;
        }}
        [data-testid="stMetricValue"] {{ color: #ffffff !important; }}
        [data-testid="stMetricLabel"] {{ color: #c4b5fd !important; }}
        .stDataFrame, .stTable {{ color: #ffffff; }}
        .footer {{
            text-align: center;
            padding: 1.5rem 0 0.5rem 0;
            color: #9ca3af !important;
            font-size: 0.85rem;
        }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            background: {PLEX_ACCENT};
            color: white !important;
            font-weight: 600;
            font-size: 0.85rem;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Parsers ----------
DATE_HINTS = ["date", "posted", "transaction date", "trans date", "post date"]
AMOUNT_HINTS = ["amount", "amt", "debit", "credit", "value", "total"]
PAYEE_HINTS = ["payee", "description", "memo", "merchant", "name", "details"]


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


def parse_excel(file) -> pd.DataFrame:
    """Parse .xlsx / .xls with auto column detection."""
    raw = pd.read_excel(file, engine="openpyxl" if file.name.endswith("xlsx") else None)
    cols = list(raw.columns.astype(str))
    date_c = _detect_col(cols, DATE_HINTS)
    amt_c = _detect_col(cols, AMOUNT_HINTS)
    payee_c = _detect_col(cols, PAYEE_HINTS)
    if not (date_c and amt_c):
        raise ValueError(
            f"Could not detect Date/Amount columns in {file.name}. "
            f"Found columns: {cols}"
        )
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(raw[date_c], errors="coerce"),
            "amount": pd.to_numeric(raw[amt_c], errors="coerce"),
            "payee": raw[payee_c].astype(str) if payee_c else "Unknown",
            "source": file.name,
        }
    )
    return df.dropna(subset=["date", "amount"])


def parse_ofx(file) -> pd.DataFrame:
    """Parse .ofx via ofxparse (reads bytes, normalizes for parser)."""
    file.seek(0)
    raw = file.read()
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", "ignore")
    else:
        text = raw
    return _parse_qfx_xml(text, file.name)


def _parse_qfx_xml(text: str, source_name: str) -> pd.DataFrame:
    """Parse QFX/QBO content. Strip OFX SGML headers, then parse XML body."""
    # Try ofxparse first (it expects bytes file-like)
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

    # Fallback: regex-extract STMTTRN blocks
    rows: list[dict] = []
    pattern = re.compile(r"<STMTTRN>(.*?)</STMTTRN>", re.DOTALL | re.IGNORECASE)
    for block in pattern.findall(text):

        def grab(tag: str) -> str:
            m = re.search(rf"<{tag}>([^<\r\n]+)", block, re.IGNORECASE)
            return m.group(1).strip() if m else ""

        date_raw = grab("DTPOSTED")
        amount_raw = grab("TRNAMT")
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


def parse_qfx(file) -> pd.DataFrame:
    """Parse .qbo / .qfx — may be plain text OFX or zipped."""
    file.seek(0)
    raw = file.read()
    # Zip case
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                if name.lower().endswith((".qfx", ".qbo", ".ofx", ".xml")):
                    with z.open(name) as f:
                        return _parse_qfx_xml(f.read().decode("utf-8", "ignore"), file.name)
        raise ValueError(f"No QFX/OFX file inside zip {file.name}")
    return _parse_qfx_xml(raw.decode("utf-8", "ignore"), file.name)


def parse_any(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith((".xlsx", ".xls")):
        return parse_excel(file)
    if name.endswith(".ofx"):
        return parse_ofx(file)
    if name.endswith((".qbo", ".qfx")):
        return parse_qfx(file)
    raise ValueError(f"Unsupported file type: {file.name}")


# ---------- Analytics ----------
def compute_health_score(df: pd.DataFrame) -> tuple[float, dict]:
    """Compute 0-100 financial health score with component breakdown."""
    if df.empty:
        return 0.0, {}

    income = df.loc[df["amount"] > 0, "amount"].sum()
    expenses = -df.loc[df["amount"] < 0, "amount"].sum()
    net = income - expenses

    # 40% — Expense Ratio (lower is better, target <50%)
    if income > 0:
        ratio = expenses / income
        expense_score = max(0.0, min(1.0, (1.0 - ratio) / 0.5))  # ratio 0 -> 1, ratio 0.5 -> 1, >0.5 declines
        if ratio <= 0.5:
            expense_score = 1.0
        else:
            expense_score = max(0.0, 1.0 - (ratio - 0.5) / 0.5)
    else:
        expense_score = 0.0

    # 30% — Savings Rate (>15% ideal)
    savings_rate = (net / income) if income > 0 else 0.0
    if savings_rate >= 0.15:
        savings_score = 1.0
    elif savings_rate <= 0:
        savings_score = 0.0
    else:
        savings_score = savings_rate / 0.15

    # 20% — Cashflow Stability (low monthly variance)
    monthly = df.set_index("date").resample("ME")["amount"].sum()
    if len(monthly) >= 2 and monthly.abs().mean() > 0:
        cv = monthly.std() / (monthly.abs().mean() + 1e-9)
        stability_score = max(0.0, min(1.0, 1.0 - min(cv, 1.0)))
    else:
        stability_score = 0.5

    # 10% — Runway Months (net / monthly expense)
    months = max(1, len(monthly))
    monthly_expense = expenses / months if months else expenses
    runway_months = (net / monthly_expense) if monthly_expense > 0 else 0
    if runway_months >= 3:
        runway_score = 1.0
    elif runway_months <= 0:
        runway_score = 0.0
    else:
        runway_score = runway_months / 3

    score = (
        0.40 * expense_score
        + 0.30 * savings_score
        + 0.20 * stability_score
        + 0.10 * runway_score
    ) * 100

    return round(score, 1), {
        "Expense Ratio (40%)": round(expense_score * 100, 1),
        "Savings Rate (30%)": round(savings_score * 100, 1),
        "Cashflow Stability (20%)": round(stability_score * 100, 1),
        "Runway Months (10%)": round(runway_score * 100, 1),
    }


def get_advice(score: float) -> tuple[str, str, list[str]]:
    if score < 40:
        return (
            "🚨 CRITICAL",
            "#dc2626",
            [
                "Cut your top 3 expense categories by 30% immediately.",
                "Build an emergency fund — start with $500 this week.",
                "Pause all non-essential subscriptions today.",
                "Consider debt consolidation to reduce monthly burden.",
            ],
        )
    if score < 70:
        return (
            "⚠️ FAIR",
            "#f59e0b",
            [
                "Aim to save at least 10% of income every month.",
                "Trim 1–2 discretionary categories (dining, subscriptions).",
                "Automate transfers to a high-yield savings account.",
                "Review recurring charges quarterly.",
            ],
        )
    return (
        "✅ GOOD",
        "#10b981",
        [
            "Invest 15%+ of income in tax-advantaged accounts.",
            "Optimize tax strategy — max out 401k / IRA / HSA.",
            "Diversify into index funds and consider real estate.",
            "Review insurance coverage and estate planning.",
        ],
    )


# ---------- UI ----------
st.markdown(
    f"""
    <h1>💰 ClearLedger AI</h1>
    <p><span class="badge">MVP</span>&nbsp;Personal Finance Analyzer · Excel · OFX · QFX</p>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("📥 Upload Statements")
    uploaded = st.file_uploader(
        "Drop Excel, OFX, or QFX files",
        type=["xlsx", "xls", "ofx", "qbo", "qfx"],
        accept_multiple_files=True,
    )
    st.divider()
    use_demo = st.toggle("🧪 Use demo data", value=not uploaded)
    st.divider()
    st.caption("🔒 Files processed in-memory. Nothing stored.")
    st.caption("💳 Pro plan: $9/mo (coming soon)")
    # SaaS slot — Stripe button placeholder
    st.markdown(
        "<a href='#' target='_blank' style='display:inline-block;padding:.5rem 1rem;"
        f"background:{PLEX_ACCENT};color:white;border-radius:8px;text-decoration:none;"
        "font-weight:600;'>Upgrade to Pro →</a>",
        unsafe_allow_html=True,
    )


def load_demo() -> pd.DataFrame:
    import numpy as np

    rng = pd.date_range(end=datetime.today(), periods=120, freq="D")
    np.random.seed(7)
    payees = ["Salary", "Whole Foods", "Amazon", "Netflix", "Uber", "Rent",
              "Starbucks", "Shell Gas", "Costco", "AT&T", "Spotify", "Gym"]
    rows = []
    for d in rng:
        # paycheck biweekly
        if d.day in (1, 15):
            rows.append({"date": d, "amount": 3200.0, "payee": "Salary", "source": "demo.xlsx"})
        # rent monthly
        if d.day == 3:
            rows.append({"date": d, "amount": -1850.0, "payee": "Rent", "source": "demo.xlsx"})
        # random spend
        if np.random.rand() < 0.7:
            p = np.random.choice(payees[1:])
            amt = -float(np.round(np.random.uniform(8, 180), 2))
            rows.append({"date": d, "amount": amt, "payee": p, "source": "demo.xlsx"})
    return pd.DataFrame(rows)


# ---------- Load data ----------
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
    st.info("👈 Upload a file or enable demo data to begin.")
    st.markdown(
        '<div class="footer">Powered by <b>Plex Automation</b></div>',
        unsafe_allow_html=True,
    )
    st.stop()

df = pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)

# ---------- Metrics ----------
income = df.loc[df["amount"] > 0, "amount"].sum()
expenses = -df.loc[df["amount"] < 0, "amount"].sum()
net = income - expenses
balance = df["amount"].sum()  # running net = ending balance vs start

c1, c2, c3, c4 = st.columns(4)
c1.metric("💵 Income", f"${income:,.2f}")
c2.metric("💸 Expenses", f"${expenses:,.2f}")
c3.metric("📈 Net", f"${net:,.2f}", delta=f"{(net/income*100 if income else 0):.1f}% rate")
c4.metric("🏦 Balance Δ", f"${balance:,.2f}")

# ---------- Health score ----------
score, breakdown = compute_health_score(df)
label, color, tips = get_advice(score)

st.markdown("### 🏥 Financial Health Score")
sc1, sc2 = st.columns([1, 2])
with sc1:
    st.markdown(
        f"""
        <div style='text-align:center;padding:1.5rem;border-radius:12px;
        background:linear-gradient(135deg,{color}33,{color}11);border:2px solid {color};'>
            <div style='font-size:3.5rem;font-weight:800;color:{color};'>{score}</div>
            <div style='font-size:1.1rem;color:{color};font-weight:600;'>{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with sc2:
    st.write("**Score breakdown:**")
    st.dataframe(
        pd.DataFrame(list(breakdown.items()), columns=["Component", "Score (0-100)"]),
        hide_index=True,
        use_container_width=True,
    )

st.markdown(f"#### 💡 Recommendations — {label}")
for t in tips:
    st.markdown(f"- {t}")

st.divider()

# ---------- Charts ----------
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown("#### 📈 Monthly Cashflow Trend")
    monthly = (
        df.set_index("date")
        .resample("ME")["amount"]
        .agg(income=lambda s: s[s > 0].sum(), expenses=lambda s: -s[s < 0].sum())
    )
    monthly["net"] = monthly["income"] - monthly["expenses"]
    monthly.index = monthly.index.strftime("%Y-%m")
    st.line_chart(monthly, use_container_width=True, height=320)

with ch2:
    st.markdown("#### 🔝 Top 10 Expenses (by Payee)")
    top_exp = (
        df[df["amount"] < 0]
        .groupby("payee")["amount"]
        .sum()
        .abs()
        .nlargest(10)
        .sort_values()
    )
    st.bar_chart(top_exp, use_container_width=True, height=320, horizontal=True)

# ---------- Recent transactions ----------
st.markdown("#### 🧾 Recent Transactions (last 20)")
recent = df.sort_values("date", ascending=False).head(20).copy()
recent["date"] = recent["date"].dt.strftime("%Y-%m-%d")
recent["amount"] = recent["amount"].map(lambda x: f"${x:,.2f}")
st.dataframe(recent, hide_index=True, use_container_width=True)

# ---------- CSV export ----------
csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Export full dataset (CSV)",
    csv_bytes,
    file_name=f"clearledger_export_{datetime.today():%Y%m%d}.csv",
    mime="text/csv",
)

# ---------- Webhook placeholder (GHL) ----------
ghl_url = os.environ.get("GHL_WEBHOOK_URL")
if ghl_url:
    try:
        import requests  # type: ignore

        requests.post(
            ghl_url,
            json={"score": score, "income": income, "expenses": expenses, "net": net},
            timeout=3,
        )
    except Exception:
        pass

# ---------- Footer ----------
st.markdown(
    '<div class="footer">⚡ Powered by <b>Plex Automation</b> · '
    "<a href='https://github.com/ThaGuff/ClearLedgerAI' style='color:#a78bfa;'>GitHub</a></div>",
    unsafe_allow_html=True,
)
