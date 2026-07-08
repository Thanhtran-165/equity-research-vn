"""Reverse image search helpers.

Phát hiện profile 'có sẵn đổi tên + avatar' — pattern mà search engine dork
KHÔNG bắt được vì username gốc không chứa keyword brand.

Cách dùng:
- self.build_search_urls(avatar_path) → trả về dict URL cho Google Lens / TinEye / Yandex
- User click → browser mở với kết quả các trang khác dùng cùng avatar
- Nếu thấy trang FB khác → đó là profile giả mạo (avatar stolen)
"""
from __future__ import annotations

import base64
import urllib.parse
from pathlib import Path


def build_search_urls(image_source: str) -> dict[str, str]:
    """Tạo URL reverse image search cho Google Lens / TinEye / Yandex.

    Args:
        image_source: có thể là URL http(s):// HOẶC local path.

    Returns:
        Dict {'google_lens': ..., 'tineye': ..., 'yandex': ...}
        Nếu local path → Google Lens/Yandex không accept URL, user phải upload tay.
    """
    is_url = image_source.startswith(("http://", "https://"))
    encoded = urllib.parse.quote(image_source, safe="")

    urls: dict[str, str] = {}

    if is_url:
        urls["google_lens"] = f"https://lens.google.com/uploadbyurl?url={encoded}"
        urls["tineye"] = f"https://tineye.com/search/?url={encoded}"
        urls["yandex"] = (
            "https://yandex.com/images/search?rpt=imageview&url="
            + encoded
        )
    else:
        # Local file — Google Lens / Yandex cần upload thủ công
        urls["google_lens"] = "https://lens.google.com/uploadpoint"
        urls["tineye"] = "https://tineye.com"
        urls["yandex"] = "https://yandex.com/images"
        urls["_local_path"] = image_source
        urls["_note"] = (
            "Ảnh local — mở link trên rồi drag-drop file "
            f"`{image_source}` vào browser để search"
        )

    return urls


def render_reverse_search_section(
    brand_avatar_path: str,
    page_avatar_url: str | None = None,
) -> str:
    """Render markdown section với các link reverse search.

    Tạo 2 nhóm link:
    1. Search avatar CHÍNH CHỦ → tìm tất cả trang stolen
    2. Search avatar TRANG NGHI VẤN (nếu có) → verify chúng dùng chung nguồn
    """
    lines: list[str] = []
    lines.append("## 🔎 Reverse Image Search — phát hiện profile đổi-avatar")
    lines.append("")
    lines.append(
        "Pattern này dùng khi kẻ gian lấy profile có sẵn (username không liên quan) "
        "rồi đổi tên + avatar. Search engine không bắt được — phải dùng image search."
    )
    lines.append("")

    # Group 1: avatar chính chủ
    lines.append("### Tìm tất cả trang dùng avatar của Chim Cút")
    lines.append("")
    brand_urls = build_search_urls(brand_avatar_path)
    if "_local_path" in brand_urls:
        lines.append(f"📷 Ảnh avatar chính chủ: `{brand_avatar_path}`")
        lines.append("")
        lines.append(f"- **Google Lens**: {brand_urls['google_lens']} — drag-drop ảnh vào")
        lines.append(f"- **TinEye**: {brand_urls['tineye']} — upload ảnh")
        lines.append(f"- **Yandex**: {brand_urls['yandex']} — upload ảnh (often finds more)")
    else:
        lines.append(f"- **Google Lens**: {brand_urls['google_lens']}")
        lines.append(f"- **TinEye**: {brand_urls['tineye']}")
        lines.append(f"- **Yandex**: {brand_urls['yandex']}")
    lines.append("")

    # Group 2: avatar trang nghi vấn (nếu có)
    if page_avatar_url:
        lines.append("### Verify trang nghi vấn dùng avatar stolen")
        lines.append("")
        page_urls = build_search_urls(page_avatar_url)
        if "_local_path" not in page_urls:
            lines.append(f"- **Google Lens**: {page_urls['google_lens']}")
            lines.append(f"- **TinEye**: {page_urls['tineye']}")
            lines.append(f"- **Yandex**: {page_urls['yandex']}")
            lines.append("")
            lines.append(
                "Nếu cả 3 search đều trả về fanpage chính chủ `chimcutvnindex` "
                "hoặc các profile khác cùng avatar → chắc chắn stolen."
            )

    lines.append("")
    lines.append(
        "💡 **Tip:** Yandex thường index ảnh FB tốt hơn Google. "
        "Thử Yandex trước nếu Google Lens không ra kết quả."
    )
    return "\n".join(lines)


def open_in_browser(url: str) -> None:
    """Mở URL trong browser mặc định (macOS)."""
    import subprocess
    import sys

    if sys.platform == "darwin":
        subprocess.run(["open", url], check=False)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", url], check=False)
    else:
        print(f"Open manually: {url}")
