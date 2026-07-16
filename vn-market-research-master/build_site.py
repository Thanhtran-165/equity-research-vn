#!/usr/bin/env python3
"""Build the governed static research site from canonical editorial Markdown."""
from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EDITORIAL = ROOT / "editorial"
CONTENT = EDITORIAL / "canonical_content"
SITE = ROOT / "site"
QA = ROOT / "qa"
RESEARCH = Path("/Users/bobo/Library/Mobile Documents/com~apple~CloudDocs/main sonet/ResearchLab/research")

SOURCES = {
    "bond_index": RESEARCH / "bond_equity_chapter2_return_v1/outputs/23_index_child_results_full.csv",
    "bond_granger": RESEARCH / "bond_equity_chapter2_return_v1/outputs/24_granger_results.csv",
    "pvb": RESEARCH / "equity_price_volume_breadth_v1/outputs/13_verdicts.json",
    "forecast": RESEARCH / "equity_multivariate_index_forecast_v1/outputs/21_phase1_inference.json",
    "index_divergence": RESEARCH / "equity_divergence_outcomes_v1/outputs/28_claim_evidence_map.json",
    "stock_verdicts": RESEARCH / "equity_stock_volume_divergence_v1/outputs/r6_corrected_verdicts.json",
    "stock_power": RESEARCH / "equity_stock_volume_divergence_v1/outputs/r6_power_analysis.json",
}

EXPECTED_HASHES = {
    "bond_index": "3b708a20931b0fac84b803f21d9ed602e118c73987f11a2e285cb8db3c2900a2",
    "bond_granger": "a342828a3a9f04df8dcd7bdee93419272141a4e4e1a942bddd89ff92c51048ea",
    "pvb": "b56a5e822a51fd3580803a273052c163e55e450440541a1938aded45434a1af2",
    "forecast": "356ab5f9c88f03fd9f06684d40693f8879033d2c64b9fd937c7c9713096e89c9",
    "index_divergence": "1a7f0e79fb4ffb99b3b641c0966bad7c89e32656957a30ffcbcb956206c0390c",
    "stock_verdicts": "53a7a0b904dd0417f8594d5eb54e7962cd71bde7fd0ca7b5c2a38a30b0e26ff2",
    "stock_power": "7a60016ae485129705872901a5c9c0bb2a40b7e4d20b6053ced243c772f89458",
}

CHAPTERS = [
    ("bond", "Bond và cổ phiếu", "A_bond_vn10y.md", "01"),
    ("participation", "Giá, khối lượng, độ rộng", "B_price_volume_breadth.md", "02"),
    ("forecast", "Thử dự báo đa biến", "C_multivariate_forecast.md", "03"),
    ("index-divergence", "Phân kỳ cấp chỉ số", "D_index_divergence.md", "04"),
    ("stock-divergence", "Phân kỳ từng cổ phiếu", "E_stock_divergence.md", "05"),
]

