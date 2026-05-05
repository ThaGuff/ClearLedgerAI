"""Categorization, enrichment, subscriptions, health score, insights.
Ported from Streamlit app.py for Iron Star Ledger API.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd


NON_SPEND_CATEGORIES = {"Transfers", "Income", "Income (unverified)"}


CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Income",        ["salary","payroll","direct dep","paycheck","stripe payout","interest payment",
                       "dividend","refund","reimbursement","tax refund","ach credit","irs treas"]),
    ("Housing",       ["rent","mortgage","hoa","property tax","landlord","property mgmt",
                       "apartment","leasing","real estate"]),
    ("Utilities",     ["electric","pg&e","con ed","water","sewer","internet","comcast","xfinity",
                       "att","at&t","verizon","tmobile","t-mobile","spectrum","cellular","sprint",
                       "duke energy","national grid","gas company","cox comm"]),
    ("Groceries",     ["whole foods","trader joe","safeway","kroger","costco","wegmans","publix",
                       "aldi","sprouts","albertsons","grocery","supermarket","walmart","heb",
                       "harris teeter","stop shop","food lion","meijer","giant"]),
    ("Dining",        ["starbucks","mcdonald","chipotle","doordash","uber eats","grubhub",
                       "restaurant","cafe","coffee","pizza","sushi","panera","chick-fil-a",
                       "subway","taco bell","wendy","burger","kfc","dunkin","sonic","denny"]),
    ("Transport",     ["uber","lyft","shell","chevron","exxon","bp gas","gas station","parking",
                       "transit","metro","amtrak","airline","delta","united","southwest",
                       "american air","jetblue","alaska air","mta","bart","caltrain","toll"]),
    ("Subscriptions", ["netflix","spotify","hulu","disney+","disney plus","hbo","max ","youtube",
                       "apple.com/bill","apple bill","icloud","adobe","github","openai","claude",
                       "anthropic","chatgpt","notion","dropbox","patreon","peacock","paramount",
                       "audible","kindle unlim","crunchyroll","prime video","linkedin"]),
    ("Shopping",      ["amazon","amzn","ebay","etsy","best buy","apple store","nike","nordstrom",
                       "macy","ikea","home depot","lowe","wayfair","target","tj maxx","ross",
                       "marshalls","old navy","gap","zara","h&m","sephora"]),
    ("Health",        ["pharmacy","cvs","walgreens","doctor","clinic","hospital","dental",
                       "vision","medical","blue cross","aetna","kaiser","cigna","humana",
                       "rite aid","quest diag","labcorp"]),
    ("Fitness",       ["gym","peloton","equinox","planet fitness","yoga","crossfit","24 hour fit",
                       "lifetime fit","la fitness","orangetheory"]),
    ("Entertainment", ["movie","amc","regal","theater","concert","ticketmaster","stubhub","steam",
                       "playstation","xbox","nintendo","cinemark","fandango"]),
    ("Personal Care", ["salon","barber","spa","nails","sephora","ulta","supercuts","massage"]),
    ("Insurance",     ["geico","progressive","state farm","allstate","insurance","liberty mut",
                       "farmers ins","nationwide"]),
    ("Education",     ["tuition","udemy","coursera","school","university","college","sallie mae",
                       "nelnet","loan servicing","masterclass","skillshare"]),
    ("Travel",        ["hotel","airbnb","marriott","hilton","expedia","booking","hyatt","ihg",
                       "vrbo","kayak","priceline"]),
    ("Fees & Interest",["fee","interest charge","overdraft","atm","service charge","late fee",
                        "annual fee","foreign trans"]),
    ("Transfers",     ["transfer","zelle","venmo","cash app","paypal","wire","ach transfer"]),
]


def _normalize(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.lower()
    s = re.sub(r"[*#]", " ", s)
    s = re.sub(r"\d{4,}", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def categorize(payee: str, amount: float) -> str:
    p = _normalize(payee)
    for cat, kw in CATEGORY_RULES:
        if any(k in p for k in kw):
            if cat == "Income" and amount < 0:
                continue
            return cat
    if amount > 0:
        return "Income (unverified)"
    return "Other"


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_values("date").reset_index(drop=True)
    df["category"] = [categorize(p, a) for p, a in zip(df["payee"], df["amount"])]
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["weekday"] = df["date"].dt.day_name()
    df["abs_amount"] = df["amount"].abs()
    df["type"] = np.where(df["amount"] > 0, "Income", "Expense")
    df["running_balance"] = df["amount"].cumsum()
    return df


def detect_subscriptions(df: pd.DataFrame) -> pd.DataFrame:
    exp = df[df["amount"] < 0].copy()
    if exp.empty:
        return pd.DataFrame()
    exp["payee_norm"] = exp["payee"].apply(_normalize)
    out: list[dict] = []

    for _, g in exp.groupby("payee_norm"):
        if len(g) < 2:
            continue
        g = g.sort_values("date")
        deltas = g["date"].diff().dt.days.dropna()
        if deltas.empty:
            continue
        gap = float(deltas.median())
        if not (5 <= gap <= 35 or 85 <= gap <= 95):
            continue
        amts = g["amount"].abs()
        if amts.std() / (amts.mean() + 1e-9) > 0.25:
            continue
        cadence = ("Weekly" if gap < 10 else "Bi-Weekly" if gap < 20
                   else "Monthly" if gap < 40 else "Quarterly")
        mult = {"Weekly": 52, "Bi-Weekly": 26, "Monthly": 12, "Quarterly": 4}[cadence]
        out.append({
            "Merchant": g["payee"].iloc[-1],
            "Cadence": cadence,
            "Avg Charge": float(amts.mean()),
            "Last Charged": g["date"].max(),
            "Charges": int(len(g)),
            "Annual Cost": float(amts.mean() * mult),
            "Detected By": "Cadence",
        })

    seen = {row["Merchant"].lower() for row in out}
    sub_kw = [k for cat, kws in CATEGORY_RULES if cat == "Subscriptions" for k in kws]
    for _, g in exp.groupby("payee_norm"):
        merchant = g["payee"].iloc[-1]
        if merchant.lower() in seen:
            continue
        p = _normalize(merchant)
        if not any(k in p for k in sub_kw):
            continue
        amts = g["amount"].abs()
        out.append({
            "Merchant": merchant,
            "Cadence": "Monthly (est)",
            "Avg Charge": float(amts.mean()),
            "Last Charged": g["date"].max(),
            "Charges": int(len(g)),
            "Annual Cost": float(amts.mean() * 12),
            "Detected By": "Keyword",
        })

    if not out:
        return pd.DataFrame()
    return (pd.DataFrame(out)
            .sort_values("Annual Cost", ascending=False)
            .reset_index(drop=True))


def compute_health(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"score": 0, "components": {}, "metrics": {}, "reasoning": []}

    spend_mask = df["amount"] < 0
    real_spend_mask = spend_mask & ~df["category"].isin(NON_SPEND_CATEGORIES)
    income_mask = (df["amount"] > 0) & (df["category"] == "Income")

    income = float(df.loc[income_mask, "amount"].sum())
    expenses = float(-df.loc[real_spend_mask, "amount"].sum())
    transfers = float(df.loc[df["category"] == "Transfers", "amount"].abs().sum())
    unverified_income = float(df.loc[df["category"] == "Income (unverified)", "amount"].sum())
    net = income - expenses

    days = max(1, (df["date"].max() - df["date"].min()).days + 1)
    months_span = days / 30.4375
    monthly_expense = expenses / months_span if months_span > 0 else expenses
    monthly_income = income / months_span if months_span > 0 else income

    ratio = expenses / income if income > 0 else 1.0
    e_score = 1.0 if ratio <= 0.5 else 0.0 if ratio >= 1.0 else 1.0 - (ratio - 0.5) / 0.5

    sr = (net / income) if income > 0 else 0.0
    s_score = 1.0 if sr >= 0.15 else max(0.0, sr / 0.15) if sr > 0 else 0.0

    monthly_net = (df.loc[~df["category"].isin({"Transfers"})]
                   .set_index("date")
                   .resample("ME")["amount"].sum())
    months = max(1, len(monthly_net))
    have_stability = len(monthly_net) >= 2 and monthly_net.abs().mean() > 0
    if have_stability:
        cv = float(monthly_net.std() / (monthly_net.abs().mean() + 1e-9))
        st_score: Optional[float] = max(0.0, 1.0 - min(cv, 1.0))
    else:
        cv, st_score = 0.0, None

    buffer_months = (net / monthly_expense) if monthly_expense > 0 else 0.0
    r_score = 1.0 if buffer_months >= 3 else max(0.0, buffer_months / 3)

    if st_score is None:
        weights = {"e": 0.52, "s": 0.38, "st": 0.0, "r": 0.10}
        st_display, cv_display = 0, 0.0
    else:
        weights = {"e": 0.40, "s": 0.30, "st": 0.20, "r": 0.10}
        st_display, cv_display = round(st_score * 100, 1), cv

    score = round((weights["e"] * e_score + weights["s"] * s_score
                   + weights["st"] * (st_score or 0) + weights["r"] * r_score) * 100, 1)

    if ratio < 0.5:
        e_txt = "Excellent — well under the 50% ceiling. Disposable income is healthy."
    elif ratio >= 1.0:
        e_txt = f"Spending ${expenses-income:,.0f} more than earned. Every dollar in is going out."
    else:
        e_txt = f"Above the 50% target. Trimming ${(expenses-income*0.5):,.0f} lands you on the ideal."

    if sr >= 0.15:
        s_txt = "Building wealth on autopilot. Consider directing surplus to investments."
    elif sr > 0:
        s_txt = f"Saving {sr*100:.1f}% of income. Need ${(income*0.15 - net):,.0f} more in net to hit the 15% target."
    else:
        s_txt = f"Negative savings — drawing down by ${-net:,.0f} over this period."

    if st_score is None:
        st_txt = (f"Need at least 2 full months of data to gauge stability. "
                  f"Currently spans {months_span:.1f} months — keep uploading.")
    elif cv < 0.3:
        st_txt = f"Monthly cashflow is rock-solid (CV {cv:.2f}). Predictable budgeting."
    elif cv < 0.7:
        st_txt = f"Some swings (CV {cv:.2f}). Maintain a buffer for variable months."
    else:
        st_txt = f"Highly volatile (CV {cv:.2f}) — irregular income or lumpy bills are stressing the budget."

    if buffer_months >= 3:
        r_txt = f"Net surplus would cover {buffer_months:.1f} months of spend. Solid cushion."
    elif buffer_months > 0:
        r_txt = f"Surplus covers only {buffer_months:.1f} months of spend. Build to 3+ months."
    else:
        r_txt = "No surplus to bank — focus on reducing the largest expense category first."

    reasoning = [
        {"name": "Expense Ratio", "weight": int(weights["e"] * 100), "score": round(e_score * 100, 1),
         "metric": f"{ratio*100:.1f}%", "ideal": "< 50%", "explanation": e_txt},
        {"name": "Savings Rate", "weight": int(weights["s"] * 100), "score": round(s_score * 100, 1),
         "metric": f"{sr*100:.1f}%", "ideal": ">= 15%", "explanation": s_txt},
        {"name": "Cashflow Stability", "weight": int(weights["st"] * 100), "score": st_display,
         "metric": (f"CV {cv:.2f}" if st_score is not None else "n/a"),
         "ideal": "low variance", "explanation": st_txt},
        {"name": "Savings Buffer", "weight": int(weights["r"] * 100), "score": round(r_score * 100, 1),
         "metric": f"{buffer_months:.1f} mo", "ideal": ">= 3 mo", "explanation": r_txt},
    ]

    return {
        "score": score,
        "band": score_band(score),
        "components": {r["name"]: r["score"] for r in reasoning},
        "metrics": {
            "income": income, "expenses": expenses, "net": net,
            "transfers": transfers, "unverified_income": unverified_income,
            "monthly_expense": monthly_expense, "monthly_income": monthly_income,
            "savings_rate": sr, "expense_ratio": ratio,
            "buffer_months": buffer_months, "runway_months": buffer_months,
            "monthly_count": months, "days_span": days, "months_span": months_span,
        },
        "reasoning": reasoning,
    }


def score_band(s: float) -> str:
    if s < 40:
        return "Critical"
    if s < 70:
        return "Fair"
    return "Strong"


def build_insights(df: pd.DataFrame, subs: pd.DataFrame, health: dict) -> list[dict]:
    insights: list[dict] = []
    m = health["metrics"]
    cats = (df[df["amount"] < 0]
            .groupby("category")["amount"].sum().abs()
            .sort_values(ascending=False))
    if not cats.empty and m["expenses"] > 0:
        top_cat, top_val = cats.index[0], cats.iloc[0]
        share = top_val / m["expenses"] * 100
        if share > 35:
            insights.append({
                "type": "warn",
                "title": f"{top_cat} dominates your spending",
                "body": (f"{share:.0f}% of expenses (${top_val:,.0f}) go to {top_cat}. "
                         f"Trimming 15% saves ${top_val*0.15:,.0f}/mo "
                         f"= ${top_val*0.15*12:,.0f}/yr."),
            })
    if not subs.empty:
        annual = subs["Annual Cost"].sum()
        insights.append({
            "type": "info",
            "title": f"{len(subs)} recurring subscriptions detected",
            "body": (f"Locked into ${annual/12:,.0f}/mo (${annual:,.0f}/yr). "
                     f"Top: {subs.iloc[0]['Merchant']} (${subs.iloc[0]['Annual Cost']:,.0f}/yr)."),
        })
    exp = df[df["amount"] < 0].copy()
    if len(exp) >= 10:
        amts = exp["amount"].abs()
        z = (amts - amts.mean()) / (amts.std() + 1e-9)
        out = exp[z > 2.5].sort_values("amount").head(3)
        if not out.empty:
            lines = " | ".join([f"${row['amount']:,.2f} · {row['payee']}"
                                for _, row in out.iterrows()])
            insights.append({
                "type": "info",
                "title": f"{len(out)} unusually large transactions",
                "body": f"2.5+ standard deviations above average: {lines}",
            })
    if m["income"] > 0:
        sr = m["savings_rate"]
        if sr < 0:
            insights.append({
                "type": "warn",
                "title": "Spending exceeds income",
                "body": (f"You spent ${-m['net']:,.0f} more than you earned. "
                         "Trim discretionary categories first (Dining, Subscriptions, Shopping)."),
            })
        elif sr >= 0.20:
            insights.append({
                "type": "good",
                "title": f"Strong savings rate ({sr*100:.0f}%)",
                "body": (f"Banking ${m['net']:,.0f}. Auto-invest into a low-cost index fund "
                         "or max tax-advantaged accounts."),
            })
    dow = exp.groupby(exp["date"].dt.day_name())["amount"].sum().abs()
    if not dow.empty and len(dow) > 3:
        worst = dow.idxmax()
        if dow[worst] > dow.mean() * 1.4:
            insights.append({
                "type": "info",
                "title": f"{worst}s are your highest-spend day",
                "body": (f"You spend ${dow[worst]:,.0f} on {worst}s — "
                         f"{(dow[worst]/dow.mean()-1)*100:.0f}% above weekly average."),
            })
    if health["score"] >= 70:
        insights.append({
            "type": "good",
            "title": "Financially healthy",
            "body": (f"Score {health['score']}/100. Time to play offense — "
                     "increase investments and tax optimization."),
        })
    return insights


def load_demo() -> pd.DataFrame:
    rng = pd.date_range(end=datetime.today(), periods=180, freq="D")
    np.random.seed(7)
    rows = []
    payees = ["Whole Foods", "Trader Joe's", "Amazon", "Starbucks", "Doordash", "Uber",
              "Shell Gas", "Costco", "Target", "Chipotle", "Best Buy", "CVS Pharmacy"]
    for d in rng:
        if d.day in (1, 15):
            rows.append({"date": d, "amount": 3400.0, "payee": "Acme Corp Payroll", "source": "demo"})
        if d.day == 3:
            rows.append({"date": d, "amount": -1850.0, "payee": "Property Management Rent", "source": "demo"})
        if d.day == 5:
            rows.append({"date": d, "amount": -89.99, "payee": "AT&T Wireless", "source": "demo"})
            rows.append({"date": d, "amount": -15.49, "payee": "Netflix", "source": "demo"})
            rows.append({"date": d, "amount": -11.99, "payee": "Spotify", "source": "demo"})
            rows.append({"date": d, "amount": -19.99, "payee": "Adobe Creative", "source": "demo"})
        if d.day == 12:
            rows.append({"date": d, "amount": -42.00, "payee": "Planet Fitness Gym", "source": "demo"})
        for _ in range(np.random.poisson(2)):
            p = payees[np.random.randint(len(payees))]
            amt = -float(np.round(np.random.uniform(8, 140), 2))
            rows.append({"date": d, "amount": amt, "payee": p, "source": "demo"})
    return pd.DataFrame(rows)
