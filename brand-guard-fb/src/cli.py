from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.config_loader import AppConfig, load_config
from src.models import RiskBand, ScoredPage, ScanReport
from src.page_meta import fetch_page_meta
from src.report import render_markdown
from src.scoring import score_page
from src.search import search_pages
from src.takedown_template import render_meta_ip, render_shtt, render_alert_post


_IST = timezone(timedelta(hours=7))


def _scan_brand(brand, cfg: dict, no_network: bool = False, urls: list[str] | None = None) -> ScanReport:
    run_at = datetime.now(_IST).strftime("%Y-%m-%dT%H:%M%z")
def _scan_brand(
    brand, cfg: dict,
    no_network: bool = False,
    urls: list[str] | None = None,
    browser_context=None,
    sleep_between: float = 2.0,
) -> ScanReport:
    run_at = datetime.now(_IST).strftime("%Y-%m-%dT%H:%M%z")
    report = ScanReport(brand_id=brand.id, run_at=run_at, pages=[])

    if no_network and urls is None:
        print(f"[*] --no-network: skipping search for {brand.display_name}", file=sys.stderr)
        return report

    if urls is not None:
        print(f"[*] Using {len(urls)} provided URLs for {brand.display_name}", file=sys.stderr)
    else:
        print(f"[*] Searching pages for brand: {brand.display_name}", file=sys.stderr)
        # Pass context to search nếu có (scrape directory dùng context chung)
        urls = search_pages(brand, browser_context=browser_context)
        print(f"[*] Found {len(urls)} candidate URLs", file=sys.stderr)

    scoring_cfg = {**cfg, **brand.scoring_overrides}

    for i, url in enumerate(urls, 1):
        print(f"[*] ({i}/{len(urls)}) Fetching {url}", file=sys.stderr)
        try:
            if browser_context is not None:
                from src.page_meta import fetch_page_meta_with_context
                meta = fetch_page_meta_with_context(url, browser_context)
            else:
                meta = fetch_page_meta(url)
        except Exception as e:
            print(f"[!] Failed to fetch {url}: {e}", file=sys.stderr)
            continue
        score = score_page(meta, brand, scoring_cfg)
        report.pages.append(ScoredPage(page=meta, score=score))
        if browser_context is not None and i < len(urls):
            import time
            time.sleep(sleep_between)

    return report