EXTERNAL_REPORTS = {
    "bond": "https://vn10y-nghien-cuu.vercel.app",
    "participation": "https://equity-volume-breadth.vercel.app",
    "forecast": "https://equity-multivariate-forecast.vercel.app",
    "index-divergence": "https://equity-divergence-study.vercel.app",
    "stock-divergence": "https://equity-stock-volume-divergence.vercel.app",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    table = str.maketrans(
        "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ",
        "aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyyd",
    )
    value = value.lower().translate(table)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "section"


def inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(
        r"\[([A-Z][A-Z0-9-]+)\]",
        r'<a class="claim-ref" href="#claim-\1" aria-label="Nguồn claim \1">\1</a>',
        escaped,
    )
    return escaped


def markdown_to_html(markdown: str) -> tuple[str, str, list[tuple[str, str]]]:
    lines = markdown.splitlines()
    title = lines[0][2:].strip() if lines and lines[0].startswith("# ") else "Báo cáo nghiên cứu"
    body: list[str] = []
    toc: list[tuple[str, str]] = []
    paragraph: list[str] = []
    quote: list[str] = []
    list_type: str | None = None
    technical_open = False
    section_open = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            body.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_quote() -> None:
        nonlocal quote
        if quote:
            body.append('<aside class="evidence-boundary">' + "".join(f"<p>{inline(x)}</p>" for x in quote if x) + "</aside>")
            quote = []

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            body.append(f"</{list_type}>")
            list_type = None

    for raw in lines[1:]:
        line = raw.rstrip()
        if line.startswith("## "):
            flush_paragraph(); flush_quote(); close_list()
            if section_open:
                body.append("</section>")
                section_open = False
            heading = line[3:].strip()
            ident = slugify(heading)
            toc.append((ident, heading))
            if heading.startswith("Phụ lục"):
                body.append(f'<details class="technical" id="{ident}"><summary>{html.escape(heading)}</summary><div class="technical-body">')
                technical_open = True
            else:
                body.append(f'<section class="report-section" id="{ident}"><h2>{html.escape(heading)}</h2>')
                section_open = True
        elif line.startswith("### "):
            flush_paragraph(); flush_quote(); close_list()
            heading = line[4:].strip()
            body.append(f'<h3 id="{slugify(heading)}">{html.escape(heading)}</h3>')
        elif line.startswith(">"):
            flush_paragraph(); close_list()
            quote.append(line[1:].strip())
        elif re.match(r"^- ", line):
            flush_paragraph(); flush_quote()
            if list_type != "ul":
                close_list(); body.append("<ul>"); list_type = "ul"
            body.append(f"<li>{inline(line[2:].strip())}</li>")
        elif re.match(r"^\d+\. ", line):
            flush_paragraph(); flush_quote()
            if list_type != "ol":
                close_list(); body.append("<ol>"); list_type = "ol"
            body.append(f"<li>{inline(re.sub(r'^\d+\. ', '', line))}</li>")
        elif not line.strip():
            flush_paragraph(); flush_quote(); close_list()
        elif line.startswith("# "):
            continue
        else:
            paragraph.append(line.strip())

    flush_paragraph(); flush_quote(); close_list()
    if section_open:
        body.append("</section>")
    if technical_open:
        body.append("</div></details>")
    return title, "\n".join(body), toc


def verify_and_extract() -> dict:
    actual = {name: sha(path) for name, path in SOURCES.items()}
    mismatches = {name: {"expected": EXPECTED_HASHES[name], "actual": actual[name]} for name in SOURCES if actual[name] != EXPECTED_HASHES[name]}
    if mismatches:
        raise SystemExit(f"BLOCKED_SOURCE_HASH_MISMATCH: {mismatches}")

    with SOURCES["bond_index"].open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    headline = [r for r in rows if r["frequency"] == "daily" and r["headline_allowed"].lower() == "true"]
    expected_indices = {"VNINDEX", "VN30", "VNCOND", "VNCONS", "VNFIN", "VNHEAL", "VNIT"}
    if len(headline) != 7 or {r["index"] for r in headline} != expected_indices:
        raise SystemExit("BLOCKED_BOND_HEADLINE_SET_MISMATCH")
    bond = []
    for row in sorted(headline, key=lambda x: float(x["beta_per_10bps"])):
        bond.append({
            "test_id": row["test_id"],
            "index": row["index"],
            "effect_pct_per_10bps": round(float(row["beta_per_10bps"]) * 100, 4),
            "ci_low_pct": round(float(row["ci_low"]) * 1000, 4),
            "ci_high_pct": round(float(row["ci_high"]) * 1000, 4),
            "p_adjusted": float(row["p_adjusted"]),
        })

    with SOURCES["bond_granger"].open(newline="", encoding="utf-8") as fh:
        granger = list(csv.DictReader(fh))
    granger_groups = Counter((r["frequency"], r["direction"]) for r in granger)
    granger_survivors = sum(bool(r["p_adjusted"].strip()) and float(r["p_adjusted"]) < 0.05 for r in granger)
    if granger_groups != Counter({("daily", "bond_to_equity"): 75, ("daily", "equity_to_bond"): 75, ("monthly", "bond_to_equity"): 75, ("monthly", "equity_to_bond"): 75}) or granger_survivors != 0:
        raise SystemExit("BLOCKED_GRANGER_COUNT_MISMATCH")

    pvb = json.loads(SOURCES["pvb"].read_text())
    price_to_volume = pvb["verdicts_per_direction"]["M1_price_to_vol_daily"]
    if price_to_volume["n_layer_b_sig"] != 13 or price_to_volume["oos_stable"]:
        raise SystemExit("BLOCKED_PVB_CLAIM_MISMATCH")

    forecast = json.loads(SOURCES["forecast"].read_text())
    forecast_key = "P1_price_volume__VNINDEX__daily__short__H5__direction__confirmatory__P1_vs_P0"
    h5 = forecast["cell_inference"][forecast_key]
    if h5["n_folds_aug_lower"] != 2 or h5["family_denominator"] != 6:
        raise SystemExit("BLOCKED_FORECAST_FOLD_MISMATCH")

    divergence = json.loads(SOURCES["index_divergence"].read_text())
    if not divergence["no_warning_candidate"]["claim"]:
        raise SystemExit("BLOCKED_DIVERGENCE_WARNING_MISMATCH")

    stock = json.loads(SOURCES["stock_verdicts"].read_text())
    stock_counts = Counter(r["verdict"] for r in stock["rows"])
    if stock["descriptive_test_ids"] or stock_counts.get("NOT_SUPPORTED_PARENT_GATE_FAIL", 0) != 4:
        raise SystemExit("BLOCKED_STOCK_VERDICT_MISMATCH")
    power = json.loads(SOURCES["stock_power"].read_text())
    if power["designs"]["power_0.1"]["rate"] != 0.44:
        raise SystemExit("BLOCKED_STOCK_POWER_MISMATCH")

    return {
        "source_hashes": actual,
        "bond": {"headline_indices": bond, "granger_total": len(granger), "granger_survivors": granger_survivors},
        "pvb": {"price_to_volume_in_sample": price_to_volume["n_layer_b_sig"], "oos_stable": price_to_volume["oos_stable"]},
        "forecast": {
            "brier_improvement": round(-h5["mean_d"], 6),
            "adjusted_p": h5["adjusted_p"],
            "folds_better": h5["n_folds_aug_lower"],
            "folds_total": h5["family_denominator"],
            "calibration_slope": h5["calibration"]["calibration_slope"],
            "old_period_share": h5["regime"]["max_contribution_share"],
        },
        "divergence": {"warning_candidates": len(divergence["no_warning_candidate"]["warning_candidate_test_ids"]), "power_binary": 0.355},
        "stock": {"verdict_counts": dict(stock_counts), "descriptive_count": len(stock["descriptive_test_ids"]), "power": power["designs"]["power_0.1"]["rate"]},
    }


def forest_svg(rows: list[dict]) -> str:
    width, height, left, right = 760, 350, 130, 32
    xmin, xmax = -0.55, 0.05
    plot_w = width - left - right
    scale = lambda x: left + (x - xmin) / (xmax - xmin) * plot_w
    parts = [f'<svg class="forest-svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="forest-title forest-desc">',
             '<title id="forest-title">Mức thay đổi cổ phiếu đi cùng 10 điểm cơ bản lợi suất 2 năm</title>',
             '<desc id="forest-desc">Bảy chỉ số đều có ước lượng âm trong cùng khoảng năm phiên. Đây không phải dự báo.</desc>']
    for tick in [-0.5, -0.4, -0.3, -0.2, -0.1, 0]:
        x = scale(tick)
        parts.append(f'<line x1="{x:.1f}" y1="28" x2="{x:.1f}" y2="318" class="grid-line{(" zero" if tick == 0 else "")}"/>')
        parts.append(f'<text x="{x:.1f}" y="342" text-anchor="middle" class="axis-label">{tick:.1f}%</text>')
    for i, row in enumerate(rows):
        y = 52 + i * 38
        lo, hi, value = scale(row["ci_low_pct"]), scale(row["ci_high_pct"]), scale(row["effect_pct_per_10bps"])
        parts.append(f'<text x="8" y="{y+5}" class="row-label">{row["index"]}</text>')
        parts.append(f'<line x1="{lo:.1f}" y1="{y}" x2="{hi:.1f}" y2="{y}" class="ci-line"/>')
        parts.append(f'<line x1="{lo:.1f}" y1="{y-5}" x2="{lo:.1f}" y2="{y+5}" class="ci-cap"/><line x1="{hi:.1f}" y1="{y-5}" x2="{hi:.1f}" y2="{y+5}" class="ci-cap"/>')
        parts.append(f'<circle cx="{value:.1f}" cy="{y}" r="5.5" class="estimate-dot"><title>{row["index"]}: {row["effect_pct_per_10bps"]:.2f}% [{row["ci_low_pct"]:.2f}%; {row["ci_high_pct"]:.2f}%]</title></circle>')
    parts.append("</svg>")
    return "".join(parts)


def visual_master(data: dict) -> str:
    forecast = data["forecast"]
    return f'''
<section class="visual-band" id="bang-chung-truc-quan" aria-labelledby="visual-heading">
  <div class="visual-heading"><p class="eyebrow">Bốn hình để giữ đúng ranh giới</p><h2 id="visual-heading">Quan sát được gì, và chưa được suy ra gì?</h2></div>
  <article class="data-visual forest-panel">
    <div class="visual-copy"><span class="visual-index">01</span><h3>Bond và cổ phiếu đi cùng trong cùng khoảng</h3><p>Bảy chỉ số có ước lượng âm khi lợi suất 2 năm tăng 10 điểm cơ bản. Thành phần chỉ số chồng lấn; đây là quan hệ cùng kỳ.</p></div>
    {forest_svg(data['bond']['headline_indices'])}
    <p class="chart-caption"><strong>Cùng kỳ, không phải dự báo.</strong> Chấm là ước lượng; đường là khoảng ước lượng 95%.</p>
  </article>
  <div class="visual-grid">
    <article class="data-visual state-panel">
      <div class="visual-copy"><span class="visual-index">02</span><h3>Ba lớp dữ liệu trả lời ba câu hỏi</h3><p>Sơ đồ khái niệm, không phải tần suất thực nghiệm.</p></div>
      <div class="state-map" role="img" aria-label="Giá cho biết kết quả, khối lượng cho biết mức hoạt động, độ rộng cho biết mức tham gia">
        <div><b>Giá</b><span>Thị trường đã đi đâu?</span></div><div><b>Khối lượng</b><span>Giao dịch sôi động đến đâu?</span></div><div><b>Độ rộng</b><span>Bao nhiêu cổ phiếu cùng tham gia?</span></div>
      </div>
      <p class="chart-caption">Bất đồng giữa ba lớp là lý do kiểm tra thêm, không phải xác suất đảo chiều.</p>
    </article>
    <article class="data-visual repeat-panel">
      <div class="visual-copy"><span class="visual-index">03</span><h3>Kết quả năm phiên không lặp đều</h3><p>Thêm khối lượng chỉ tốt hơn ở {forecast['folds_better']} trong {forecast['folds_total']} giai đoạn.</p></div>
      <div class="repeat-bar" role="img" aria-label="Hai giai đoạn tốt hơn, bốn giai đoạn không tốt hơn"><span class="better" style="--n:2"></span><span class="not-better" style="--n:4"></span></div>
      <div class="repeat-legend"><span><i class="swatch better"></i>2 tốt hơn</span><span><i class="swatch not-better"></i>4 không tốt hơn</span></div>
      <p class="chart-caption">Điểm tổng hợp cải thiện {forecast['brier_improvement']:.3f}, nhưng phần lớn lợi ích tập trung ở dữ liệu cũ.</p>
    </article>
  </div>
  <article class="data-visual ladder-panel">
    <div class="visual-copy"><span class="visual-index">04</span><h3>Phân kỳ dừng ở bước “kiểm tra thêm”</h3></div>
    <ol class="evidence-ladder"><li class="reached"><b>Quan sát</b><span>Hai lớp dữ liệu bất đồng</span></li><li class="reached"><b>Điều tra</b><span>Đối chiếu sự kiện, ngành, thanh khoản</span></li><li><b>Dự báo ổn định</b><span>Chưa được xác nhận</span></li><li><b>Lệnh giao dịch</b><span>Không được hỗ trợ</span></li></ol>
  </article>
</section>'''


def visual_for_chapter(slug: str, data: dict) -> str:
    if slug == "bond":
        return f'<section class="chapter-visual data-visual"><h2>Bảy chỉ số cùng cho thấy quan hệ âm</h2>{forest_svg(data["bond"]["headline_indices"])}<p class="chart-caption">Mức thay đổi trung bình đi cùng 10 điểm cơ bản lợi suất 2 năm. Không phải khoảng dự báo.</p></section>'
    if slug == "participation":
        return '<section class="chapter-visual data-visual"><h2>Đọc riêng từng lớp trước khi ghép câu chuyện</h2><div class="state-map"><div><b>Giá</b><span>Kết quả</span></div><div><b>Khối lượng</b><span>Mức hoạt động</span></div><div><b>Độ rộng</b><span>Mức tham gia</span></div></div><p class="chart-caption">Đây là sơ đồ giải thích, không biểu diễn xác suất hay thứ tự thực nghiệm.</p></section>'
    if slug == "forecast":
        return '<section class="chapter-visual data-visual"><h2>Hai giai đoạn tốt hơn chưa đủ cho một công cụ</h2><div class="repeat-bar"><span class="better" style="--n:2"></span><span class="not-better" style="--n:4"></span></div><div class="repeat-legend"><span><i class="swatch better"></i>2 tốt hơn</span><span><i class="swatch not-better"></i>4 không tốt hơn</span></div><p class="chart-caption">Kết quả tổng hợp và độ lặp lại phải được đọc cùng nhau.</p></section>'
    if slug in {"index-divergence", "stock-divergence"}:
        last = "Chưa được xác nhận" if slug == "index-divergence" else "Chưa xác nhận; dữ liệu còn giới hạn"
        return f'<section class="chapter-visual data-visual"><h2>Phân kỳ đang đứng ở đâu?</h2><ol class="evidence-ladder"><li class="reached"><b>Quan sát</b><span>Nhận diện bất đồng</span></li><li class="reached"><b>Điều tra</b><span>Kiểm tra thêm dữ liệu</span></li><li><b>Dự báo</b><span>{last}</span></li><li><b>Giao dịch</b><span>Không được hỗ trợ</span></li></ol></section>'
    return ""


def nav(current: str) -> str:
    items = ['<a href="/" class="brand" aria-label="Về báo cáo tổng hợp"><span class="brand-mark">VN</span><span>Nghiên cứu thị trường</span></a>']
    items.append('<nav class="chapter-nav" aria-label="Các chương">')
    items.append(f'<a href="/"{(" class=active" if current == "master" else "")}>Tổng hợp</a>')
    for slug, label, _, number in CHAPTERS:
        items.append(f'<a href="/chapters/{slug}.html"{(" class=active" if current == slug else "")}><span>{number}</span>{html.escape(label)}</a>')
    items.append('</nav><button class="menu-button" type="button" aria-expanded="false" aria-controls="mobile-nav">Mục lục</button>')
    return '<header class="site-header"><div class="header-inner">' + "".join(items) + '</div><div id="mobile-nav" class="mobile-nav" hidden></div></header>'


def toc_html(toc: list[tuple[str, str]]) -> str:
    links = "".join(f'<a href="#{ident}">{html.escape(label)}</a>' for ident, label in toc)
    return f'<aside class="page-toc"><p>Trong chương</p>{links}</aside>'


def source_drawer() -> str:
    return '''<details class="source-drawer"><summary>Phạm vi và nguồn bằng chứng</summary><div><p>Báo cáo tổng hợp năm nghiên cứu đã qua audit. Mỗi kết luận định lượng trỏ về artifact, khóa truy xuất và SHA256 trong registry. HTML không phải nguồn bằng chứng.</p><a href="/data/claim_registry.json">Mở claim registry</a><a href="/data/source_manifest.json">Mở source manifest</a></div></details>'''


def specialist_directory() -> str:
    cards = []
    for slug, label, _, number in CHAPTERS:
        cards.append(
            f'<a class="specialist-card" href="{EXTERNAL_REPORTS[slug]}">'
            f'<span>Chuyên khảo {number}</span><b>{html.escape(label)}</b>'
            '<small>Mở báo cáo độc lập</small></a>'
        )
    return (
        '<section class="specialist-directory" aria-labelledby="specialist-heading">'
        '<div><p class="eyebrow">Thư viện báo cáo con</p>'
        '<h2 id="specialist-heading">Mở chuyên khảo độc lập khi cần xem sâu</h2>'
        '<p>Mỗi báo cáo con giữ URL riêng và dẫn ngược về đúng chương trong master. '
        'Master là bản đọc xuyên suốt; chuyên khảo là lớp bằng chứng chi tiết.</p></div>'
        f'<div class="specialist-grid">{"".join(cards)}</div></section>'
    )


def external_report_link(current: str) -> str:
    if current == "master":
        return ""
    return (
        '<aside class="external-report-link"><span>Bản chuyên khảo độc lập</span>'
        f'<a href="{EXTERNAL_REPORTS[current]}">Mở báo cáo riêng với đầy đủ biểu đồ</a></aside>'
    )


def page_shell(*, title: str, description: str, current: str, body: str, toc: list[tuple[str, str]], chapter_no: str | None = None, visual: str = "") -> str:
    eyebrow = "Báo cáo tổng hợp" if current == "master" else f"Chương {chapter_no} / 05"
    next_link = ""
    if current != "master":
        idx = [x[0] for x in CHAPTERS].index(current)
        if idx < len(CHAPTERS) - 1:
            nslug, nlabel, _, nnum = CHAPTERS[idx + 1]
            next_link = f'<a class="next-chapter" href="/chapters/{nslug}.html"><span>Đọc tiếp · Chương {nnum}</span><b>{html.escape(nlabel)}</b></a>'
        else:
            next_link = '<a class="next-chapter" href="/"><span>Quay lại</span><b>Báo cáo tổng hợp</b></a>'
    return f'''<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{html.escape(description, quote=True)}"><title>{html.escape(title)} · Nghiên cứu thị trường Việt Nam</title><link rel="icon" href="data:,"><link rel="stylesheet" href="/assets/styles.css"><script defer src="/assets/site.js"></script></head>
<body data-page="{current}"><a class="skip-link" href="#content">Bỏ qua điều hướng</a>{nav(current)}
<main id="content"><header class="report-hero"><div class="hero-inner"><p class="eyebrow">{eyebrow}</p><h1>{html.escape(title)}</h1><p class="deck">{html.escape(description)}</p><div class="hero-boundary"><span>Vai trò</span><b>Đọc bối cảnh và mức đồng thuận</b><span>Ranh giới</span><b>Chưa phải tín hiệu giao dịch</b></div></div></header>
{visual if current == 'master' else ''}{specialist_directory() if current == 'master' else ''}
<div class="report-layout">{toc_html(toc)}<article class="report-prose">{external_report_link(current)}{visual if current != 'master' else ''}{body}{source_drawer()}{next_link}</article></div></main>
<footer class="site-footer"><div><b>Nghiên cứu thị trường Việt Nam</b><p>Bối cảnh trước, kết luận sau. Không phải khuyến nghị đầu tư.</p></div><a href="#content">Lên đầu trang</a></footer></body></html>'''


def build_claim_registry(data: dict) -> dict:
    original = json.loads((EDITORIAL / "14_claim_usage_matrix.json").read_text())
    claims = original["claims"]
    corrected_ids = [r["test_id"] for r in data["bond"]["headline_indices"]]
    for claim in claims:
        if claim["claim_id"] == "A-CONTEMPORANEOUS":
            claim["sources"][0]["test_id_or_key"] = ",".join(corrected_ids)
            claim["governance_note"] = "Corrected at site build from headline_allowed=true rows; Session 7 duplicate-ID ledger listed mixed VNINDEX tests."
    return {"claims": claims, "unresolved_claims": [], "html_as_empirical_source": False}


def build() -> None:
    editorial_status = json.loads((EDITORIAL / "19_final_resume_packet.json").read_text())["status"]
    if editorial_status != "PASS_CODEX_LONGFORM_R3_CLOSEOUT":
        raise SystemExit(f"BLOCKED_EDITORIAL_STATUS: {editorial_status}")
    data = verify_and_extract()

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "assets").mkdir(parents=True)
    (SITE / "chapters").mkdir()
    (SITE / "data").mkdir()
    QA.mkdir(exist_ok=True)

    master_md = (CONTENT / "08_master_report_draft.md").read_text()
    master_title, master_body, master_toc = markdown_to_html(master_md)
    master_desc = "Dữ liệu giúp đọc bối cảnh và nhận ra bất đồng. Năm nghiên cứu chưa xác nhận một tín hiệu độc lập, ổn định ngoài mẫu để giao dịch."
    write(SITE / "index.html", page_shell(title=master_title, description=master_desc, current="master", body=master_body, toc=master_toc, visual=visual_master(data)))

    for slug, _, filename, number in CHAPTERS:
        md = (CONTENT / filename).read_text()
        title, body, toc = markdown_to_html(md)
        first_para = next((x.strip() for x in re.split(r"\n\s*\n", md) if x.strip() and not x.startswith("#")), "")
        first_para = re.sub(r"[*`>]", "", first_para)[:280]
        write(SITE / "chapters" / f"{slug}.html", page_shell(title=title, description=first_para, current=slug, body=body, toc=toc, chapter_no=number, visual=visual_for_chapter(slug, data)))

    claim_registry = build_claim_registry(data)
    write(SITE / "data/claim_registry.json", json.dumps(claim_registry, ensure_ascii=False, indent=2, sort_keys=True))
    source_manifest = {"sources": {name: {"artifact": str(SOURCES[name].relative_to(RESEARCH)), "sha256": value} for name, value in data["source_hashes"].items()}, "editorial_status": editorial_status, "statistics_rerun": False}
    write(SITE / "data/source_manifest.json", json.dumps(source_manifest, ensure_ascii=False, indent=2, sort_keys=True))
    write(SITE / "data/report_data.json", json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))

    styles = (ROOT / "web_src/styles.css").read_text()
    script = (ROOT / "web_src/site.js").read_text()
    write(SITE / "assets/styles.css", styles)
    write(SITE / "assets/site.js", script)
    write(SITE / "robots.txt", "User-agent: *\nAllow: /\n")

    files = sorted(p for p in SITE.rglob("*") if p.is_file())
    manifest = {str(p.relative_to(SITE)): sha(p) for p in files}
    write(QA / "build_manifest.json", json.dumps({"files": manifest, "site_file_count": len(files)}, indent=2, sort_keys=True))
    print("PASS_MASTER_RESEARCH_SITE_BUILD")


if __name__ == "__main__":
    build()
