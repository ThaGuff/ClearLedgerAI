"""
ClearLedger AI · Synthwave Money Coach
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
import plotly.io as pio
import streamlit as st

# ============================================================
# Stranger Things / Synthwave palette
# ============================================================
BG_DEEP    = "#06010f"      # near-black, purple shifted
BG_PANEL   = "#10061f"      # deep purple-black panel
BG_CARD    = "#160831"
NEON_PINK  = "#ff10f0"
NEON_RED   = "#ff003c"      # ST-logo red
NEON_CYAN  = "#00f0ff"
NEON_PURPLE= "#a855f7"
NEON_AMBER = "#ffb700"
NEON_GREEN = "#39ff14"
TXT_MAIN   = "#f8f7ff"
TXT_DIM    = "#c4b5fd"
GRID       = "#2a1452"

ST_PALETTE = [NEON_PINK, NEON_CYAN, NEON_PURPLE, NEON_AMBER, NEON_GREEN, "#ff5f1f", "#7209b7", "#3a0ca3"]

# ----- Custom Plotly template (NEVER white) -----
synth = go.layout.Template()
synth.layout = go.Layout(
    paper_bgcolor=BG_PANEL,
    plot_bgcolor=BG_PANEL,
    font=dict(family="JetBrains Mono, ui-monospace, monospace", color=TXT_MAIN, size=12),
    colorway=ST_PALETTE,
    title=dict(font=dict(color=NEON_PINK, size=16)),
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID,
               tickfont=dict(color=TXT_DIM)),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID,
               tickfont=dict(color=TXT_DIM)),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TXT_MAIN)),
    hoverlabel=dict(bgcolor=BG_CARD, bordercolor=NEON_PINK,
                    font=dict(color=TXT_MAIN, family="JetBrains Mono")),
    margin=dict(t=30, b=20, l=20, r=20),
)
pio.templates["synthwave"] = synth
pio.templates.default = "synthwave"
PLOTLY_TEMPLATE = "synthwave"

# ============================================================
# Page config + global CSS
# ============================================================
st.set_page_config(
    page_title="ClearLedger AI · Synthwave Money Coach",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        /* ===== Global background — synth grid + sun gradient ===== */
        .stApp {{
            background:
                radial-gradient(ellipse at 50% 120%, rgba(255,16,240,.18) 0%, transparent 55%),
                radial-gradient(ellipse at 50% -20%, rgba(0,240,255,.10) 0%, transparent 55%),
                linear-gradient(180deg, {BG_DEEP} 0%, #100425 60%, {BG_DEEP} 100%);
            color: {TXT_MAIN};
            background-attachment: fixed;
        }}
        .stApp::before {{
            content:"";
            position:fixed; inset:0; pointer-events:none; z-index:0;
            background-image:
                linear-gradient(transparent 95%, rgba(255,16,240,.08) 96%),
                linear-gradient(90deg, transparent 95%, rgba(0,240,255,.07) 96%);
            background-size: 40px 40px;
            mask-image: linear-gradient(180deg, transparent 0%, black 35%, black 65%, transparent 100%);
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0a0220 0%, {BG_DEEP} 100%);
            border-right: 1px solid {NEON_PINK}33;
        }}
        section[data-testid="stSidebar"] * {{ color:{TXT_MAIN}; }}

        /* ===== Typography ===== */
        h1 {{
            font-family: 'Orbitron', sans-serif !important;
            font-weight: 900 !important;
            letter-spacing: .04em;
            background: linear-gradient(180deg, #fff 30%, {NEON_PINK} 55%, {NEON_RED} 100%);
            -webkit-background-clip: text; background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow:
                0 0 10px rgba(255,16,240,.5),
                0 0 30px rgba(255,16,240,.3);
            margin-bottom: 0;
        }}
        h2, h3, h4 {{
            font-family: 'Orbitron', sans-serif !important;
            color: {TXT_MAIN} !important;
            letter-spacing: .03em;
        }}
        h3, h4 {{ text-shadow: 0 0 8px rgba(0,240,255,.35); }}
        p, label, span, div, li {{ color: {TXT_MAIN}; }}

        /* ===== Metric cards — neon ===== */
        [data-testid="stMetric"] {{
            background: linear-gradient(180deg, rgba(255,16,240,.08), rgba(0,240,255,.05));
            border: 1px solid {NEON_PINK}55;
            border-radius: 12px;
            padding: 14px 16px;
            box-shadow:
                0 0 12px rgba(255,16,240,.15),
                inset 0 0 18px rgba(168,85,247,.1);
        }}
        [data-testid="stMetricLabel"] {{
            color: {NEON_CYAN} !important;
            text-transform: uppercase;
            letter-spacing: .12em;
            font-size: .75rem !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 600 !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {TXT_MAIN} !important;
            font-family: 'Orbitron', sans-serif !important;
            font-weight: 700 !important;
            text-shadow: 0 0 10px rgba(255,16,240,.4);
        }}
        [data-testid="stMetricDelta"] {{
            color: {NEON_GREEN} !important;
            font-family: 'JetBrains Mono', monospace !important;
        }}

        /* ===== Tabs ===== */
        .stTabs [data-baseweb="tab-list"] {{ gap:8px; border-bottom:1px solid {NEON_PINK}33; }}
        .stTabs [data-baseweb="tab"] {{
            background: {BG_PANEL};
            border: 1px solid {NEON_PINK}33;
            border-bottom: none;
            border-radius: 10px 10px 0 0;
            padding: 12px 22px;
            color: {TXT_DIM} !important;
            font-family: 'Orbitron', sans-serif !important;
            font-weight: 600 !important;
            letter-spacing: .08em;
            text-transform: uppercase;
            font-size: .8rem;
            transition: all .15s;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: {NEON_CYAN} !important;
            box-shadow: 0 -3px 12px rgba(0,240,255,.3);
        }}
        .stTabs [aria-selected="true"] {{
            background: linear-gradient(180deg, {NEON_PINK}33, {NEON_PURPLE}11);
            color: {NEON_PINK} !important;
            border-color: {NEON_PINK};
            box-shadow: 0 -4px 18px rgba(255,16,240,.45);
        }}

        /* ===== Buttons ===== */
        .stDownloadButton button, .stButton button {{
            background: linear-gradient(135deg, {NEON_PINK}, {NEON_PURPLE});
            color: white !important;
            border: 1px solid {NEON_PINK};
            font-family: 'Orbitron', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: .08em;
            text-transform: uppercase;
            border-radius: 8px;
            box-shadow: 0 0 18px rgba(255,16,240,.4);
            transition: all .2s;
        }}
        .stDownloadButton button:hover, .stButton button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 0 28px rgba(255,16,240,.7);
            border-color: {NEON_CYAN};
        }}

        /* ===== Inputs ===== */
        input, textarea, .stTextInput input, .stDateInput input, [data-baseweb="select"] > div {{
            background: {BG_PANEL} !important;
            color: {TXT_MAIN} !important;
            border: 1px solid {NEON_PURPLE}55 !important;
            border-radius: 8px !important;
        }}
        input:focus, [data-baseweb="select"] > div:focus-within {{
            border-color: {NEON_CYAN} !important;
            box-shadow: 0 0 12px rgba(0,240,255,.4) !important;
        }}

        /* ===== File uploader ===== */
        [data-testid="stFileUploader"] {{
            background: linear-gradient(135deg, rgba(255,16,240,.08), rgba(0,240,255,.05));
            border: 2px dashed {NEON_PINK}88;
            border-radius: 12px;
            padding: 8px;
        }}
        [data-testid="stFileUploader"] section {{
            background: transparent !important;
            border: none !important;
        }}
        [data-testid="stFileUploader"] small {{ color: {NEON_CYAN} !important; }}

        /* ===== Cards ===== */
        .insight-card {{
            background: linear-gradient(135deg, rgba(168,85,247,.10), rgba(0,240,255,.04));
            border: 1px solid {NEON_PURPLE}66;
            border-left: 4px solid {NEON_PURPLE};
            border-radius: 12px; padding: 14px 18px; margin-bottom: 12px;
            box-shadow: 0 0 16px rgba(168,85,247,.15);
        }}
        .insight-card.warn {{
            background: linear-gradient(135deg, rgba(255,0,60,.12), rgba(255,16,240,.04));
            border-color: {NEON_RED}88; border-left-color: {NEON_RED};
            box-shadow: 0 0 18px rgba(255,0,60,.25);
        }}
        .insight-card.good {{
            background: linear-gradient(135deg, rgba(57,255,20,.10), rgba(0,240,255,.04));
            border-color: {NEON_GREEN}88; border-left-color: {NEON_GREEN};
            box-shadow: 0 0 18px rgba(57,255,20,.2);
        }}
        .insight-card.info {{
            background: linear-gradient(135deg, rgba(255,183,0,.10), rgba(0,240,255,.04));
            border-color: {NEON_AMBER}88; border-left-color: {NEON_AMBER};
            box-shadow: 0 0 18px rgba(255,183,0,.2);
        }}
        .insight-card h4 {{ margin:0 0 .35rem 0; font-size:1.05rem; }}

        .badge {{
            display:inline-block; padding:.3rem .8rem;
            background: linear-gradient(90deg, {NEON_PINK}, {NEON_RED});
            color: white !important; font-family:'Orbitron',sans-serif;
            font-weight:700; letter-spacing:.1em; font-size:.7rem;
            border-radius:999px; text-transform:uppercase;
            box-shadow:0 0 14px rgba(255,16,240,.5);
        }}
        .glow-cyan {{ color:{NEON_CYAN} !important; text-shadow:0 0 8px {NEON_CYAN}; }}
        .glow-pink {{ color:{NEON_PINK} !important; text-shadow:0 0 8px {NEON_PINK}; }}

        .footer {{
            text-align:center; padding:2rem 0 1rem 0;
            color:{NEON_PURPLE} !important; font-family:'JetBrains Mono',monospace;
            font-size:.78rem; letter-spacing:.15em; text-transform:uppercase;
        }}
        .footer b {{ color:{NEON_PINK}; text-shadow:0 0 8px {NEON_PINK}; }}

        /* DataFrame */
        .stDataFrame, [data-testid="stDataFrame"] {{
            background: {BG_PANEL} !important;
            border: 1px solid {NEON_PURPLE}55;
            border-radius: 10px; overflow: hidden;
        }}

        /* Dividers */
        hr, [data-testid="stDivider"] {{
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent, {NEON_PINK}88, transparent) !important;
            margin: 1.5rem 0 !important;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width:10px; height:10px; }}
        ::-webkit-scrollbar-track {{ background:{BG_DEEP}; }}
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient({NEON_PINK}, {NEON_PURPLE});
            border-radius:6px;
        }}

        /* Streamlit alerts: dark with neon */
        [data-testid="stAlert"] {{
            background:{BG_PANEL} !important;
            border:1px solid {NEON_CYAN}55 !important;
            border-radius:10px !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# Parsers
# ============================================================
DATE_HINTS = ["date", "posted", "transaction date", "trans date", "post date", "posting date"]
AMOUNT_HINTS = ["amount", "amt", "value", "total"]
DEBIT_HINTS = ["debit", "withdrawal", "withdrawals"]
CREDIT_HINTS = ["credit", "deposit", "deposits"]
PAYEE_HINTS = ["payee", "description", "memo", "merchant", "name", "details", "transaction"]


def _detect_col(cols: list[str], hints: list[str]) -> Optional[str]:
    lowered = {c.lower().strip(): c for c in cols}
    for h in hints:
        for low, orig in lowered.items():
            if h == low:
                return orig
    for h in hints:
        for low, orig in lowered.items():
            if h in low:
                return orig
    return None


def _frame_from_tabular(raw: pd.DataFrame, source_name: str) -> pd.DataFrame:
    cols = list(raw.columns.astype(str))
    date_c = _detect_col(cols, DATE_HINTS)
    amt_c = _detect_col(cols, AMOUNT_HINTS)
    debit_c = _detect_col(cols, DEBIT_HINTS)
    credit_c = _detect_col(cols, CREDIT_HINTS)
    payee_c = _detect_col(cols, PAYEE_HINTS)
    if not date_c:
        raise ValueError(f"No Date column in {source_name}. Saw: {cols}")
    if amt_c:
        amount = pd.to_numeric(raw[amt_c], errors="coerce")
    elif debit_c or credit_c:
        deb = pd.to_numeric(raw[debit_c], errors="coerce").fillna(0) if debit_c else 0
        cre = pd.to_numeric(raw[credit_c], errors="coerce").fillna(0) if credit_c else 0
        amount = cre - deb
    else:
        raise ValueError(f"No Amount/Debit/Credit column in {source_name}. Saw: {cols}")
    df = pd.DataFrame({
        "date": pd.to_datetime(raw[date_c], errors="coerce"),
        "amount": amount,
        "payee": raw[payee_c].astype(str).str.strip() if payee_c else "Unknown",
        "source": source_name,
    })
    return df.dropna(subset=["date", "amount"]).reset_index(drop=True)


def parse_excel(file) -> pd.DataFrame:
    raw = pd.read_excel(file, engine="openpyxl" if file.name.lower().endswith("xlsx") else None)
    return _frame_from_tabular(raw, file.name)


def parse_csv(file) -> pd.DataFrame:
    file.seek(0)
    raw_bytes = file.read()
    last_err = None
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = raw_bytes.decode(enc)
        except UnicodeDecodeError:
            continue
        for sep in (",", ";", "\t", "|"):
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep, engine="python")
                if df.shape[1] >= 2:
                    return _frame_from_tabular(df, file.name)
            except Exception as e:
                last_err = e
                continue
    raise ValueError(f"Could not parse CSV {file.name}: {last_err}")


def _parse_ofx_text(text: str, source_name: str) -> pd.DataFrame:
    try:
        from ofxparse import OfxParser
        ofx = OfxParser.parse(io.BytesIO(text.encode("utf-8")))
        rows = []
        for account in ofx.accounts:
            for t in account.statement.transactions:
                rows.append({
                    "date": pd.to_datetime(t.date),
                    "amount": float(t.amount),
                    "payee": (t.payee or t.memo or "Unknown").strip(),
                    "source": source_name,
                })
        if rows:
            return pd.DataFrame(rows)
    except Exception:
        pass
    rows: list[dict] = []
    for block in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", text, re.DOTALL | re.IGNORECASE):
        def grab(tag: str) -> str:
            m = re.search(rf"<{tag}>([^<\r\n]+)", block, re.IGNORECASE)
            return m.group(1).strip() if m else ""
        d, a = grab("DTPOSTED"), grab("TRNAMT")
        if not d or not a: continue
        try:
            rows.append({
                "date": pd.to_datetime(d[:8], format="%Y%m%d", errors="coerce"),
                "amount": float(a),
                "payee": grab("NAME") or grab("MEMO") or "Unknown",
                "source": source_name,
            })
        except Exception:
            continue
    if not rows:
        raise ValueError(f"No transactions in {source_name}")
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
                        return _parse_ofx_text(f.read().decode("utf-8", "ignore"), file.name)
        raise ValueError(f"No QFX/OFX in zip {file.name}")
    return _parse_ofx_text(raw.decode("utf-8", "ignore"), file.name)


def parse_any(file) -> pd.DataFrame:
    n = file.name.lower()
    if n.endswith((".xlsx", ".xls")): return parse_excel(file)
    if n.endswith(".csv"): return parse_csv(file)
    if n.endswith(".ofx"): return parse_ofx(file)
    if n.endswith((".qbo", ".qfx")): return parse_qfx(file)
    raise ValueError(f"Unsupported: {file.name}")


# ============================================================
# Categorization
# ============================================================
CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Income",        ["salary","payroll","direct dep","paycheck","stripe payout","interest","dividend","refund"]),
    ("Housing",       ["rent","mortgage","hoa","property tax","landlord","property mgmt"]),
    ("Utilities",     ["electric","pg&e","water","sewer","internet","comcast","xfinity","at&t","verizon","t-mobile","spectrum","cellular"]),
    ("Groceries",     ["whole foods","trader joe","safeway","kroger","costco","wegmans","publix","aldi","sprouts","albertsons","grocery","supermarket","walmart"]),
    ("Dining",        ["starbucks","mcdonald","chipotle","doordash","uber eats","grubhub","restaurant","cafe","coffee","pizza","sushi","panera","chick-fil-a","subway"]),
    ("Transport",     ["uber","lyft","shell","chevron","exxon","bp gas","gas station","parking","transit","metro","amtrak","airline","delta","united","southwest","american air"]),
    ("Subscriptions", ["netflix","spotify","hulu","disney","hbo","max ","youtube","apple.com/bill","icloud","adobe","github","openai","claude","anthropic","chatgpt","notion","dropbox","patreon"]),
    ("Shopping",      ["amazon","ebay","etsy","best buy","apple store","nike","nordstrom","macy","ikea","home depot","lowe","wayfair","target"]),
    ("Health",        ["pharmacy","cvs","walgreens","doctor","clinic","hospital","dental","vision","medical","blue cross","aetna","kaiser"]),
    ("Fitness",       ["gym","peloton","equinox","planet fitness","yoga","crossfit"]),
    ("Entertainment", ["movie","amc","regal","theater","concert","ticketmaster","stubhub","steam","playstation","xbox","nintendo"]),
    ("Personal Care", ["salon","barber","spa","nails","sephora","ulta"]),
    ("Insurance",     ["geico","progressive","state farm","allstate","insurance"]),
    ("Education",     ["tuition","udemy","coursera","school","university","college"]),
    ("Travel",        ["hotel","airbnb","marriott","hilton","expedia","booking"]),
    ("Fees & Interest",["fee","interest charge","overdraft","atm","service charge"]),
    ("Transfers",     ["transfer","zelle","venmo","cash app","paypal"]),
]


def categorize(payee: str, amount: float) -> str:
    p = (payee or "").lower()
    if amount > 0:
        for cat, kw in CATEGORY_RULES:
            if cat == "Income" and any(k in p for k in kw):
                return "Income"
        if any(k in p for k in ["transfer","zelle","venmo","cash app","paypal"]):
            return "Transfers"
        return "Income"
    for cat, kw in CATEGORY_RULES:
        if cat == "Income": continue
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
# Subscription detector
# ============================================================
def detect_subscriptions(df: pd.DataFrame) -> pd.DataFrame:
    exp = df[df["amount"] < 0].copy()
    if exp.empty: return pd.DataFrame()
    exp["payee_norm"] = exp["payee"].str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True).str.strip()
    out = []
    for _, g in exp.groupby("payee_norm"):
        if len(g) < 2: continue
        g = g.sort_values("date")
        deltas = g["date"].diff().dt.days.dropna()
        if deltas.empty: continue
        gap = deltas.median()
        if not (5 <= gap <= 35 or 85 <= gap <= 95): continue
        amts = g["amount"].abs()
        if amts.std() / (amts.mean() + 1e-9) > 0.25: continue
        cadence = "Weekly" if gap < 10 else "Bi-Weekly" if gap < 20 else "Monthly" if gap < 40 else "Quarterly"
        mult = {"Weekly":52,"Bi-Weekly":26,"Monthly":12,"Quarterly":4}[cadence]
        out.append({
            "Merchant": g["payee"].iloc[-1],
            "Cadence": cadence,
            "Avg Charge": amts.mean(),
            "Last Charged": g["date"].max(),
            "Charges": len(g),
            "Annual Cost": amts.mean() * mult,
        })
    return (pd.DataFrame(out).sort_values("Annual Cost", ascending=False).reset_index(drop=True)
            if out else pd.DataFrame())


# ============================================================
# Health Score + Reasoning
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

    ratio = expenses / income if income > 0 else 1.0
    e_score = 1.0 if ratio <= 0.5 else 0.0 if ratio >= 1.0 else 1.0 - (ratio - 0.5) / 0.5
    sr = (net / income) if income > 0 else 0.0
    s_score = 1.0 if sr >= 0.15 else max(0.0, sr / 0.15)
    if len(monthly) >= 2 and monthly.abs().mean() > 0:
        cv = monthly.std() / (monthly.abs().mean() + 1e-9)
        st_score = max(0.0, 1.0 - min(cv, 1.0))
    else:
        st_score, cv = 0.5, 0.0
    runway = (net / monthly_expense) if monthly_expense > 0 else 0
    r_score = 1.0 if runway >= 3 else max(0.0, runway / 3)

    score = round((0.40*e_score + 0.30*s_score + 0.20*st_score + 0.10*r_score) * 100, 1)
    reasoning = [
        {"name":"Expense Ratio","weight":40,"score":round(e_score*100,1),"metric":f"{ratio*100:.1f}%","ideal":"< 50%",
         "explanation": (f"Spending **{ratio*100:.1f}%** of income. " +
                         ("Excellent — well under the 50% ceiling." if ratio < 0.5
                          else "🚨 Above 100% — every dollar earned is consumed by expenses." if ratio >= 1.0
                          else f"Above 50% target. Cutting expenses by **${(expenses-income*0.5):,.0f}** lands you on the ideal ratio."))},
        {"name":"Savings Rate","weight":30,"score":round(s_score*100,1),"metric":f"{sr*100:.1f}%","ideal":"≥ 15%",
         "explanation": (f"Net savings rate is **{sr*100:.1f}%**. " +
                         ("Building wealth on autopilot." if sr >= 0.15
                          else f"Need an extra **${(income*0.15 - net):,.0f}** in net to hit 15%."))},
        {"name":"Cashflow Stability","weight":20,"score":round(st_score*100,1),"metric":f"CV {cv:.2f}","ideal":"low variance",
         "explanation": (f"Monthly cashflow CV = **{cv:.2f}** " +
                         ("(rock-solid)." if cv < 0.3
                          else "(some swings — keep a buffer)." if cv < 0.7
                          else "(highly volatile — irregular income or lumpy bills)."))},
        {"name":"Runway Months","weight":10,"score":round(r_score*100,1),"metric":f"{runway:.1f} mo","ideal":"≥ 3 mo",
         "explanation": (f"Net buffer covers **{runway:.1f} months** of expenses. " +
                         ("Solid emergency cushion." if runway >= 3 else "Below the 3-month minimum."))},
    ]
    return {
        "score": score,
        "components": {r["name"]: r["score"] for r in reasoning},
        "metrics": {"income":income,"expenses":expenses,"net":net,
                    "monthly_expense":monthly_expense,"savings_rate":sr,
                    "expense_ratio":ratio,"runway_months":runway,"monthly_count":months},
        "reasoning": reasoning,
    }


def score_band(s: float) -> tuple[str, str]:
    if s < 40: return "🚨 CRITICAL", NEON_RED
    if s < 70: return "⚠️ FAIR", NEON_AMBER
    return "✅ STRONG", NEON_GREEN


# ============================================================
# Insights
# ============================================================
def build_insights(df: pd.DataFrame, subs: pd.DataFrame, health: dict) -> list[dict]:
    insights: list[dict] = []
    m = health["metrics"]
    cats = df[df["amount"] < 0].groupby("category")["amount"].sum().abs().sort_values(ascending=False)
    if not cats.empty and m["expenses"] > 0:
        top_cat, top_val = cats.index[0], cats.iloc[0]
        share = top_val / m["expenses"] * 100
        if share > 35:
            insights.append({"type":"warn",
                "title": f"⚠️ {top_cat} is eating your budget",
                "body": f"<b>{share:.0f}%</b> of expenses (<span class='glow-pink'>${top_val:,.0f}</span>) → <b>{top_cat}</b>. "
                        f"Cutting 15% saves <span class='glow-cyan'>${top_val*0.15:,.0f}/mo</span> "
                        f"= <b>${top_val*0.15*12:,.0f}/yr</b>."})
    if not subs.empty:
        annual = subs["Annual Cost"].sum()
        insights.append({"type":"info",
            "title": f"🔁 {len(subs)} recurring subscriptions detected",
            "body": f"You're locked into <span class='glow-pink'>${annual/12:,.0f}/mo</span> "
                    f"(<b>${annual:,.0f}/yr</b>). Top hit: <b>{subs.iloc[0]['Merchant']}</b> "
                    f"(${subs.iloc[0]['Annual Cost']:,.0f}/yr)."})
    exp = df[df["amount"] < 0].copy()
    if len(exp) >= 10:
        amts = exp["amount"].abs()
        z = (amts - amts.mean()) / (amts.std() + 1e-9)
        out = exp[z > 2.5].sort_values("amount").head(3)
        if not out.empty:
            lines = "<br>".join([f"• ${row['amount']:,.2f} · {row['payee']} · {row['date']:%b %d}" for _, row in out.iterrows()])
            insights.append({"type":"info",
                "title": f"🔍 {len(out)} unusually large transactions",
                "body": f"These are >2.5σ above your average:<br>{lines}"})
    if m["income"] > 0:
        sr = m["savings_rate"]
        if sr < 0:
            insights.append({"type":"warn",
                "title": "🛑 Spending exceeds income",
                "body": f"You spent <b>${-m['net']:,.0f} more</b> than earned. "
                        "Knife the 3 biggest discretionary categories first."})
        elif sr >= 0.20:
            insights.append({"type":"good",
                "title": f"💪 Strong savings rate ({sr*100:.0f}%)",
                "body": f"Banking <b>${m['net']:,.0f}</b>. Auto-invest into a low-cost index fund "
                        "or max tax-advantaged accounts."})
    dow = exp.groupby(exp["date"].dt.day_name())["amount"].sum().abs()
    if not dow.empty and len(dow) > 3:
        worst = dow.idxmax()
        if dow[worst] > dow.mean() * 1.4:
            insights.append({"type":"info",
                "title": f"📅 {worst}s = your splurge day",
                "body": f"You spend <b>${dow[worst]:,.0f}</b> on {worst}s — "
                        f"{(dow[worst]/dow.mean()-1)*100:.0f}% above weekly avg."})
    if health["score"] >= 70:
        insights.append({"type":"good",
            "title": "✅ Financially healthy",
            "body": f"Score <b>{health['score']}/100</b>. Time to play offense — increase investments and tax optimization."})
    return insights


# ============================================================
# AI Coach
# ============================================================
def ai_coach_narrative(df: pd.DataFrame, subs: pd.DataFrame, health: dict) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    m = health["metrics"]
    cats = df[df["amount"] < 0].groupby("category")["amount"].sum().abs().sort_values(ascending=False).head(5)
    summary = {
        "score": health["score"], "income": round(m["income"],2), "expenses": round(m["expenses"],2),
        "net": round(m["net"],2), "savings_rate_pct": round(m["savings_rate"]*100,1),
        "expense_ratio_pct": round(m["expense_ratio"]*100,1), "runway_months": round(m["runway_months"],1),
        "top_categories": {k: round(float(v),2) for k,v in cats.to_dict().items()},
        "subscription_monthly": round(float(subs["Annual Cost"].sum())/12,2) if not subs.empty else 0,
    }
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
                max_tokens=900,
                messages=[{"role":"user","content":
                    "You are a CFP-level money coach. Given this JSON, write a punchy markdown coaching memo "
                    "(≤350 words) with sections: **Where you stand**, **Top 3 wins this month**, **Risks**, "
                    f"**90-day game plan**. Use concrete dollar figures.\n\nData: {summary}"}],
            )
            return msg.content[0].text
        except Exception as e:
            return _fallback_narrative(summary, str(e))
    return _fallback_narrative(summary)


def _fallback_narrative(s: dict, err: Optional[str] = None) -> str:
    band, _ = score_band(s["score"])
    sr, er = s["savings_rate_pct"], s["expense_ratio_pct"]
    top = list(s["top_categories"].items())[:3]
    note = f"\n\n_Set `ANTHROPIC_API_KEY` env var on Railway to unlock the live AI coach{f' — {err}' if err else ''}._"
    lines = [
        f"### {band} · Score {s['score']}/100", "",
        "**Where you stand**",
        f"- Income: **${s['income']:,.0f}** · Expenses: **${s['expenses']:,.0f}** · Net: **${s['net']:,.0f}**",
        f"- Savings rate: **{sr:.1f}%** (target ≥15%) · Expense ratio: **{er:.1f}%** (target <50%)",
        f"- Runway: **{s['runway_months']:.1f} months** · Subs: **${s['subscription_monthly']:,.0f}/mo**", "",
        "**Top 3 wins this month**",
    ]
    for cat, val in top:
        lines.append(f"- Trim **{cat}** by 15% → save **${val*0.15:,.0f}/mo** (**${val*0.15*12:,.0f}/yr**)")
    if s["subscription_monthly"] > 50:
        lines.append(f"- Audit subs — cancelling 25% saves **${s['subscription_monthly']*0.25*12:,.0f}/yr**")
    lines += ["", "**Risks**"]
    risks_added = False
    if sr < 10: lines.append("- ⚠️ Savings rate <10% — vulnerable to any income shock."); risks_added=True
    if s["runway_months"] < 3: lines.append("- ⚠️ Emergency fund <3 months — single bill can destabilize."); risks_added=True
    if er > 90: lines.append("- 🚨 Spending nearly all you earn. Lifestyle creep is the #1 killer."); risks_added=True
    if not risks_added: lines.append("- No critical risks — focus on optimization.")
    lines += ["",
        "**90-day game plan**",
        "- **Days 1–14:** List every recurring charge. Cancel anything unused 30+ days.",
        f"- **Days 15–45:** Auto-transfer **{max(10, int(sr+5))}%** of every paycheck to a HYSA.",
        "- **Days 46–90:** Move excess into Roth IRA / 401k match / HSA. Set a quarterly review.",
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
    payees = ["Whole Foods","Trader Joe's","Amazon","Starbucks","Doordash","Uber",
              "Shell Gas","Costco","Target","Chipotle","Best Buy","CVS Pharmacy"]
    for d in rng:
        if d.day in (1, 15):
            rows.append({"date":d,"amount":3400.0,"payee":"Acme Corp Payroll","source":"demo"})
        if d.day == 3:
            rows.append({"date":d,"amount":-1850.0,"payee":"Property Management Rent","source":"demo"})
        if d.day == 5:
            rows.append({"date":d,"amount":-89.99,"payee":"AT&T Wireless","source":"demo"})
            rows.append({"date":d,"amount":-15.49,"payee":"Netflix","source":"demo"})
            rows.append({"date":d,"amount":-11.99,"payee":"Spotify","source":"demo"})
            rows.append({"date":d,"amount":-19.99,"payee":"Adobe Creative","source":"demo"})
        if d.day == 12:
            rows.append({"date":d,"amount":-42.00,"payee":"Planet Fitness Gym","source":"demo"})
        for _ in range(np.random.poisson(2)):
            p = payees[np.random.randint(len(payees))]
            amt = -float(np.round(np.random.uniform(8, 140), 2))
            rows.append({"date":d,"amount":amt,"payee":p,"source":"demo"})
    return pd.DataFrame(rows)


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        f"<div style='text-align:center;padding:1rem 0;'>"
        f"<div style='font-family:Orbitron,sans-serif;font-size:1.6rem;font-weight:900;"
        f"background:linear-gradient(180deg,#fff,{NEON_PINK} 60%,{NEON_RED});"
        f"-webkit-background-clip:text;-webkit-text-fill-color:transparent;"
        f"text-shadow:0 0 12px {NEON_PINK}77;letter-spacing:.1em;'>"
        "CLEARLEDGER<br>AI</div>"
        f"<span class='badge' style='margin-top:.5rem;'>SYNTHWAVE COACH</span>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<p style='color:{NEON_CYAN};text-align:center;font-family:JetBrains Mono;"
                "font-size:.75rem;letter-spacing:.1em;'>// UPLOAD STATEMENTS //</p>",
                unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "📥  CSV · Excel · OFX · QFX",
        type=["csv", "xlsx", "xls", "ofx", "qbo", "qfx"],
        accept_multiple_files=True,
        help="Drop multiple files. Auto-detects columns.",
    )
    use_demo = st.toggle("🧪 Use demo data", value=not uploaded)
    st.markdown(
        f"<div style='margin-top:1rem;padding:.75rem;border:1px solid {NEON_CYAN}55;"
        f"border-radius:8px;background:rgba(0,240,255,.05);'>"
        f"<div style='color:{NEON_CYAN};font-family:JetBrains Mono;font-size:.7rem;"
        "letter-spacing:.1em;'>SUPPORTED FORMATS</div>"
        f"<div style='font-family:JetBrains Mono;font-size:.8rem;color:{TXT_MAIN};margin-top:.4rem;'>"
        "✓ .csv (any delimiter)<br>✓ .xlsx / .xls<br>✓ .ofx<br>✓ .qfx / .qbo</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='margin-top:1.5rem;padding:1rem;border-radius:10px;"
        f"background:linear-gradient(135deg,{NEON_PINK}22,{NEON_PURPLE}11);"
        f"border:1px solid {NEON_PINK}66;'>"
        f"<div style='font-family:Orbitron;font-weight:700;color:{NEON_PINK};"
        "letter-spacing:.1em;font-size:.85rem;'>💜 CLEARLEDGER PRO</div>"
        f"<div style='color:{TXT_MAIN};margin:.5rem 0;font-size:.85rem;'>"
        "AI coach · alerts · unlimited history · CSV/PDF export</div>"
        f"<div style='font-family:Orbitron;font-size:1.4rem;color:{NEON_CYAN};"
        f"text-shadow:0 0 10px {NEON_CYAN};'>$9<span style='font-size:.7rem;color:{TXT_DIM};'>/mo</span></div>"
        f"<a href='#' style='display:block;margin-top:.5rem;text-align:center;padding:.5rem;"
        f"background:{NEON_PINK};color:white;border-radius:6px;text-decoration:none;"
        "font-family:Orbitron;font-weight:700;letter-spacing:.1em;font-size:.75rem;"
        f"box-shadow:0 0 14px {NEON_PINK}88;'>UPGRADE</a>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"<p style='color:{NEON_PURPLE};font-family:JetBrains Mono;font-size:.7rem;"
                "text-align:center;margin-top:1rem;letter-spacing:.1em;'>"
                "🔒 IN-MEMORY · NEVER STORED</p>", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================
st.markdown(
    "<h1>CLEARLEDGER AI</h1>"
    f"<p style='color:{NEON_CYAN};font-family:JetBrains Mono;letter-spacing:.15em;"
    "text-transform:uppercase;font-size:.85rem;margin-top:.5rem;'>"
    "// AI Money Coach · Drill Down · Spot Leaks · Build Wealth //"
    "</p>",
    unsafe_allow_html=True,
)

# ============================================================
# Load
# ============================================================
frames: list[pd.DataFrame] = []
errors: list[str] = []
if uploaded:
    for f in uploaded:
        try:
            frames.append(parse_any(f))
            st.toast(f"✓ {f.name} — {len(frames[-1])} txns", icon="💜")
        except Exception as e:
            errors.append(f"❌ {f.name}: {e}")

if use_demo and not frames:
    frames.append(load_demo())

for err in errors:
    st.error(err)

if not frames:
    st.markdown(
        f"<div style='text-align:center;padding:4rem 2rem;border:2px dashed {NEON_PINK}66;"
        f"border-radius:18px;background:linear-gradient(135deg,rgba(255,16,240,.05),rgba(0,240,255,.03));"
        f"box-shadow:0 0 30px rgba(255,16,240,.15);'>"
        f"<div style='font-size:4rem;'>📡</div>"
        f"<h2 style='color:{NEON_PINK};margin:1rem 0;'>AWAITING TRANSMISSION</h2>"
        f"<p style='color:{TXT_DIM};font-family:JetBrains Mono;'>"
        "Upload <b>CSV</b>, <b>Excel</b>, <b>OFX</b>, or <b>QFX</b> in the sidebar — or flip the demo toggle.</p>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="footer">⚡ POWERED BY <b>PLEX AUTOMATION</b></div>', unsafe_allow_html=True)
    st.stop()

raw_df = pd.concat(frames, ignore_index=True).sort_values("date").reset_index(drop=True)
df_all = enrich(raw_df)

# ============================================================
# FILTER BAR
# ============================================================
fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
min_d, max_d = df_all["date"].min().date(), df_all["date"].max().date()
with fc1:
    date_range = st.date_input("📅 Date range", value=(min_d, max_d),
                               min_value=min_d, max_value=max_d)
with fc2:
    sources = st.multiselect("🏦 Source",
                             sorted(df_all["source"].unique()),
                             default=sorted(df_all["source"].unique()))
with fc3:
    cats_avail = sorted(df_all["category"].unique())
    selected_cats = st.multiselect("🏷️ Category", cats_avail, default=cats_avail)
with fc4:
    search = st.text_input("🔎 Search payee", "", placeholder="Amazon, Starbucks…")

start_d = pd.to_datetime(date_range[0]) if isinstance(date_range, tuple) else pd.to_datetime(date_range)
end_d   = pd.to_datetime(date_range[1]) if isinstance(date_range, tuple) and len(date_range) > 1 else pd.to_datetime(max_d)

df = df_all[
    (df_all["date"] >= start_d) & (df_all["date"] <= end_d + timedelta(days=1)) &
    (df_all["source"].isin(sources)) & (df_all["category"].isin(selected_cats))
]
if search.strip():
    df = df[df["payee"].str.contains(search.strip(), case=False, na=False)]

if df.empty:
    st.warning("No transactions match current filters.")
    st.stop()

health = compute_health(df)
subs = detect_subscriptions(df)
metrics = health["metrics"]
band, band_color = score_band(health["score"])

# ============================================================
# TOP METRICS
# ============================================================
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("💵 Income", f"${metrics['income']:,.0f}")
m2.metric("💸 Expenses", f"${metrics['expenses']:,.0f}")
m3.metric("📈 Net", f"${metrics['net']:,.0f}",
          delta=f"{metrics['savings_rate']*100:.1f}% saved")
m4.metric("🔁 Subs/mo", f"${(subs['Annual Cost'].sum()/12) if not subs.empty else 0:,.0f}")
m5.metric("🏥 Health", f"{health['score']}", delta=band)

st.markdown("---")

# ============================================================
# TABS
# ============================================================
tab_overview, tab_spend, tab_subs, tab_insights, tab_coach, tab_data = st.tabs(
    ["🌐 OVERVIEW", "🍔 SPENDING", "🔁 SUBSCRIPTIONS", "💡 INSIGHTS", "🤖 AI COACH", "🧾 TRANSACTIONS"]
)

# ---------- OVERVIEW ----------
with tab_overview:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("#### 📈 MONTHLY CASHFLOW")
        monthly = (df.set_index("date").resample("ME")["amount"]
                   .agg(income=lambda s: s[s>0].sum(), expenses=lambda s: -s[s<0].sum())
                   .reset_index())
        monthly["net"] = monthly["income"] - monthly["expenses"]
        monthly["month_label"] = monthly["date"].dt.strftime("%b %Y")
        fig = go.Figure()
        fig.add_bar(name="Income", x=monthly["month_label"], y=monthly["income"],
                    marker=dict(color=NEON_CYAN, line=dict(color=NEON_CYAN, width=0)),
                    hovertemplate="<b>%{x}</b><br>Income: $%{y:,.0f}<extra></extra>")
        fig.add_bar(name="Expenses", x=monthly["month_label"], y=monthly["expenses"],
                    marker=dict(color=NEON_PINK),
                    hovertemplate="<b>%{x}</b><br>Expenses: $%{y:,.0f}<extra></extra>")
        fig.add_scatter(name="Net", x=monthly["month_label"], y=monthly["net"],
                        mode="lines+markers",
                        line=dict(color=NEON_AMBER, width=4),
                        marker=dict(size=12, color=NEON_AMBER,
                                    line=dict(color="white", width=1)),
                        hovertemplate="<b>%{x}</b><br>Net: $%{y:,.0f}<extra></extra>")
        fig.update_layout(barmode="group", height=380,
                          legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown("#### 🏥 HEALTH SCORE")
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health["score"],
            number={"font":{"size":56,"color":band_color,"family":"Orbitron"}, "suffix":"<span style='font-size:18px'>/100</span>"},
            gauge={
                "axis":{"range":[0,100],"tickcolor":TXT_DIM,"tickfont":{"color":TXT_DIM}},
                "bar":{"color":band_color, "thickness":0.35},
                "bgcolor":BG_PANEL, "borderwidth":0,
                "steps":[
                    {"range":[0,40],"color":"rgba(255,0,60,.25)"},
                    {"range":[40,70],"color":"rgba(255,183,0,.25)"},
                    {"range":[70,100],"color":"rgba(57,255,20,.25)"},
                ],
                "threshold":{"line":{"color":"white","width":3},"thickness":.7,"value":health["score"]},
            },
        ))
        fig.update_layout(height=300, margin=dict(t=20,b=10,l=20,r=20))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown(f"<div style='text-align:center;font-family:Orbitron;font-weight:700;"
                    f"color:{band_color};text-shadow:0 0 10px {band_color};font-size:1.1rem;"
                    f"letter-spacing:.15em;'>{band}</div>", unsafe_allow_html=True)

    st.markdown("#### 🔬 WHY THIS SCORE?")
    rcols = st.columns(4)
    for i, comp in enumerate(health["reasoning"]):
        with rcols[i]:
            cc = NEON_GREEN if comp["score"] >= 70 else NEON_AMBER if comp["score"] >= 40 else NEON_RED
            st.markdown(
                f"""<div class='insight-card' style='border-left-color:{cc};border-color:{cc}66;
                box-shadow:0 0 16px {cc}33;'>
                    <div style='display:flex;justify-content:space-between;'>
                        <span style='font-family:Orbitron;font-weight:700;letter-spacing:.05em;'>{comp['name']}</span>
                        <span style='color:{NEON_CYAN};font-family:JetBrains Mono;font-size:.85rem;'>{comp['weight']}%</span>
                    </div>
                    <div style='font-size:2rem;font-family:Orbitron;font-weight:800;color:{cc};
                                text-shadow:0 0 12px {cc}88;margin:.25rem 0;'>{comp['score']}/100</div>
                    <div style='color:{TXT_DIM};font-family:JetBrains Mono;font-size:.78rem;letter-spacing:.05em;'>
                        {comp['metric']} · ideal {comp['ideal']}
                    </div>
                    <div style='margin-top:.55rem;font-size:.88rem;line-height:1.4;'>{comp['explanation']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

# ---------- SPENDING ----------
with tab_spend:
    exp = df[df["amount"] < 0].copy()
    if exp.empty:
        st.info("No expenses in current filter.")
    else:
        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("#### 🥧 BY CATEGORY")
            cat_sum = exp.groupby("category")["abs_amount"].sum().sort_values(ascending=False).reset_index()
            fig = px.pie(cat_sum, values="abs_amount", names="category", hole=0.6,
                         color_discrete_sequence=ST_PALETTE)
            fig.update_traces(textposition="outside", textinfo="label+percent",
                              marker=dict(line=dict(color=BG_DEEP, width=2)),
                              hovertemplate="<b>%{label}</b><br>$%{value:,.0f} (%{percent})<extra></extra>")
            fig.update_layout(height=420, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with sc2:
            st.markdown("#### 🔝 TOP MERCHANTS")
            top_m = exp.groupby("payee")["abs_amount"].sum().nlargest(12).sort_values().reset_index()
            fig = go.Figure(go.Bar(
                x=top_m["abs_amount"], y=top_m["payee"], orientation="h",
                marker=dict(color=top_m["abs_amount"], colorscale=[[0,NEON_PURPLE],[.5,NEON_PINK],[1,NEON_RED]],
                            line=dict(color=NEON_PINK, width=0)),
                hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
                text=[f"${v:,.0f}" for v in top_m["abs_amount"]],
                textposition="outside", textfont=dict(color=NEON_CYAN, family="JetBrains Mono"),
            ))
            fig.update_layout(height=420, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### 🌳 DRILL-DOWN: CATEGORY → MERCHANT")
        tree = exp.groupby(["category","payee"])["abs_amount"].sum().reset_index()
        fig = px.treemap(tree, path=["category","payee"], values="abs_amount",
                         color="abs_amount",
                         color_continuous_scale=[[0,NEON_PURPLE],[.5,NEON_PINK],[1,NEON_RED]])
        fig.update_traces(marker=dict(line=dict(color=BG_DEEP, width=2)),
                          hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<extra></extra>",
                          textfont=dict(color="white", family="JetBrains Mono"))
        fig.update_layout(height=520, margin=dict(t=10,b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### 🔎 DRILL INTO A CATEGORY")
        drill_cat = st.selectbox("Pick a category", cat_sum["category"].tolist())
        drill_df = exp[exp["category"] == drill_cat].sort_values("date", ascending=False)
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Total spent", f"${drill_df['abs_amount'].sum():,.2f}")
        d2.metric("Transactions", f"{len(drill_df):,}")
        d3.metric("Avg per txn", f"${drill_df['abs_amount'].mean():,.2f}")
        d4.metric("Largest", f"${drill_df['abs_amount'].max():,.2f}")

        trend = drill_df.set_index("date").resample("W")["abs_amount"].sum().reset_index()
        fig = go.Figure()
        fig.add_scatter(x=trend["date"], y=trend["abs_amount"], mode="lines",
                        fill="tozeroy", line=dict(color=NEON_PINK, width=3),
                        fillcolor="rgba(255,16,240,.18)",
                        hovertemplate="<b>Week of %{x|%b %d}</b><br>$%{y:,.0f}<extra></extra>")
        fig.update_layout(height=280, title=f"Weekly spend · {drill_cat}",
                          margin=dict(t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            drill_df[["date","payee","amount","source"]].rename(
                columns={"date":"Date","payee":"Payee","amount":"Amount","source":"Source"}),
            hide_index=True, use_container_width=True,
            column_config={
                "Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
                "Amount": st.column_config.NumberColumn(format="$%.2f"),
            },
        )

# ---------- SUBSCRIPTIONS ----------
with tab_subs:
    if subs.empty:
        st.info("No recurring charges detected. Try a longer date range.")
    else:
        annual = subs["Annual Cost"].sum()
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Subscriptions", len(subs))
        s2.metric("Monthly", f"${annual/12:,.0f}")
        s3.metric("Annual", f"${annual:,.0f}")
        s4.metric("10-yr cost", f"${annual*10:,.0f}")

        st.markdown("#### 💸 RECURRING CHARGES")
        fig = go.Figure(go.Bar(
            x=subs["Annual Cost"], y=subs["Merchant"], orientation="h",
            marker=dict(color=subs["Annual Cost"],
                        colorscale=[[0,NEON_CYAN],[.5,NEON_PINK],[1,NEON_RED]]),
            text=[f"${v:,.0f}/yr ({c})" for v, c in zip(subs["Annual Cost"], subs["Cadence"])],
            textposition="outside", textfont=dict(color=NEON_CYAN, family="JetBrains Mono"),
            hovertemplate="<b>%{y}</b><br>$%{x:,.0f}/yr<extra></extra>",
        ))
        fig.update_layout(height=max(280, len(subs)*36),
                          xaxis_title=None, yaxis_title=None,
                          yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            subs, hide_index=True, use_container_width=True,
            column_config={
                "Avg Charge": st.column_config.NumberColumn(format="$%.2f"),
                "Annual Cost": st.column_config.NumberColumn(format="$%.2f"),
                "Last Charged": st.column_config.DateColumn(format="YYYY-MM-DD"),
            },
        )

        st.markdown("#### 🔪 CANCELLATION SIMULATOR")
        to_cancel = st.multiselect("Select subs to kill:", subs["Merchant"].tolist())
        if to_cancel:
            saved = subs[subs["Merchant"].isin(to_cancel)]["Annual Cost"].sum()
            st.markdown(
                f"<div class='insight-card good'>"
                f"<h4>💰 Projected savings</h4>"
                f"<div style='font-size:1.1rem;'>"
                f"<span class='glow-cyan'>${saved/12:,.2f}/mo</span> · "
                f"<span class='glow-pink'>${saved:,.2f}/yr</span> · "
                f"<b>${saved*10:,.0f}</b> over 10 years</div></div>",
                unsafe_allow_html=True,
            )

# ---------- INSIGHTS ----------
with tab_insights:
    insights = build_insights(df, subs, health)
    if not insights:
        st.info("No notable insights yet — upload more data for richer analysis.")
    for ins in insights:
        st.markdown(
            f"<div class='insight-card {ins['type']}'>"
            f"<h4>{ins['title']}</h4><div>{ins['body']}</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### 📅 SPENDING HEATMAP · DAY-OF-WEEK × WEEK")
    exp = df[df["amount"] < 0].copy()
    if not exp.empty:
        exp["dow"] = exp["date"].dt.day_name()
        exp["week"] = exp["date"].dt.to_period("W").dt.start_time
        heat = exp.pivot_table(index="dow", columns="week",
                               values="abs_amount", aggfunc="sum", fill_value=0)
        order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        heat = heat.reindex([d for d in order if d in heat.index])
        fig = px.imshow(heat, aspect="auto",
                        color_continuous_scale=[[0,BG_PANEL],[.5,NEON_PURPLE],[1,NEON_PINK]],
                        labels=dict(color="$ spent"))
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Week %{x}<br>$%{z:,.0f}<extra></extra>")
        fig.update_layout(height=320, margin=dict(t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)

# ---------- AI COACH ----------
with tab_coach:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.markdown(
            f"<div class='insight-card info'>"
            f"<h4>⚡ ACTIVATE LIVE AI COACH</h4>"
            f"Set <code>ANTHROPIC_API_KEY</code> in Railway → Variables to unlock real-time "
            "Claude-powered coaching. Showing rule-based memo below."
            "</div>",
            unsafe_allow_html=True,
        )
    if st.button("🧠 GENERATE COACHING MEMO", type="primary"):
        with st.spinner("Analyzing your finances…"):
            st.session_state["coach_memo"] = ai_coach_narrative(df, subs, health)
    memo = st.session_state.get("coach_memo") or ai_coach_narrative(df, subs, health)
    st.markdown(
        f"<div class='insight-card' style='font-size:.95rem;'>{memo}</div>",
        unsafe_allow_html=True,
    )

# ---------- TRANSACTIONS ----------
with tab_data:
    st.markdown(f"#### 🧾 {len(df):,} TRANSACTIONS")
    show = df.sort_values("date", ascending=False)[
        ["date","payee","category","amount","source"]
    ].rename(columns={"date":"Date","payee":"Payee","category":"Category",
                      "amount":"Amount","source":"Source"})
    st.dataframe(
        show, hide_index=True, use_container_width=True, height=560,
        column_config={
            "Date": st.column_config.DateColumn(format="YYYY-MM-DD"),
            "Amount": st.column_config.NumberColumn(format="$%.2f"),
        },
    )
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ EXPORT FILTERED CSV", csv_bytes,
        file_name=f"clearledger_{datetime.today():%Y%m%d}.csv",
        mime="text/csv",
    )

# ============================================================
# Optional GHL webhook
# ============================================================
ghl_url = os.environ.get("GHL_WEBHOOK_URL")
if ghl_url:
    try:
        import requests
        requests.post(ghl_url, json={
            "score": health["score"],
            "income": metrics["income"], "expenses": metrics["expenses"],
            "net": metrics["net"], "savings_rate": metrics["savings_rate"],
        }, timeout=3)
    except Exception:
        pass

# ============================================================
# FOOTER
# ============================================================
st.markdown(
    "<div class='footer'>⚡ POWERED BY <b>PLEX AUTOMATION</b> · "
    f"<a href='https://github.com/ThaGuff/ClearLedgerAI' style='color:{NEON_CYAN};'>GITHUB</a> · "
    "BANK-GRADE IN-MEMORY PROCESSING</div>",
    unsafe_allow_html=True,
)
