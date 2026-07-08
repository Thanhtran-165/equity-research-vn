from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.models import Brand, ScoredPage


_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"


def _format_pages_list(pages: list[ScoredPage], with_evidence: bool = False) -> str:
    lines: list[str] = []
    for i, sp in enumerate(pages, 1):
        url = sp.page.url
        title = sp.page.title or "—"
        score = sp.score.total
        if with_evidence:
            lines.append(
                f"{i}. **URL:** {url}\n"
                f"   - Tên hiển thị: {title}\n"
                f"   - Điểm rủi ro: {score}/100\n"
                f"   - Screenshot: cần chụp thủ công vào lúc truy cập"
            )
        else:
            lines.append(f"{i}. {url} — {title} (score: {score})")
    return "\n".join(lines) if lines else "(không có)"


def render_meta_ip(
    brand: Brand,
    pages: list[ScoredPage],
    signatory_name: str,
    signatory_title: str,
    signatory_email: str,
    today_date: str | None = None,
) -> str:
    today_date = today_date or datetime.now().strftime("%Y-%m-%d")
    template = (_TEMPLATE_DIR / "meta_ip_report.md").read_text(encoding="utf-8")
    return template.format(
        brand=brand,
        infringing_pages_list=_format_pages_list(pages, with_evidence=False),
        signatory_name=signatory_name,
        signatory_title=signatory_title,
        signatory_email=signatory_email,
        today_date=today_date,
    )


def render_shtt(
    brand: Brand,
    pages: list[ScoredPage],
    signatory_name: str,
    signatory_title: str,
    signatory_email: str,
    today_date: str | None = None,
) -> str:
    today_date = today_date or datetime.now().strftime("%Y-%m-%d")
    template = (_TEMPLATE_DIR / "shtt_complaint_vi.md").read_text(encoding="utf-8")
    return template.format(
        brand=brand,
        infringing_pages_list_with_evidence=_format_pages_list(pages, with_evidence=True),
        signatory_name=signatory_name,
        signatory_title=signatory_title,
        signatory_email=signatory_email,
        today_date=today_date,
    )


def render_alert_post(
    brand: Brand,
    pages: list[ScoredPage],
    include_medium: bool = True,
) -> str:
    """Render bài post cảnh báo giả mạo bằng tiếng Việt.
    Mặc định include cả trang MID (tên giống + avatar khác) — set False để chỉ
    liệt kê trang HIGH (avatar trùng)."""
    template = (_TEMPLATE_DIR / "alert_post_vi.md").read_text(encoding="utf-8")
    lines: list[str] = []
    for i, sp in enumerate(pages, 1):
        score_pct = int(sp.score.total / 110 * 100)  # normalize theo max có thể
        signals = []
        if sp.score.name >= 35:
            signals.append("tên trùng")
        if sp.score.avatar >= 25:
            signals.append(f"avatar giống {sp.score.avatar}/35")
        if sp.score.cover >= 12:
            signals.append("ảnh bìa giống")
        reason = ", ".join(signals) if signals else "nghi vấn"
        lines.append(f"{i}. {sp.page.url} — {sp.page.title} ({reason})")
    fake_list = "\n".join(lines) if lines else "(chưa có)"
    return template.format(
        brand=brand,
        fake_pages_list=fake_list,
    )
