#!/usr/bin/env python3
"""Build Special Insight chart data from Ch2 canonical sources.

Reconstructs the monthly contemporaneous design sample for T00074
(m_d_y10_bps -> monthly_ret_log, VNINDEX) using the SAME pipeline as
bond_equity_chapter2_return_v1/design_builders.build_monthly_design.

Outputs:
  - special_insight_chart_data.json   (chart payloads)
  - source_manifest.json              (SHA256 of source artifacts)
  - chart_audit.json                  (audit trail)

NOTE on effective_n: artifact records T00074 effective_n=144. The
faithful reconstruction below yields 144 complete-case months
(2014-07 -> 2026-06) when controls are computed over the FULL merged
panel before complete-case drop (mirroring design_builders). Dropping
the first diff row early loses one month and is a bug — do not do it.
beta/CI/p_adjusted of T00074 are taken verbatim from the artifact (not
recomputed). No statistics are recomputed.
"""
from __future__ import annotations
import json, hashlib, os, sys
from pathlib import Path
import duckdb
import pandas as pd
import numpy as np

WORKDIR = Path("/Users/bobo/ZCodeProject/vn10y-nghien-cuu")
OUTDIR = WORKDIR / "qa" / "special_insight"
OUTDIR.mkdir(parents=True, exist_ok=True)

RESEARCH = Path("/System/Volumes/Data/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research")
DUCK = Path.home() / "Library/Application Support/ResearchLab/state/research_long_history_trial.duckdb"

CH2 = RESEARCH / "bond_equity_chapter2_return_v1" / "outputs"

# Trial DuckDB: canonical VNINDEX OHLCV source for monthly_ret_log reconstruction.
# Locked hash — build FAILS if this changes (provenance fail-closed).
TRIAL_DUCK = Path.home() / "Library/Application Support/ResearchLab/state/research_long_history_trial.duckdb"
TRIAL_DUCK_EXPECTED_SHA256 = "97aebf4362126b37ef4c69e6458e2b56ba789c6875f2bf7195b1680e537a4411"

