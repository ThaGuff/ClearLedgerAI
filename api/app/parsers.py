"""File parsers for CSV / Excel / OFX / QFX statements.
Ported from Streamlit app.py for Iron Star Ledger API.
"""
from __future__ import annotations

import io
import re
import zipfile
from typing import Optional, BinaryIO, Tuple

import pandas as pd


DATE_HINTS = ["date", "posted", "transaction date", "trans date", "post date",
              "posting date", "transaction"]
AMOUNT_HINTS = ["amount", "amt", "value", "total", "transaction amount"]
DEBIT_HINTS = ["debit", "withdrawal", "withdrawals", "money out", "outflow", "spent"]
CREDIT_HINTS = ["credit", "deposit", "deposits", "money in", "inflow"]
PAYEE_HINTS = ["description", "payee", "merchant", "name", "memo", "details",
               "transaction description", "narration", "particulars"]
TYPE_HINTS = ["transaction type", "trans type", "type", "dr/cr", "debit/credit",
              "credit/debit", "txn type"]
DEBIT_TYPE_TOKENS = {"debit", "withdrawal", "dr", "purchase", "payment", "fee",
                     "charge", "outflow", "out", "expense", "spend", "sale"}
CREDIT_TYPE_TOKENS = {"credit", "deposit", "cr", "refund", "interest", "inflow",
                      "in", "income", "salary", "payroll"}


def _clean_amount(v) -> Optional[float]:
    if pd.isna(v):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s or s.lower() in ("nan", "none", "-", "—"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[(),$£€¥₹\s]", "", s).replace("USD", "").replace("CAD", "")
    s = s.replace(",", "").replace("'", "")
    if neg:
        s = "-" + s
    try:
        return float(s)
    except ValueError:
        return None


def _clean_amount_series(s: pd.Series) -> pd.Series:
    return s.apply(_clean_amount)


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


def _frame_from_tabular(raw: pd.DataFrame, source_name: str) -> Tuple[pd.DataFrame, dict]:
    raw = raw.copy()
    raw.columns = [str(c).strip() for c in raw.columns]
    cols = list(raw.columns)
    date_c = _detect_col(cols, DATE_HINTS)
    amt_c = _detect_col(cols, AMOUNT_HINTS)
    debit_c = _detect_col(cols, DEBIT_HINTS)
    credit_c = _detect_col(cols, CREDIT_HINTS)
    payee_c = _detect_col(cols, PAYEE_HINTS)
    type_c = _detect_col(cols, TYPE_HINTS)
    if amt_c:
        if debit_c == amt_c:
            debit_c = None
        if credit_c == amt_c:
            credit_c = None

    meta = {"columns": cols, "date_col": date_c, "amount_col": amt_c,
            "debit_col": debit_c, "credit_col": credit_c, "payee_col": payee_c,
            "type_col": type_c}

    if not date_c:
        raise ValueError(f"No Date column detected. Columns found: {cols}")

    if amt_c:
        amount = _clean_amount_series(raw[amt_c])
        non_null = amount.dropna()
        if len(non_null) > 0 and type_c and (non_null >= 0).all():
            t = raw[type_c].astype(str).str.lower().str.strip()
            sign = pd.Series(1.0, index=amount.index)
            sign[t.apply(lambda x: any(tok in x for tok in DEBIT_TYPE_TOKENS))] = -1.0
            amount = amount.abs() * sign
            meta["sign_applied_from_type"] = True
    elif debit_c or credit_c:
        deb = _clean_amount_series(raw[debit_c]).fillna(0).abs() if debit_c else 0
        cre = _clean_amount_series(raw[credit_c]).fillna(0).abs() if credit_c else 0
        amount = cre - deb
    else:
        raise ValueError(f"No Amount/Debit/Credit column detected. Columns: {cols}")

    parsed_dates = pd.to_datetime(raw[date_c], errors="coerce")
    if parsed_dates.notna().sum() == 0:
        parsed_dates = pd.to_datetime(raw[date_c], errors="coerce", dayfirst=True)

    df = pd.DataFrame({
        "date": parsed_dates,
        "amount": amount,
        "payee": raw[payee_c].astype(str).str.strip() if payee_c else "Unknown",
        "source": source_name,
    }).dropna(subset=["date", "amount"]).reset_index(drop=True)

    if df.empty:
        raise ValueError(
            f"All rows had unparseable dates or amounts. "
            f"Detected: date={date_c}, amount={amt_c or f'{debit_c}/{credit_c}'}"
        )
    return df, meta


def _read_csv_smart(text: str, source_name: str) -> pd.DataFrame:
    best = None
    best_cols = 0
    for skip in range(0, 6):
        for sep in (",", ";", "\t", "|"):
            try:
                df = pd.read_csv(io.StringIO(text), sep=sep, engine="python",
                                 skiprows=skip, on_bad_lines="skip")
                if df.shape[1] > best_cols and df.shape[0] > 0:
                    cols_low = " ".join(str(c).lower() for c in df.columns)
                    score = df.shape[1]
                    if any(k in cols_low for k in DATE_HINTS):
                        score += 5
                    if any(k in cols_low for k in AMOUNT_HINTS + DEBIT_HINTS + CREDIT_HINTS):
                        score += 5
                    if score > best_cols:
                        best, best_cols = df, score
            except Exception:
                continue
    if best is None or best.empty:
        raise ValueError(f"Could not read CSV: {source_name}")
    return best


def parse_csv(name: str, raw_bytes: bytes) -> pd.DataFrame:
    text = None
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError(f"Could not decode CSV: {name}")
    raw = _read_csv_smart(text, name)
    parsed, _ = _frame_from_tabular(raw, name)
    return parsed


def parse_excel(name: str, raw_bytes: bytes) -> pd.DataFrame:
    engine = "openpyxl" if name.lower().endswith("xlsx") else None
    raw = pd.read_excel(io.BytesIO(raw_bytes), engine=engine)
    parsed, _ = _frame_from_tabular(raw, name)
    return parsed


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
    rows = []
    for block in re.findall(r"<STMTTRN>(.*?)</STMTTRN>", text, re.DOTALL | re.IGNORECASE):
        def grab(tag, b=block):
            m = re.search(rf"<{tag}>([^<\r\n]+)", b, re.IGNORECASE)
            return m.group(1).strip() if m else ""
        d, a = grab("DTPOSTED"), grab("TRNAMT")
        if not d or not a:
            continue
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


def parse_ofx(name: str, raw_bytes: bytes) -> pd.DataFrame:
    text = raw_bytes.decode("utf-8", "ignore")
    return _parse_ofx_text(text, name)


def parse_qfx(name: str, raw_bytes: bytes) -> pd.DataFrame:
    if raw_bytes[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
            for inner in z.namelist():
                if inner.lower().endswith((".qfx", ".qbo", ".ofx", ".xml")):
                    with z.open(inner) as f:
                        return _parse_ofx_text(
                            f.read().decode("utf-8", "ignore"), name
                        )
        raise ValueError(f"No QFX/OFX in zip {name}")
    return _parse_ofx_text(raw_bytes.decode("utf-8", "ignore"), name)


def parse_any(name: str, raw_bytes: bytes) -> pd.DataFrame:
    n = name.lower()
    if n.endswith(".csv"):
        return parse_csv(name, raw_bytes)
    if n.endswith((".xlsx", ".xls")):
        return parse_excel(name, raw_bytes)
    if n.endswith(".ofx"):
        return parse_ofx(name, raw_bytes)
    if n.endswith((".qbo", ".qfx")):
        return parse_qfx(name, raw_bytes)
    raise ValueError(f"Unsupported file type: {name}")
