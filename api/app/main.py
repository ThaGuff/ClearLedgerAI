"""Iron Star Ledger · FastAPI service
Powered by PLEX Automation
"""
from __future__ import annotations

import os
from typing import Optional

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .analytics import (
    build_insights,
    compute_health,
    detect_subscriptions,
    enrich,
    load_demo,
)
from .coach import coach_narrative
from .parsers import parse_any


app = FastAPI(
    title="Iron Star Ledger API",
    description="Interstellar finance navigator backend.",
    version="1.0.0",
)

# CORS — allow the web frontend (Next.js) and any preview origins
_allowed = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:3030,*"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed + ["*"] if "*" in _allowed else _allowed,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Models
# ============================================================
class TransactionDTO(BaseModel):
    date: str
    amount: float
    payee: str
    source: str
    category: Optional[str] = None
    running_balance: Optional[float] = None


class SubscriptionDTO(BaseModel):
    merchant: str
    cadence: str
    avg_charge: float
    last_charged: str
    charges: int
    annual_cost: float
    detected_by: str


class HealthDTO(BaseModel):
    score: float
    band: str
    components: dict
    metrics: dict
    reasoning: list


class TimeSeriesPoint(BaseModel):
    date: str
    income: float
    expenses: float
    net: float
    running_balance: float


class CategoryAggDTO(BaseModel):
    category: str
    total: float
    count: int


class AnalysisResponse(BaseModel):
    transactions: list[TransactionDTO]
    health: HealthDTO
    subscriptions: list[SubscriptionDTO]
    insights: list[dict]
    time_series: list[TimeSeriesPoint]
    by_category: list[CategoryAggDTO]
    by_month: list[dict]
    top_expenses: list[TransactionDTO]


# ============================================================
# Helpers
# ============================================================
def _df_to_transactions(df: pd.DataFrame) -> list[TransactionDTO]:
    return [
        TransactionDTO(
            date=row.date.isoformat() if hasattr(row.date, "isoformat") else str(row.date),
            amount=float(row.amount),
            payee=str(row.payee),
            source=str(row.source),
            category=str(getattr(row, "category", "")) or None,
            running_balance=float(getattr(row, "running_balance", 0.0)),
        )
        for row in df.itertuples()
    ]


def _subs_to_dto(subs: pd.DataFrame) -> list[SubscriptionDTO]:
    if subs.empty:
        return []
    out = []
    for _, r in subs.iterrows():
        last = r["Last Charged"]
        out.append(SubscriptionDTO(
            merchant=str(r["Merchant"]),
            cadence=str(r["Cadence"]),
            avg_charge=float(r["Avg Charge"]),
            last_charged=last.isoformat() if hasattr(last, "isoformat") else str(last),
            charges=int(r["Charges"]),
            annual_cost=float(r["Annual Cost"]),
            detected_by=str(r["Detected By"]),
        ))
    return out


def _build_time_series(df: pd.DataFrame) -> list[TimeSeriesPoint]:
    if df.empty:
        return []
    days = (df["date"].max() - df["date"].min()).days + 1
    rule = "D" if days < 14 else "W" if days < 70 else "ME"
    inc = df[df["amount"] > 0].set_index("date")["amount"].resample(rule).sum()
    exp = df[df["amount"] < 0].set_index("date")["amount"].abs().resample(rule).sum()
    bal = df.set_index("date")["running_balance"].resample(rule).last().ffill()
    idx = inc.index.union(exp.index).union(bal.index)
    inc = inc.reindex(idx).fillna(0.0)
    exp = exp.reindex(idx).fillna(0.0)
    bal = bal.reindex(idx).ffill().fillna(0.0)
    return [
        TimeSeriesPoint(
            date=d.isoformat(),
            income=float(inc.loc[d]),
            expenses=float(exp.loc[d]),
            net=float(inc.loc[d] - exp.loc[d]),
            running_balance=float(bal.loc[d]),
        )
        for d in idx
    ]


def _by_category(df: pd.DataFrame) -> list[CategoryAggDTO]:
    if df.empty:
        return []
    exp = df[df["amount"] < 0]
    if exp.empty:
        return []
    g = exp.groupby("category").agg(total=("amount", lambda s: float(-s.sum())),
                                    count=("amount", "count")).reset_index()
    g = g.sort_values("total", ascending=False)
    return [CategoryAggDTO(category=r.category, total=float(r.total), count=int(r.count))
            for r in g.itertuples()]


def _by_month(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []
    g = df.set_index("date").resample("ME").agg({
        "amount": [
            lambda s: float(s[s > 0].sum()),
            lambda s: float(-s[s < 0].sum()),
        ]
    })
    g.columns = ["income", "expenses"]
    g["net"] = g["income"] - g["expenses"]
    g = g.reset_index()
    return [{
        "month": r.date.isoformat(),
        "income": float(r.income),
        "expenses": float(r.expenses),
        "net": float(r.net),
    } for r in g.itertuples()]


def _top_expenses(df: pd.DataFrame, n: int = 10) -> list[TransactionDTO]:
    if df.empty:
        return []
    exp = df[df["amount"] < 0].nsmallest(n, "amount")
    return _df_to_transactions(exp)


def _build_response(df: pd.DataFrame) -> AnalysisResponse:
    df = enrich(df)
    health = compute_health(df)
    subs = detect_subscriptions(df)
    insights = build_insights(df, subs, health)
    return AnalysisResponse(
        transactions=_df_to_transactions(df),
        health=HealthDTO(**health),
        subscriptions=_subs_to_dto(subs),
        insights=insights,
        time_series=_build_time_series(df),
        by_category=_by_category(df),
        by_month=_by_month(df),
        top_expenses=_top_expenses(df, 10),
    )


# ============================================================
# Routes
# ============================================================
@app.get("/")
def root():
    return {
        "service": "Iron Star Ledger API",
        "powered_by": "PLEX Automation",
        "version": "1.0.0",
        "endpoints": ["/health", "/api/demo", "/api/analyze", "/api/coach"],
    }


@app.get("/health")
def healthcheck():
    return {"status": "ok", "service": "iron-star-ledger-api"}


@app.get("/api/demo", response_model=AnalysisResponse)
def demo():
    df = load_demo()
    return _build_response(df)


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "No files uploaded.")
    frames: list[pd.DataFrame] = []
    errors: list[str] = []
    for f in files:
        try:
            raw = await f.read()
            df = parse_any(f.filename or "upload", raw)
            frames.append(df)
        except Exception as e:
            errors.append(f"{f.filename}: {e}")
    if not frames:
        raise HTTPException(400, f"Could not parse any files. Errors: {errors}")
    combined = (pd.concat(frames, ignore_index=True)
                .sort_values("date").reset_index(drop=True))
    return _build_response(combined)


class CoachRequest(BaseModel):
    transactions: list[TransactionDTO]


@app.post("/api/coach")
def coach(req: CoachRequest):
    if not req.transactions:
        raise HTTPException(400, "No transactions provided.")
    rows = [{"date": pd.to_datetime(t.date), "amount": t.amount,
             "payee": t.payee, "source": t.source}
            for t in req.transactions]
    df = enrich(pd.DataFrame(rows))
    health = compute_health(df)
    subs = detect_subscriptions(df)
    return {"narrative": coach_narrative(df, subs, health)}