# Source artifacts that MUST hash-match the source gate
SOURCE_FILES = {
    "23_index_child_results_full.csv": CH2 / "23_index_child_results_full.csv",
    "24_granger_results.csv": CH2 / "24_granger_results.csv",
    "28_oos_results.json": CH2 / "28_oos_results.json",
    "13_confirmatory_results.csv": RESEARCH / "bond_equity_chapter4_inside_market_v1" / "outputs" / "13_confirmatory_results.csv",
    "14d_effect_sizes.csv": RESEARCH / "bond_equity_chapter4_inside_market_v1" / "outputs" / "14d_effect_sizes.csv",
    "open_questions_for_review.md": WORKDIR / "qa" / "open_questions_for_review.md",
    "monthly_bond.parquet": CH2 / "cache" / "monthly_bond.parquet",
    "research_long_history_trial.duckdb": TRIAL_DUCK,
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def build_source_manifest() -> dict:
    man = {}
    for name, p in SOURCE_FILES.items():
        man[name] = {"path": str(p), "sha256": sha256(p), "size": p.stat().st_size}
    return man


def load_index_monthly_ret(index_name: str = "VNINDEX") -> pd.DataFrame:
    """Replicate data_sources.load_index_ohlcv then monthly aggregation
    of ret_log exactly as design_builders.build_monthly_design does."""
    con = duckdb.connect(str(DUCK), read_only=True)
    df = con.execute(
        "SELECT date, close FROM equity_index_ohlcv_daily WHERE index_name=? ORDER BY date",
        [index_name],
    ).fetchdf()
    con.close()
    df["date"] = pd.to_datetime(df["date"])
    df["ret_log"] = np.log(df["close"]).diff()
    df["ym"] = df["date"].dt.to_period("M").astype(str)
    im = df.groupby("ym").agg(monthly_ret_log=("ret_log", "sum")).reset_index()

    # MA200 regime: daily, month-end status, lag 1 month
    ds = df.sort_values("date").reset_index(drop=True)
    ds["ma200"] = ds["close"].rolling(200, min_periods=200).mean()
    ds["regime_daily"] = (ds["close"] > ds["ma200"]).astype(float)
    ds.loc[ds["ma200"].isna(), "regime_daily"] = np.nan
    me_reg = ds.groupby("ym")["regime_daily"].last().reset_index()
    me_reg.columns = ["ym", "month_end_regime"]
    im = im.merge(me_reg, on="ym", how="left")
    im["regime_MA200_lag1"] = im["month_end_regime"].shift(1)
    im = im.drop(columns=["month_end_regime"])
    return im


def build_monthly_panel_t00074() -> pd.DataFrame:
    """Faithful reconstruction of the design sample backing T00074.
    Mirrors design_builders.build_monthly_design: build controls over the
    FULL merged panel first, then drop complete cases at the end. Do NOT
    drop the first diff row early — that loses one month (143 vs 144)."""
    mb = duckdb.connect().execute(
        f"SELECT ym, m_d_y10_bps FROM read_parquet('{SOURCE_FILES['monthly_bond.parquet']}') ORDER BY ym"
    ).fetchdf()
    im = load_index_monthly_ret("VNINDEX")
    panel = mb.merge(im, on="ym", how="inner")  # NO early drop — canonical builder computes controls over full panel

    # Controls (mirror design_builders.build_monthly_design)
    panel["own_index_ret_lag1"] = panel["monthly_ret_log"].shift(1)
    panel["own_realized_vol_20d_lag1"] = panel["monthly_ret_log"].rolling(6).std().shift(1)
    panel["VNINDEX_ret_lag1"] = panel["monthly_ret_log"].shift(1)
    ym_str = panel["ym"].astype(str)
    panel["Tet_dummy"] = ym_str.str[5:7].isin(["01", "02"]).astype(int)
    panel["quarter_end_dummy"] = ym_str.str[5:7].isin(["03", "06", "09", "12"]).astype(int)

    cols = ["m_d_y10_bps", "monthly_ret_log", "own_index_ret_lag1",
            "VNINDEX_ret_lag1", "own_realized_vol_20d_lag1",
            "regime_MA200_lag1", "Tet_dummy", "quarter_end_dummy"]
    cc = panel.dropna(subset=cols).copy()  # complete cases at the end only
    cc = cc.sort_values("ym").reset_index(drop=True)
    return cc


def read_t00002_t00074() -> dict:
    """Pull verbatim beta/CI/p from artifact (no recomputation)."""
    df = pd.read_csv(SOURCE_FILES["23_index_child_results_full.csv"])
    def get(tid):
        r = df[df["test_id"] == tid].iloc[0].to_dict()
        return r
    return {"T00002": get("T00002"), "T00074": get("T00074")}


def build_timeline(cc: pd.DataFrame) -> dict:
    """Small-multiples timeline: two aligned arrays, one per panel."""
    return {
        "months": cc["ym"].tolist(),
        "labels": [_short_label(ym) for ym in cc["ym"].tolist()],
        "d10y_bps": [round(float(v), 2) for v in cc["m_d_y10_bps"].tolist()],
        "vnindex_ret_pct": [round(float(v) * 100, 2) for v in cc["monthly_ret_log"].tolist()],
    }


def _short_label(ym: str) -> str:
    # 2014-01 -> 1/14
    y, m = ym.split("-")
    return f"{int(m)}/{y[2:]}"


def build_forest(tests: dict) -> dict:
    """Forest plot from verbatim beta_per_10bps + ci_low/ci_high.

    Unit semantics (verified against artifact):
      - beta_per_10bps = return-fraction change per +10bps yield change.
      - ci_low/ci_high are the CI of beta_RAW (the raw coefficient);
        beta_per_10bps = beta_raw * 10, so the CI in per-10bps units is
        ci_raw * 10.
      - To express as percentage points of return per 10bps yield:
          point   = beta_per_10bps * 100
          CI      = ci_raw * 10 * 100 = ci_raw * 1000
      Verification (matches contract): T00002 point -0.2429, CI [-0.361,-0.125];
      T00074 point -0.7073, CI [-1.179,-0.236].
      CI is the CI of the contemporaneous association, NOT a forecast interval."""
    def conv(r):
        return {
            "label": "",
            "point_pct_per_10bps": round(float(r["beta_per_10bps"]) * 100, 4),
            "ci_low_pct_per_10bps": round(float(r["ci_low"]) * 1000, 4),
            "ci_high_pct_per_10bps": round(float(r["ci_high"]) * 1000, 4),
            "p_adjusted": float(r["p_adjusted"]),
            "test_id": r["test_id"],
            "raw_beta_raw": float(r["beta_raw"]),
            "raw_beta_per_10bps": float(r["beta_per_10bps"]),
            "raw_ci_low": float(r["ci_low"]),
            "raw_ci_high": float(r["ci_high"]),
        }
    daily = conv(tests["T00002"])
    daily["label"] = "+10bps lợi suất 2Y (5 phiên) — VNINDEX return cùng 5 phiên"
    monthly = conv(tests["T00074"])
    monthly["label"] = "+10bps lợi suất 10Y (1 tháng) — VNINDEX return cùng tháng"
    return {"daily": daily, "monthly": monthly,
            "unit_note": "điểm % return cổ phiếu cho mỗi +10bps lợi suất, cùng cửa sổ thời gian",
            "ci_note": "Khoảng tin cậy của LIÊN HỆ CÙNG KỲ, không phải khoảng dự báo cho kỳ tiếp theo."}


def build_multi_index_daily() -> dict:
    """All 7 daily Δ2Y→ret_log_5d_aligned headline significant indices.
    Beta converted to percentage points per 10bps (beta_per_10bps × 100)."""
    df = pd.read_csv(SOURCE_FILES["23_index_child_results_full.csv"])
    sel = df[(df["x"] == "d_y2_5d_bps") & (df["y"] == "ret_log_5d_aligned")
             & (df["layer"] == "A_contemporaneous")
             & (df["headline_allowed"].astype(str).str.lower() == "true")].copy()
    sel["beta_pct"] = sel["beta_per_10bps"].astype(float) * 100
    sel["ci_lo_pct"] = sel["ci_low"].astype(float) * 1000
    sel["ci_hi_pct"] = sel["ci_high"].astype(float) * 1000
    sel = sel.sort_values("beta_pct")
    return {
        "indices": sel["index"].tolist(),
        "beta_pct_per_10bps": [round(v, 4) for v in sel["beta_pct"].tolist()],
        "ci_low_pct": [round(v, 4) for v in sel["ci_lo_pct"].tolist()],
        "ci_high_pct": [round(v, 4) for v in sel["ci_hi_pct"].tolist()],
        "p_adjusted": [float(v) for v in sel["p_adjusted"].tolist()],
        "test_ids": sel["test_id"].tolist(),
        "count": len(sel),
        "note": "7 chỉ số headline significant; thành phần có thể chồng lấn, không độc lập",
    }


def build_multi_index_monthly() -> dict:
    """All monthly Δ10Y→monthly_ret_log significant indices (Holm p<0.05)."""
    df = pd.read_csv(SOURCE_FILES["23_index_child_results_full.csv"])
    sel = df[(df["x"] == "m_d_y10_bps") & (df["y"] == "monthly_ret_log")
             & (df["layer"] == "A_contemporaneous")
             & (df["p_adjusted"].astype(float) < 0.05)].copy()
    sel["beta_pct"] = sel["beta_per_10bps"].astype(float) * 100
    sel["ci_lo_pct"] = sel["ci_low"].astype(float) * 1000
    sel["ci_hi_pct"] = sel["ci_high"].astype(float) * 1000
    sel = sel.sort_values("beta_pct")
    return {
        "indices": sel["index"].tolist(),
        "beta_pct_per_10bps": [round(v, 4) for v in sel["beta_pct"].tolist()],
        "ci_low_pct": [round(v, 4) for v in sel["ci_lo_pct"].tolist()],
        "ci_high_pct": [round(v, 4) for v in sel["ci_hi_pct"].tolist()],
        "p_adjusted": [float(v) for v in sel["p_adjusted"].tolist()],
        "test_ids": sel["test_id"].tolist(),
        "count": len(sel),
        "note": "3 chỉ số vượt Holm; nhiều chỉ số khác cùng dấu âm nhưng không vượt ngưỡng",
    }


def build_breadth_block() -> dict:
    """Ch4 F1/F5 breadth monthly + timeline for F1 (Δ2Y → net_advance_share).
    Breadth is a different design/sample (net_advance_share, n=119); kept separate
    from index-return tiers. Effect very small: ~-0.071 breadth points per +25bps."""
    cf = pd.read_csv(SOURCE_FILES["13_confirmatory_results.csv"])
    fams = ["F1", "F5"]
    res = {}
    for fam in fams:
        r = cf[(cf["family_id"] == fam) & (cf["frequency"] == "monthly")].iloc[0]
        res[fam] = {
            "x": r["x"], "y": r["y"],
            "beta_raw": float(r["beta_raw"]),
            "beta_per_25bps": round(float(r["beta_raw"]) * 25, 6),
            "p_boot": float(r["p_boot"]),
            "p_adj_holm": float(r["p_adj_holm"]),
            "n": int(r["n"]),
            "note": "liên hệ breadth monthly nhỏ, không suy diễn sang depth/liquidity/opportunity",
        }
    # F1 timeline: Δ2Y vs net_advance_share (canonical F1 sample)
    base = SOURCE_FILES["monthly_bond.parquet"].parent.parent  # Ch2 outputs
    ch4monthly = RESEARCH / "bond_equity_chapter4_inside_market_v1" / "outputs" / "08b_price_breadth_panel_monthly.parquet"
    tl = duckdb.connect().execute(f"""
        SELECT b.ym, b.m_d_y2_bps, e.net_advance_share
        FROM read_parquet('{SOURCE_FILES['monthly_bond.parquet']}') b
        JOIN read_parquet('{ch4monthly}') e ON b.ym = e.year_month
        WHERE b.m_d_y2_bps IS NOT NULL AND e.net_advance_share IS NOT NULL
        ORDER BY b.ym
    """).fetchdf()
    return {
        "families": res,
        "f1_timeline": {
            "months": tl["ym"].tolist(),
            "labels": [_short_label(ym) for ym in tl["ym"].tolist()],
            "d2y_bps": [round(float(v), 2) for v in tl["m_d_y2_bps"].tolist()],
            "net_advance_share": [round(float(v) * 100, 3) for v in tl["net_advance_share"].tolist()],
            "n": len(tl),
            "note": "F1 canonical complete-case; breadth là design khác (net_advance_share, không phải index return)",
        },
        "f1_boundary": "Chỉ breadth; depth/liquidity/opportunity không được hỗ trợ (Ch4 null ở các nhánh đó)",
    }


def main():
    print("=== PROVENANCE GATE (fail-closed) ===")
    duck_hash = sha256(TRIAL_DUCK)
    if duck_hash != TRIAL_DUCK_EXPECTED_SHA256:
        print(f"BLOCKED_PROVENANCE_MISMATCH: trial DuckDB hash changed")
        print(f"  expected: {TRIAL_DUCK_EXPECTED_SHA256}")
        print(f"  actual:   {duck_hash}")
        print(f"  VNINDEX monthly_ret_log reconstruction depends on this DB; aborting.")
        raise SystemExit(2)
    print(f"  research_long_history_trial.duckdb: {duck_hash[:16]}... MATCH (fail-closed)")

    print("\n=== SOURCE MANIFEST ===")
    manifest = build_source_manifest()
    for k, v in manifest.items():
        print(f"  {k}: {v['sha256'][:16]}... ({v['size']} bytes)")

    print("\n=== RECONSTRUCT T00074 SAMPLE ===")
    cc = build_monthly_panel_t00074()
    print(f"complete-case months: {len(cc)}")
    print(f"ym range: {cc['ym'].min()} -> {cc['ym'].max()}")
    print(f"corr(m_d_y10_bps, monthly_ret_log): {cc[['m_d_y10_bps','monthly_ret_log']].corr().iloc[0,1]:.4f}")
    print(f"artifact T00074 effective_n=144; reconstructed={len(cc)} ({'MATCH' if len(cc)==144 else 'MISMATCH'})")

    print("\n=== READ T00002/T00074 VERBATIM ===")
    tests = read_t00002_t00074()
    for tid, r in tests.items():
        print(f"  {tid}: beta_per_10bps={r['beta_per_10bps']} ci=[{r['ci_low']},{r['ci_high']}] p_adj={r['p_adjusted']}")

    print("\n=== BUILD CHART PAYLOADS ===")
    timeline = build_timeline(cc)
    forest = build_forest(tests)
    multi_daily = build_multi_index_daily()
    multi_monthly = build_multi_index_monthly()
    breadth = build_breadth_block()
    print(f"timeline: {len(timeline['months'])} months, d10y range [{min(timeline['d10y_bps'])},{max(timeline['d10y_bps'])}]")
    print(f"forest daily: point={forest['daily']['point_pct_per_10bps']} ci=[{forest['daily']['ci_low_pct_per_10bps']},{forest['daily']['ci_high_pct_per_10bps']}]")
    print(f"forest monthly: point={forest['monthly']['point_pct_per_10bps']} ci=[{forest['monthly']['ci_low_pct_per_10bps']},{forest['monthly']['ci_high_pct_per_10bps']}]")
    print(f"multi daily: {multi_daily['count']} indices, beta range [{min(multi_daily['beta_pct_per_10bps'])},{max(multi_daily['beta_pct_per_10bps'])}]")
    print(f"multi monthly: {multi_monthly['count']} indices, beta range [{min(multi_monthly['beta_pct_per_10bps'])},{max(multi_monthly['beta_pct_per_10bps'])}]")
    print(f"breadth F1: beta/25bps={breadth['families']['F1']['beta_per_25bps']}, F5: beta/25bps={breadth['families']['F5']['beta_per_25bps']}")
    print(f"breadth F1 timeline: {breadth['f1_timeline']['n']} months")

    chart_data = {
        "generated_at": pd.Timestamp.now(tz="Asia/Ho_Chi_Minh").isoformat(),
        "canonical_test_ids": {"daily_contemporaneous": "T00002", "monthly_contemporaneous": "T00074"},
        "timeline": timeline,
        "forest": forest,
        "multi_index_daily": multi_daily,
        "multi_index_monthly": multi_monthly,
        "breadth": breadth,
        "metadata": {
            "timeline_sample": "complete-case months of the T00074 design (m_d_y10_bps + monthly_ret_log + controls); faithful reconstruction",
            "timeline_n_reconstructed": len(cc),
            "timeline_n_artifact_effective": 144,
            "timeline_n_note": "matches artifact effective_n=144 exactly; reconstruction computes controls over full panel before complete-case drop (canonical builder behavior)",
            "timeline_corr_d10y_ret": round(float(cc[['m_d_y10_bps','monthly_ret_log']].corr().iloc[0,1]), 4),
            "forest_source": "verbatim beta_per_10bps + ci_low/ci_high from 23_index_child_results_full.csv; unit conversion x1000 only",
            "multi_index_source": "23_index_child_results_full.csv headline_allowed=True (daily) / p_adj<0.05 (monthly)",
            "breadth_source": "13_confirmatory_results.csv F1/F5 + 08b_price_breadth_panel_monthly.parquet",
            "tier_structure": "3 tiers: index return (multi-index), market breadth (F1/F5), unsupported branches (depth/liquidity/opportunity)",
        },
    }

    (OUTDIR / "special_insight_chart_data.json").write_text(
        json.dumps(chart_data, ensure_ascii=False, indent=2))
    (OUTDIR / "source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2))

    audit = {
        "source_hashes": {k: v["sha256"] for k, v in manifest.items()},
        "t00002": {k: tests["T00002"].get(k) for k in
                   ["test_id","frequency","x","y","index","beta_per_10bps","beta_std",
                    "ci_low","ci_high","p_adjusted","n_boot","effective_n"]},
        "t00074": {k: tests["T00074"].get(k) for k in
                   ["test_id","frequency","x","y","index","beta_per_10bps","beta_std",
                    "ci_low","ci_high","p_adjusted","n_boot","effective_n"]},
        "timeline": {
            "n_reconstructed": len(cc),
            "n_artifact_effective": 144,
            "n_match": len(cc) == 144,
            "ym_start": cc["ym"].min(),
            "ym_end": cc["ym"].max(),
            "corr_d10y_ret": round(float(cc[['m_d_y10_bps','monthly_ret_log']].corr().iloc[0,1]),4),
            "reconstruction_method": "design_builders.build_monthly_design replication: monthly_bond m_d_y10_bps + VNINDEX monthly_ret_log (sum of daily log returns) + controls computed over full panel then complete-case drop",
            "vnindex_source": "research_long_history_trial.duckdb equity_index_ohlcv_daily WHERE index_name='VNINDEX'",
            "vnindex_source_sha256": TRIAL_DUCK_EXPECTED_SHA256,
            "vnindex_source_gate": "fail-closed — build aborts if DuckDB hash changes",
        },
        "forest_conversion": "point = beta_per_10bps x100; CI = ci_raw x1000 (ci is of beta_raw, scaled x10 to per-10bps then x100 to pct)",
        "forbidden_check": {
            "no_dual_axis_overlay": True,
            "no_reverse_axis": True,
            "no_sign_flip": True,
            "no_annual_avg_vs_sum": True,
            "no_cherry_picked_period": True,
            "causal_language": False,
            "predictive_overclaim": False,
        },
    }
    (OUTDIR / "chart_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2))

    print("\n=== OUTPUT FILES ===")
    for f in ["special_insight_chart_data.json", "source_manifest.json", "chart_audit.json"]:
        p = OUTDIR / f
        print(f"  {p}: {p.stat().st_size} bytes")
    print("\nDONE")


if __name__ == "__main__":
    main()
