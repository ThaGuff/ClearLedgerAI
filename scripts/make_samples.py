"""Generate sample Excel + OFX files into ../samples/."""
from __future__ import annotations
import os
from datetime import datetime, timedelta

import pandas as pd

OUT = os.path.join(os.path.dirname(__file__), "..", "samples")
os.makedirs(OUT, exist_ok=True)

# --- Excel sample ---
rows = []
start = datetime.today() - timedelta(days=90)
payees = ["Salary", "Rent", "Whole Foods", "Amazon", "Netflix", "Uber", "Shell"]
for i in range(90):
    d = start + timedelta(days=i)
    if d.day in (1, 15):
        rows.append({"Date": d, "Amount": 3200, "Payee": "Salary"})
    if d.day == 3:
        rows.append({"Date": d, "Amount": -1850, "Payee": "Rent"})
    if i % 2 == 0:
        rows.append({"Date": d, "Amount": -round(20 + (i % 7) * 13.37, 2),
                     "Payee": payees[(i + 2) % len(payees)]})
df = pd.DataFrame(rows)
df.to_excel(os.path.join(OUT, "sample_transactions.xlsx"), index=False)

# --- OFX sample ---
ofx_header = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRSV1><SONRS><STATUS><CODE>0<SEVERITY>INFO</STATUS>
<DTSERVER>20260101000000<LANGUAGE>ENG</SONRS></SIGNONMSGSRSV1>
<BANKMSGSRSV1><STMTTRNRS><TRNUID>1<STATUS><CODE>0<SEVERITY>INFO</STATUS>
<STMTRS><CURDEF>USD<BANKACCTFROM><BANKID>123<ACCTID>456<ACCTTYPE>CHECKING</BANKACCTFROM>
<BANKTRANLIST><DTSTART>20260101<DTEND>20260401
"""
txns = []
for i, r in enumerate(rows[:30]):
    dt = r["Date"].strftime("%Y%m%d")
    amt = f"{r['Amount']:.2f}"
    typ = "CREDIT" if r["Amount"] > 0 else "DEBIT"
    txns.append(
        f"<STMTTRN><TRNTYPE>{typ}<DTPOSTED>{dt}<TRNAMT>{amt}"
        f"<FITID>{i:08d}<NAME>{r['Payee']}</STMTTRN>"
    )
ofx_footer = """
</BANKTRANLIST><LEDGERBAL><BALAMT>1000.00<DTASOF>20260401</LEDGERBAL>
</STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>
"""
with open(os.path.join(OUT, "sample_statement.ofx"), "w") as f:
    f.write(ofx_header + "\n".join(txns) + ofx_footer)

print(f"Wrote samples to {OUT}")
