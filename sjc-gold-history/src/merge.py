"""Parse raw JSON chunks and merge into a clean master dataset.

Raw chunks live in data/raw/*.json (one per 89-day window). This module
reads all of them, normalizes to a tidy DataFrame, deduplicates, and writes:

  - data/processed/sjc_master.parquet  (canonical, typed)
  - data/processed/sjc_master.csv      (human-readable, VND/lượng)

Schema (one row per price update event):
    timestamp      datetime64[ns, Asia/Ho_Chi_Minh]  — when SJC set the price
    date           date                               — calendar date (UTC+7)
    gold_price_id  int                                — source ID
    branch         str                                — e.g. "Hồ Chí Minh"
    gold_type      str                                — e.g. "Vàng SJC 1L, 10L, 1KG"
    buy_vnd        int64  — buy price, VND per lượng
    sell_vnd       int64  — sell price, VND per lượng
    buy_million    float  — buy in millions (convenience)
    sell_million   float  — sell in millions (convenience)

The natural key for dedup is (gold_price_id, timestamp).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

from .config import GOLD_PRICE_IDS

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

# SJC quotes in Vietnam time (UTC+7). The API epoch is UTC ms; we render to
# Asia/Ho_Chi_Minh so that "08:30 on 15/01/2024" matches the human-facing site.
VN_TZ = timezone(timedelta(hours=7))

# Maps gold_price_id -> (branch, gold_type) for enrichment.
_ID_MAP = {gid: (branch, gtype) for gid, branch, gtype in GOLD_PRICE_IDS}

_EPOCH_RE = re.compile(r"/Date\((-?\d+)\)/")


def _parse_groupdate(s: str) -> datetime:
    """Convert '/Date(1783474364310)/' -> tz-aware datetime in Asia/Ho_Chi_Minh.

    Some points carry DateTime.MinValue ('/Date(-62135596800000)/') when the
    server returns a realtime snapshot without history. Those map to year 0001
    and are dropped upstream; here we just parse faithfully.
    """
    m = _EPOCH_RE.search(s or "")
    if not m:
        return pd.NaT  # type: ignore[return-value]
    epoch_ms = int(m.group(1))
    return datetime.fromtimestamp(epoch_ms / 1000, tz=VN_TZ)


def load_chunk(path: Path) -> pd.DataFrame:
    """Read one raw chunk file into a typed DataFrame."""
    payload = json.loads(path.read_text())
    gpid = payload.get("gold_price_id")
    branch, gtype = _ID_MAP.get(gpid, (None, None))
    rows = []
    for p in payload.get("data", []):
        ts = _parse_groupdate(p.get("GroupDate", ""))
        rows.append({
            "timestamp": ts,
            "gold_price_id": gpid,
            "branch": branch or p.get("BranchName"),
            "gold_type": gtype or p.get("TypeName"),
            "buy_vnd": int(p.get("BuyValue") or 0),
            "sell_vnd": int(p.get("SellValue") or 0),
        })
    return pd.DataFrame(rows)


def build_master(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Concatenate all raw chunks, dedup, sort. Returns the tidy DataFrame."""
    files = sorted(raw_dir.glob("sjc_id*.json"))
    if not files:
        return pd.DataFrame(columns=[
            "timestamp", "gold_price_id", "branch", "gold_type",
            "buy_vnd", "sell_vnd",
        ])
    frames = [load_chunk(f) for f in files]
    df = pd.concat(frames, ignore_index=True)

    # Drop NaT timestamps (DateTime.MinValue snapshot points) and zero-price
    # rows (they appear in some empty responses).
    df = df[df["timestamp"].notna()]
    df = df[(df["buy_vnd"] > 0) | (df["sell_vnd"] > 0)]

    # Sanity floor: SJC 1L has never traded below ~5M VND/lượng in our era
    # (2009+). Sub-5M values are transient feed errors from the source (e.g.
    # a single 2024-07-18 point at 78k). Drop them as corrupted.
    MIN_PLAUSIBLE_VND = 5_000_000
    df = df[(df["buy_vnd"] >= MIN_PLAUSIBLE_VND)
            & (df["sell_vnd"] >= MIN_PLAUSIBLE_VND)]

    # Dedup on the natural key, keeping the last-seen value per merge run.
    df = df.drop_duplicates(
        subset=["gold_price_id", "timestamp"], keep="last"
    )

    df["date"] = df["timestamp"].dt.tz_convert(VN_TZ).dt.date
    df["buy_million"] = (df["buy_vnd"] / 1_000_000).round(3)
    df["sell_million"] = (df["sell_vnd"] / 1_000_000).round(3)

    df = df.sort_values(["gold_price_id", "timestamp"]).reset_index(drop=True)
    return df[
        ["timestamp", "date", "gold_price_id", "branch", "gold_type",
         "buy_vnd", "sell_vnd", "buy_million", "sell_million"]
    ]


def save_master(df: pd.DataFrame, out_dir: Path = PROCESSED_DIR) -> dict:
    """Write parquet + CSV. Returns paths + row counts."""
    out_dir.mkdir(parents=True, exist_ok=True)
    pq = out_dir / "sjc_master.parquet"
    csv = out_dir / "sjc_master.csv"
    df.to_parquet(pq, index=False)
    df.to_csv(csv, index=False)
    return {
        "parquet": str(pq),
        "csv": str(csv),
        "rows": len(df),
        "unique_days": int(df["date"].nunique()) if len(df) else 0,
        "date_min": str(df["timestamp"].min()) if len(df) else None,
        "date_max": str(df["timestamp"].max()) if len(df) else None,
    }


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Merge raw chunks → master dataset.")
    ap.add_argument("--raw-dir", default=str(RAW_DIR))
    ap.add_argument("--out-dir", default=str(PROCESSED_DIR))
    args = ap.parse_args()

    df = build_master(Path(args.raw_dir))
    info = save_master(df, Path(args.out_dir))
    print(f"Master dataset built: {info['rows']:,} rows, "
          f"{info['unique_days']:,} unique days")
    print(f"  Range: {info['date_min']} → {info['date_max']}")
    print(f"  Parquet: {info['parquet']}")
    print(f"  CSV:     {info['csv']}")

    if len(df):
        print("\nPer gold_price_id counts:")
        print(df.groupby(["gold_price_id", "branch", "gold_type"])
              .size().reset_index(name="n").to_string(index=False))


if __name__ == "__main__":
    main()