def _load_urls_per_brand(urls_file: str, brands: list) -> dict:
    """Đọc file URL theo format:
        # chim_cut       (gắn URL sau cho brand_id này — 1 từ duy nhất sau #)
        https://...
        # Đây là comment giải thích (nhiều từ sau # → bị ignore)
        https://...
       Hoặc nếu không có # marker, gán cho brand đầu tiên.
    """
    from src.search import filter_eligible_urls
    out: dict[str, list[str]] = {}
    brand_ids = {b.id for b in brands}
    current_brand_id = brands[0].id if brands else None
    out.setdefault(current_brand_id, [])
    with open(urls_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                # Chỉ coi là brand marker nếu là 1 từ duy nhất VÀ match brand_id
                marker = line[1:].strip()
                if marker in brand_ids:
                    current_brand_id = marker
                    out.setdefault(current_brand_id, [])
                # Ngược lại: comment, ignore
                continue
            if line.startswith("//"):
                continue
            out.setdefault(current_brand_id, []).append(line)
    # Lọc official URLs cho mỗi brand
    brand_map = {b.id: b for b in brands}
    for bid, urls in out.items():
        if bid in brand_map:
            out[bid] = filter_eligible_urls(urls, brand_map[bid])
    return out


def _load_known_fakes(path: str) -> dict:
    """Load pattern DB known_fakes.yaml. Trả về dict rỗng nếu file không tồn tại."""
    import yaml as _yaml
    p = Path(path)
    if not p.exists():
        return {"fakes": [], "patterns": []}
    try:
        with p.open("r", encoding="utf-8") as f:
            return _yaml.safe_load(f) or {"fakes": [], "patterns": []}
    except Exception:
        return {"fakes": [], "patterns": []}


def _learn_fake(url: str, brand, scoring_cfg: dict, known_fakes_path: str) -> int:
    """Fetch profile giả mạo mới, học pattern, thêm vào known_fakes.yaml."""
    import yaml as _yaml
    from src.scoring import _phash_distance

    print(f"[*] Learning new fake: {url}", file=sys.stderr)
    meta = fetch_page_meta(url)
    score = score_page(meta, brand, scoring_cfg)

    # Compute pHash của avatar trang giả (nếu có local path)
    avatar_phash = ""
    if meta.avatar_url and not meta.avatar_url.startswith("http"):
        h = _phash_distance(meta.avatar_url)
        if h is not None:
            avatar_phash = str(h)

    # Detect pattern: username không chứa keyword brand
    from urllib.parse import urlparse
    slug = urlparse(url).path.strip("/").split("/")[0].lower()
    brand_keywords = [a.lower() for a in brand.aliases] + [brand.official_username.lower()]
    username_has_keyword = any(k in slug for k in brand_keywords)
    pattern = "stolen_profile_renamed" if not username_has_keyword else "keyword_username"

    # Load existing fakes
    known = _load_known_fakes(known_fakes_path)
    existing_urls = {f.get("url") for f in known.get("fakes", [])}
    if url in existing_urls:
        print(f"[!] URL đã có trong known_fakes.yaml — skip", file=sys.stderr)
        return 0

    # Tạo entry mới
    import re
    # Username pattern: giữ phần đầu trước số, regex match
    username_parts = re.split(r"[.\-_\d]", slug)
    username_regex = ".".join(p for p in username_parts[:3] if p) + ".*" if username_parts else slug

    new_entry = {
        "url": url,
        "added_at": datetime.now(_IST).strftime("%Y-%m-%d"),
        "pattern": pattern,
        "username_pattern": f"^{username_regex}",
        "title": meta.title,
        "avatar_phash": avatar_phash,
        "score": score.total,
        "notes": f"Added via --learn. Title={meta.title!r}, score={score.total}.",
    }

    known.setdefault("fakes", []).append(new_entry)

    # Đảm bảo pattern signature tồn tại
    patterns = known.setdefault("patterns", [])
    pattern_ids = {p.get("id") for p in patterns}
    if pattern == "stolen_profile_renamed" and pattern not in pattern_ids:
        patterns.append({
            "id": "stolen_profile_renamed",
            "description": "Kẻ gian lấy profile FB có sẵn (username nước ngoài), đổi tên + avatar thành brand. Search dork không bắt được.",
            "signals": [
                "title match brand name (≥80%)",
                "avatar pHash match brand avatar (Hamming ≤ 8)",
                "username KHÔNG chứa keyword brand",
            ],
            "detection_method": "reverse_image_search + user_report",
        })

    # Write lại file
    out_path = Path(known_fakes_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        _yaml.safe_dump(known, f, allow_unicode=True, sort_keys=False)

    print(f"[+] Added to {known_fakes_path}:", file=sys.stderr)
    print(f"    pattern: {pattern}", file=sys.stderr)
    print(f"    title: {meta.title!r}", file=sys.stderr)
    print(f"    avatar_phash: {avatar_phash!r}", file=sys.stderr)
    print(f"    score: {score.total}", file=sys.stderr)

    # In reverse search section để user verify
    from src.reverse_search import render_reverse_search_section
    print("\n" + render_reverse_search_section(
        brand_avatar_path=brand.avatar_path,
        page_avatar_url=meta.avatar_url if meta.avatar_url.startswith("http") else None,
    ))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="brand-guard-fb")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent.parent / "config" / "brands.yaml"),
        help="Path to brands.yaml",
    )
    parser.add_argument(
        "--brand",
        help="Brand ID to scan (default: scan all brands in config)",
    )
    parser.add_argument(
        "--urls-file",
        help="File chứa list URL Facebook (1 URL/dòng) để scan thay vì search engine. Dùng '# brand_id' để gắn URL cho brand cụ thể.",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Skip network calls, only use cached page metadata",
    )
    parser.add_argument(
        "--use-chrome-profile",
        action="store_true",
        help="Dùng Chrome profile có sẵn session login FB. Yêu cầu Chrome đã đóng. "
             "Cho phép fetch đầy đủ metadata (cover, activity) + tránh login wall.",
    )
    parser.add_argument(
        "--chrome-profile-dir",
        default="Default",
        help="Chrome profile dir name (Default, Profile 1, ...). Mặc định: Default",
    )
    parser.add_argument(
        "--sleep-between",
        type=float,
        default=2.0,
        help="Sleep giữa các fetch khi dùng --use-chrome-profile (giảm rate limit). Mặc định: 2.0s",
    )
    parser.add_argument(
        "--generate-complaints",
        action="store_true",
        help="Generate takedown complaint templates for high-risk pages",
    )
    parser.add_argument(
        "--alert",
        action="store_true",
        help="Sinh bài post cảnh báo giả mạo (tiếng Việt) để đăng lên fanpage chính chủ",
    )
    parser.add_argument(
        "--alert-include-medium",
        action="store_true",
        help="Bao gồm cả trang MID (tên giống nhưng avatar khác) trong bài cảnh báo",
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Sinh link reverse image search (Google Lens/TinEye/Yandex) cho avatar brand và avatar các trang HIGH. Dùng để phát hiện profile 'có sẵn đổi tên+avatar'.",
    )
    parser.add_argument(
        "--learn",
        help="Thêm URL profile giả mạo mới vào known_fakes.yaml (pattern DB). VD: --learn https://facebook.com/some.profile",
    )
    parser.add_argument(
        "--known-fakes",
        default=str(Path(__file__).parent.parent / "config" / "known_fakes.yaml"),
        help="Path tới file pattern DB known_fakes.yaml",
    )
    parser.add_argument(
        "--signatory-name", default="[YOUR NAME]",
    )
    parser.add_argument(
        "--signatory-title", default="[YOUR TITLE]",
    )
    parser.add_argument(
        "--signatory-email", default="[YOUR EMAIL]",
    )
    args = parser.parse_args(argv)

    config: AppConfig = load_config(Path(args.config))
    brands = [b for b in config.brands if not args.brand or b.id == args.brand]
    if not brands:
        print(f"[!] No brand matching '{args.brand}'", file=sys.stderr)
        return 2

    # Mode --learn: thêm profile giả mạo mới vào pattern DB
    if args.learn:
        return _learn_fake(
            url=args.learn,
            brand=brands[0],
            scoring_cfg=config.scoring,
            known_fakes_path=args.known_fakes,
        )

    # Load URLs từ file nếu có
    urls_per_brand: dict = {}
    if args.urls_file:
        urls_per_brand = _load_urls_per_brand(args.urls_file, brands)
        print(f"[*] Loaded URLs from {args.urls_file}: "
              f"{', '.join(f'{k}={len(v)}' for k, v in urls_per_brand.items())}",
              file=sys.stderr)

    # Load known_fakes.yaml để skip URLs đã biết + học pattern
    known_fakes = _load_known_fakes(args.known_fakes)

    # Mở browser context nếu --use-chrome-profile
    browser_context = None
    browser_to_close = None
    if args.use_chrome_profile:
        from src.browser import launch_logged_in_context
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        try:
            browser_context, _ = launch_logged_in_context(
                pw,
                headless=False,
                profile_dir=args.chrome_profile_dir,
            )
            print(f"[*] Using Chrome profile: {args.chrome_profile_dir}", file=sys.stderr)
            print(f"[*] Đã đăng nhập FB? Vào https://facebook.com để verify.", file=sys.stderr)
        except RuntimeError as e:
            print(f"[!] {e}", file=sys.stderr)
            pw.stop()
            return 3

    outputs: list[str] = []
    try:
        for brand in brands:
            brand_urls = urls_per_brand.get(brand.id)
            report = _scan_brand(
                brand, config.scoring,
                no_network=args.no_network,
                urls=brand_urls,
                browser_context=browser_context,
                sleep_between=args.sleep_between,
            )
        outputs.append(render_markdown(report, brand))

        if args.generate_complaints:
            high_pages = report.iter_by_band(band=RiskBand.HIGH)
            if high_pages:
                out_dir = Path(".cache/complaints")
                out_dir.mkdir(parents=True, exist_ok=True)
                today = datetime.now(_IST).strftime("%Y-%m-%d")
                meta_md = render_meta_ip(
                    brand=brand,
                    pages=high_pages,
                    signatory_name=args.signatory_name,
                    signatory_title=args.signatory_title,
                    signatory_email=args.signatory_email,
                    today_date=today,
                )
                shtt_md = render_shtt(
                    brand=brand,
                    pages=high_pages,
                    signatory_name=args.signatory_name,
                    signatory_title=args.signatory_title,
                    signatory_email=args.signatory_email,
                    today_date=today,
                )
                meta_path = out_dir / f"{today}-{brand.id}-meta.md"
                shtt_path = out_dir / f"{today}-{brand.id}-shtt.md"
                meta_path.write_text(meta_md, encoding="utf-8")
                shtt_path.write_text(shtt_md, encoding="utf-8")
                outputs.append(
                    f"\n👉 Mẫu đơn khiếu nại: `{meta_path}` và `{shtt_path}`"
                )

        if args.alert:
            alert_pages = report.iter_by_band(band=RiskBand.HIGH)
            if args.alert_include_medium:
                alert_pages = alert_pages + report.iter_by_band(band=RiskBand.MID)
                # Re-sort by score desc
                alert_pages = sorted(alert_pages, key=lambda p: p.score.total, reverse=True)
            if alert_pages:
                out_dir = Path(".cache/complaints")
                out_dir.mkdir(parents=True, exist_ok=True)
                today = datetime.now(_IST).strftime("%Y-%m-%d")
                alert_md = render_alert_post(
                    brand=brand,
                    pages=alert_pages,
                    include_medium=args.alert_include_medium,
                )
                alert_path = out_dir / f"{today}-{brand.id}-alert.md"
                alert_path.write_text(alert_md, encoding="utf-8")
                # In ngay ra stdout để user copy paste
                outputs.append(f"\n\n---\n\n📝 **BÀI POST CẢNH BÁO (copy đăng lên fanpage):**\n\n{alert_md}")
                outputs.append(f"\n👉 File đã lưu: `{alert_path}`")

        if args.reverse:
            from src.reverse_search import render_reverse_search_section
            high_pages = report.iter_by_band(band=RiskBand.HIGH)
            # Dùng avatar của trang HIGH đầu tiên (nếu có)
            page_avatar = None
            for sp in high_pages:
                if sp.page.avatar_url and sp.page.avatar_url.startswith("http"):
                    page_avatar = sp.page.avatar_url
                    break
            outputs.append("\n\n---\n\n" + render_reverse_search_section(
                brand_avatar_path=brand.avatar_path,
                page_avatar_url=page_avatar,
            ))
    finally:
        # Đóng browser context nếu có
        if browser_context is not None:
            try:
                browser_context.close()
            except Exception:
                pass
        if browser_to_close is not None:
            browser_to_close.close()

    print("\n\n".join(outputs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
