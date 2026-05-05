"""AI coach narrative — Ollama with rule-based fallback."""
from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import requests

from .analytics import score_band

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3:latest")
_OLLAMA_HEADERS = {
    "ngrok-skip-browser-warning": "true",
    "User-Agent": "IronStarLedger/1.0",
}


def coach_narrative(df: pd.DataFrame, subs: pd.DataFrame, health: dict) -> str:
    m = health["metrics"]
    cats = (df[df["amount"] < 0]
            .groupby("category")["amount"].sum().abs()
            .sort_values(ascending=False).head(5))
    summary = {
        "score": health["score"],
        "income": round(m["income"], 2),
        "expenses": round(m["expenses"], 2),
        "net": round(m["net"], 2),
        "savings_rate_pct": round(m["savings_rate"] * 100, 1),
        "expense_ratio_pct": round(m["expense_ratio"] * 100, 1),
        "runway_months": round(m["runway_months"], 1),
        "top_categories": {k: round(float(v), 2) for k, v in cats.to_dict().items()},
        "subscription_monthly": (round(float(subs["Annual Cost"].sum()) / 12, 2)
                                 if not subs.empty else 0),
    }
    prompt = (
        "You are a CFP-level money coach. Given this JSON, write a punchy markdown coaching memo "
        "(<=350 words) with sections: Where you stand, Top 3 wins this month, Risks, "
        f"90-day game plan. Use concrete dollar figures.\n\nData: {summary}"
    )
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.4, "num_predict": 900}},
            headers=_OLLAMA_HEADERS,
            timeout=int(os.environ.get("OLLAMA_TIMEOUT", "120")),
        )
        r.raise_for_status()
        text = r.json().get("response", "").strip()
        if text:
            return text
        return _fallback_narrative(summary, "Empty Ollama response")
    except Exception as e:
        return _fallback_narrative(summary, f"Ollama unreachable at {OLLAMA_URL} — {e}")


def _fallback_narrative(s: dict, err: Optional[str] = None) -> str:
    band = score_band(s["score"])
    sr, er = s["savings_rate_pct"], s["expense_ratio_pct"]
    top = list(s["top_categories"].items())[:3]
    note = (f"\n\n_AI coach offline — using rule-based memo"
            f"{f' ({err})' if err else ''}._")
    lines = [
        f"### {band} · Score {s['score']}/100", "",
        "**Where you stand**",
        f"- Income: **${s['income']:,.0f}** · Expenses: **${s['expenses']:,.0f}** · Net: **${s['net']:,.0f}**",
        f"- Savings rate: **{sr:.1f}%** (target ≥15%) · Expense ratio: **{er:.1f}%** (target <50%)",
        f"- Runway: **{s['runway_months']:.1f} months** · Subs: **${s['subscription_monthly']:,.0f}/mo**",
        "", "**Top 3 wins this month**",
    ]
    for cat, val in top:
        lines.append(f"- Trim **{cat}** by 15% → save **${val*0.15:,.0f}/mo** (**${val*0.15*12:,.0f}/yr**)")
    if s["subscription_monthly"] > 50:
        lines.append(f"- Audit subscriptions — cancelling 25% saves **${s['subscription_monthly']*0.25*12:,.0f}/yr**")
    lines += ["", "**Risks**"]
    risks_added = False
    if sr < 10:
        lines.append("- ⚠ Savings rate <10% — vulnerable to any income shock.")
        risks_added = True
    if s["runway_months"] < 3:
        lines.append("- ⚠ Emergency fund <3 months — single bill can destabilize.")
        risks_added = True
    if er > 90:
        lines.append("- 🚨 Spending nearly all you earn. Lifestyle creep is the #1 killer.")
        risks_added = True
    if not risks_added:
        lines.append("- No critical risks — focus on optimization.")
    lines += ["", "**90-day game plan**",
              "- **Days 1–14:** List every recurring charge. Cancel anything unused 30+ days.",
              f"- **Days 15–45:** Auto-transfer **{max(10, int(sr+5))}%** of every paycheck to a HYSA.",
              "- **Days 46–90:** Move excess into Roth IRA / 401k match / HSA.", note]
    return "\n".join(lines)
