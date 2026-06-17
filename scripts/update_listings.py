#!/usr/bin/env python3
"""Update static stock listing CSVs for all 8 markets.

Run from the project root:  python scripts/update_listings.py
Also invoked automatically by GitHub Actions every Monday.
"""
import io
import json
import os
import sys
from datetime import datetime, timedelta

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "resources", "listings")
os.makedirs(OUT, exist_ok=True)


# ---------------------------------------------------------------------------
# Korean markets — FDR GitHub cache
# ---------------------------------------------------------------------------
def _fetch_kr_raw() -> tuple[pd.DataFrame | None, str | None]:
    base = (
        "https://raw.githubusercontent.com/FinanceData/"
        "fdr_krx_data_cache/refs/heads/master/data/listing/krx/"
    )
    for i in range(7):
        d = datetime.today() - timedelta(days=i)
        url = base + d.strftime("%Y-%m-%d") + ".csv"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                df = pd.read_csv(io.StringIO(r.text), dtype={"Code": str})
                return df, d.strftime("%Y-%m-%d")
        except Exception:
            continue
    return None, None


def save_kr_markets() -> str | None:
    df, date_str = _fetch_kr_raw()
    if df is None:
        print("KR: FAILED — no data found in last 7 days", file=sys.stderr)
        return None

    segments = {
        "KOSPI": df[df["Market"] == "KOSPI"],
        "KOSDAQ": df[df["Market"].isin(["KOSDAQ", "KOSDAQ GLOBAL"])],
        "KONEX": df[df["Market"] == "KONEX"],
    }
    for market, sub in segments.items():
        out = sub[["Code", "Name", "Market"]].copy()
        out["Market"] = market
        path = os.path.join(OUT, f"{market}.csv")
        out.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"{market}: {len(out)} stocks ({date_str})")

    return date_str


# ---------------------------------------------------------------------------
# Foreign markets — FinanceDataReader
# ---------------------------------------------------------------------------
def save_foreign_market(market: str) -> bool:
    try:
        import FinanceDataReader as fdr

        df = fdr.StockListing(market)
        df = df.copy()
        if df.index.name:
            df = df.reset_index()

        rename: dict[str, str] = {}
        for col in df.columns:
            cl = col.lower().strip()
            if cl in ("symbol", "ticker", "code") and "Code" not in rename.values():
                rename[col] = "Code"
            elif cl in ("name", "company") and "Name" not in rename.values():
                rename[col] = "Name"
        df = df.rename(columns=rename)

        if "Code" not in df.columns and len(df.columns) >= 1:
            df = df.rename(columns={df.columns[0]: "Code"})
        if "Name" not in df.columns and len(df.columns) >= 2:
            df = df.rename(columns={df.columns[1]: "Name"})

        df["Market"] = market
        out = (
            df[["Code", "Name", "Market"]]
            .dropna(subset=["Code", "Name"])
            .pipe(lambda d: d[d["Code"].astype(str).str.strip() != ""])
            .head(2000)
        )
        path = os.path.join(OUT, f"{market}.csv")
        out.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"{market}: {len(out)} stocks")
        return True
    except Exception as exc:
        print(f"{market}: FAILED — {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    kr_date = save_kr_markets()

    for market in ["NYSE", "NASDAQ", "TSE", "HKEX", "HOSE"]:
        save_foreign_market(market)

    meta = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%d"),
        "kr_data_date": kr_date or "unknown",
    }
    meta_path = os.path.join(OUT, "meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(f"meta.json written: {meta}")


if __name__ == "__main__":
    main()
