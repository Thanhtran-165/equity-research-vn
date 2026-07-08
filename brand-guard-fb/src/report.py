from __future__ import annotations

from src.models import Brand, RiskBand, ScanReport

_BAND_VI = {RiskBand.HIGH: "🔴 Cao rủi ro", RiskBand.MID: "🟡 Trung", RiskBand.LOW: "🟢 Thấp"}


def _table_header() -> str:
    return (
        "| # | Page | Tên hiển thị | Score | Tên (15) | Avatar (50) | "
        "Cover (30) | Mới (3) | URL (2) |\n"
        "|---|------|--------------|-------|----------|-------------|"
        "------------|---------|---------|"
    )


def _row(idx: int, page_url: str, title: str, s) -> str:
    short_slug = page_url.replace("https://www.facebook.com/", "")
    flag = " ⚠️" if s.needs_semantic_check else ""
    return (
        f"| {idx} | [{short_slug}]({page_url}) | {title or '—'} | "
        f"**{s.total}**{flag} | {s.name} | {s.avatar} | {s.cover} | {s.recency} | {s.url} |"
    )


def render_markdown(report: ScanReport, brand: Brand) -> str:
    lines: list[str] = []
    lines.append("# 🔍 Brand Guard — Facebook Fake Page Scan")
    lines.append("")
    lines.append(f"**Run at:** {report.run_at}  **Brand:** {brand.display_name}  "
                 f"**Pages scanned:** {len(report.pages)}")
    lines.append("")

    if not report.pages:
        lines.append("✅ Không tìm thấy trang nghi vấn cho thương hiệu này.")
        return "\n".join(lines)

    for band in (RiskBand.HIGH, RiskBand.MID, RiskBand.LOW):
        items = report.iter_by_band(band=band)
        if not items:
            continue
        label = _BAND_VI[band]
        lines.append(f"## {label} ({len(items)})")
        lines.append("")
        lines.append(_table_header())
        for i, sp in enumerate(items, 1):
            lines.append(_row(i, sp.page.url, sp.page.title, sp.score))
        lines.append("")

    # Warning cho profiles cần semantic check (pHash miss, có thể edit nhẹ)
    semantic_flagged = [sp for sp in report.pages if sp.score.needs_semantic_check]
    if semantic_flagged:
        lines.append("---")
        lines.append("")
        lines.append(f"## ⚠️ {len(semantic_flagged)} profile cần semantic check")
        lines.append("")
        lines.append("pHash miss (avatar/cover khác nhiều) nhưng tên match — có thể bị edit nhẹ.")
        lines.append("**Agent workflow:** gọi `analyze_image` MCP cho từng URL:")
        lines.append("")
        for sp in semantic_flagged:
            av = sp.page.avatar_url if sp.page.avatar_url.startswith("http") else "(local cache)"
            lines.append(f"- `{sp.page.url}`")
            lines.append(f"  - avatar: {av[:100]}")
        lines.append("")
        lines.append("Prompt template cho analyze_image:")
        lines.append('```')
        lines.append('analyze_image(imageSource=<suspect_avatar_url>,')
        lines.append('  prompt="Avatar này có giống [mô tả brand avatar] không? Đánh giá: identical/similar/different")')
        lines.append('```')

    lines.append("---")
    lines.append("")
    lines.append(
        "**Lưu ý pháp lý:** Kết quả chỉ là gợi ý dựa trên heuristic. "
        "Trước khi gửi khiếu nại, hãy review lại bằng chứng và xác nhận với pháp chế. "
        "Không tự liên hệ/xâm phạm trang nghi vấn."
    )
    return "\n".join(lines)
