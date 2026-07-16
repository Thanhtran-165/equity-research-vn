from __future__ import annotations

import argparse
import json as _json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src import logging_util
from src.config_loader import AppConfig, ConfigError, load_config
from src.models import RiskBand, ScoredPage, ScanReport
from src.page_meta import fetch_page_meta, list_cached_urls, inspect_cache
from src.report import render_markdown
from src.scoring import score_page, preflight_brand_assets
from src.search import search_pages
from src.takedown_template import render_meta_ip, render_shtt, render_alert_post


_IST = timezone(timedelta(hours=7))

# Exit codes
EXIT_OK = 0
EXIT_CONFIG_ERROR = 2
EXIT_BROWSER_ERROR = 3
EXIT_PARTIAL_FAILURE = 4


def _scan_brand(
    brand, cfg: dict,
    no_network: bool = False,
    urls: list[str] | None = None,
    browser_context=None,
    sleep_between: float = 2.0,
) -> tuple[ScanReport, dict]:
    """Scan 1 brand. Returns (report, stats_dict)."""
    run_at = datetime.now(_IST).strftime("%Y-%m-%dT%H:%M%z")
    report = ScanReport(brand_id=brand.id, run_at=run_at, pages=[])
    stats = {"discovered": 0, "cached": 0, "fetched": 0, "failed": 0, "stale": 0, "skipped_nocache": 0}

    # --no-network mode: đọc URLs từ cache nếu không có urls-file
    if no_network and urls is None:
        urls = list_cached_urls(brand=brand)
        logging_util.info(f"--no-network: loaded {len(urls)} URLs from cache for {brand.display_name}")
        if not urls:
            logging_util.info(f"Cache trống — chạy không --no-network để fetch trước.")
            return report, stats

    if urls is not None:
        stats["discovered"] = len(urls)
        logging_util.info(f"Using {len(urls)} provided URLs for {brand.display_name}")
    else:
        logging_util.info(f"Searching pages for brand: {brand.display_name}")
        urls = search_pages(brand, browser_context=browser_context)
        stats["discovered"] = len(urls)
        logging_util.info(f"Found {len(urls)} candidate URLs")

    scoring_cfg = {**cfg, **brand.scoring_overrides}

    for i, url in enumerate(urls, 1):
        # Check cache trước để skip network (trừ khi cache stale)
        from src.page_meta import _read_cache, _cache_path
        cached_meta = _read_cache(url)
        if cached_meta is not None:
            stats["cached"] += 1
            score = score_page(cached_meta, brand, scoring_cfg)
            report.pages.append(ScoredPage(page=cached_meta, score=score))
            continue

        # Check if cache file exists but is stale
        if _cache_path(url).exists():
            stats["stale"] += 1

        # --no-network: skip fetch cho cache miss (chỉ dùng cached data)
        if no_network:
            stats["skipped_nocache"] += 1
            logging_util.debug(f"--no-network: skipped (no cache): {url}")
            continue

        logging_util.info(f"({i}/{len(urls)}) Fetching {url}")
        try:
            if browser_context is not None:
                from src.page_meta import fetch_page_meta_with_context
                meta = fetch_page_meta_with_context(url, browser_context)
            else:
                meta = fetch_page_meta(url)
            stats["fetched"] += 1
        except Exception as e:
            stats["failed"] += 1
            logging_util.warn(f"Failed to fetch {url}: {e}")
            continue

        # Tag cache entry with brand_id + source (fixes _write_cache not receiving these)
        from src.page_meta import _write_cache
        _write_cache(url, meta, brand_id=brand.id,
                     source="search_bar" if browser_context is not None else "public")

        score = score_page(meta, brand, scoring_cfg)
        report.pages.append(ScoredPage(page=meta, score=score))
        if browser_context is not None and i < len(urls):
            import time
            time.sleep(sleep_between)

    logging_util.info(
        f"Scan done: {stats['cached']} cached + {stats['fetched']} fetched "
        f"+ {stats['skipped_nocache']} skipped = {len(report.pages)} scored"
    )
    return report, stats


def _add_report_counts(stats: dict, report: ScanReport) -> dict:
    """Attach risk-band and semantic-check counts to a scan stats dict."""
    stats["high"] = len(report.iter_by_band(band=RiskBand.HIGH))
    stats["mid"] = len(report.iter_by_band(band=RiskBand.MID))
    stats["low"] = len(report.iter_by_band(band=RiskBand.LOW))
    stats["semantic_check"] = sum(
        1 for scored_page in report.pages if scored_page.score.needs_semantic_check
    )
    return stats


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
        logging_util.warn(f"URL đã có trong known_fakes.yaml — skip")
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
    parser.add_argument("--config", default=str(Path(__file__).parent.parent / "config" / "brands.yaml"))
    parser.add_argument("--brand", help="Brand ID to scan (default: scan all)")
    parser.add_argument("--urls-file", help="File URL list (1/dòng). '# brand_id' để gắn brand.")
    parser.add_argument("--no-network", action="store_true", help="Chỉ dùng cache, không network.")
    parser.add_argument("--clear-cache", action="store_true", help="Xóa cache trước scan.")
    parser.add_argument("--use-chrome-profile", action="store_true",
                        help="Dùng Chrome profile login FB. Yêu cầu Chrome đóng.")
    parser.add_argument("--chrome-profile-dir", default="Default")
    parser.add_argument("--sleep-between", type=float, default=2.0)
    parser.add_argument("--generate-complaints", action="store_true")
    parser.add_argument("--alert", action="store_true", help="Sinh bài post cảnh báo tiếng Việt.")
    parser.add_argument("--alert-include-medium", action="store_true")
    parser.add_argument("--reverse", action="store_true", help="Sinh link reverse image search.")
    parser.add_argument("--learn", help="Thêm URL fake vào known_fakes.yaml.")
    parser.add_argument("--known-fakes", default=str(Path(__file__).parent.parent / "config" / "known_fakes.yaml"))
    parser.add_argument("--signatory-name", default="[YOUR NAME]")
    parser.add_argument("--signatory-title", default="[YOUR TITLE]")
    parser.add_argument("--signatory-email", default="[YOUR EMAIL]")
    parser.add_argument("--verbose", action="store_true", help="Debug-level logging.")
    parser.add_argument("--output-dir", default=".cache/complaints",
                        help="Output dir cho complaints/alert files. Mặc định: .cache/complaints")
    parser.add_argument("--report-json", action="store_true",
                        help="Output JSON report ra stdout (machine-readable).")
    parser.add_argument("--inspect-cache", action="store_true",
                        help="Inspect cache: count, stale, by brand. Không scan.")
    args = parser.parse_args(argv)

    logging_util.set_verbose(args.verbose)

    # === --inspect-cache mode ===
    if args.inspect_cache:
        stats = inspect_cache(brand_id=args.brand)
        print(_json.dumps(stats, indent=2, ensure_ascii=False))
        return EXIT_OK

    # === Config validation (fail-closed) ===
    try:
        config: AppConfig = load_config(Path(args.config))
    except ConfigError as e:
        logging_util.error(f"Config error: {e}")
        return EXIT_CONFIG_ERROR

    brands = [b for b in config.brands if not args.brand or b.id == args.brand]
    if not brands:
        logging_util.error(f"No brand matching '{args.brand}'")
        return EXIT_CONFIG_ERROR

    # === Preflight: check brand assets (fail-closed) ===
    if not args.no_network:
        for brand in brands:
            errors = preflight_brand_assets(brand)
            if errors:
                for err in errors:
                    logging_util.error(f"Preflight [{brand.id}]: {err}")
                logging_util.error(
                    f"Brand assets check failed. Fix above errors or copy avatar/cover "
                    f"to config/avatars/ before scanning."
                )
                return EXIT_CONFIG_ERROR

    # Mode --learn
    if args.learn:
        return _learn_fake(
            url=args.learn, brand=brands[0],
            scoring_cfg=config.scoring, known_fakes_path=args.known_fakes,
        )

    # Load URLs từ file nếu có
    urls_per_brand: dict = {}
    if args.urls_file:
        urls_per_brand = _load_urls_per_brand(args.urls_file, brands)
        logging_util.info(f"Loaded URLs: {', '.join(f'{k}={len(v)}' for k, v in urls_per_brand.items())}")

    # Clear cache nếu --clear-cache
    if args.clear_cache:
        import shutil
        cache_dir = Path(".cache/page_meta")
        if cache_dir.exists():
            count = len(list(cache_dir.glob("*.json")))
            shutil.rmtree(cache_dir)
            logging_util.info(f"Cleared cache: {count} profiles removed")
    else:
        cache_dir = Path(".cache/page_meta")
        if cache_dir.exists():
            stats = inspect_cache()
            logging_util.info(
                f"Cache: {stats['valid']} valid + {stats['stale']} stale "
                f"({stats['total']} total, TTL 7 ngày)"
            )

    # Mở browser context nếu --use-chrome-profile
    browser_context = None
    playwright = None
    if args.use_chrome_profile:
        from src.browser import launch_logged_in_context
        from playwright.sync_api import sync_playwright
        logging_util.warn("--use-chrome-profile: Chrome phải đóng hoàn toàn (Cmd+Q).")
        logging_util.warn("  Profile sẽ được copy sang .cache/chrome_profile/ (không làm hỏng profile thật).")
        playwright = sync_playwright().start()
        try:
            browser_context, _ = launch_logged_in_context(
                playwright, headless=False, profile_dir=args.chrome_profile_dir,
            )
            logging_util.info(f"Using Chrome profile: {args.chrome_profile_dir}")
        except RuntimeError as e:
            logging_util.error(f"Browser/profile error: {e}")
            playwright.stop()
            return EXIT_BROWSER_ERROR

    # === Scan ===
    all_stats: dict = {}
    json_reports: list[dict] = []
    outputs: list[str] = []
    total_failed = 0

    try:
        for brand in brands:
            brand_urls = urls_per_brand.get(brand.id)
            report, brand_stats = _scan_brand(
                brand, config.scoring,
                no_network=args.no_network, urls=brand_urls,
                browser_context=browser_context, sleep_between=args.sleep_between,
            )
            _add_report_counts(brand_stats, report)
            all_stats[brand.id] = brand_stats
            total_failed += brand_stats["failed"]

            outputs.append(render_markdown(report, brand))

            # JSON report
            if args.report_json:
                json_reports.append({
                    "brand_id": brand.id,
                    "run_at": report.run_at,
                    "stats": brand_stats,
                    "pages": [
                        {
                            "url": sp.page.url,
                            "title": sp.page.title,
                            "score": sp.score.total,
                            "band": sp.score.band.name,
                            "avatar": sp.score.avatar,
                            "cover": sp.score.cover,
                            "name": sp.score.name,
                            "needs_semantic_check": sp.score.needs_semantic_check,
                        }
                        for sp in report.pages
                    ],
                })

            # Generate complaints
            if args.generate_complaints:
                high_pages = report.iter_by_band(band=RiskBand.HIGH)
                if high_pages:
                    out_dir = Path(args.output_dir)
                    out_dir.mkdir(parents=True, exist_ok=True)
                    today = datetime.now(_IST).strftime("%Y-%m-%d")
                    meta_md = render_meta_ip(brand=brand, pages=high_pages,
                                             signatory_name=args.signatory_name,
                                             signatory_title=args.signatory_title,
                                             signatory_email=args.signatory_email, today_date=today)
                    shtt_md = render_shtt(brand=brand, pages=high_pages,
                                          signatory_name=args.signatory_name,
                                          signatory_title=args.signatory_title,
                                          signatory_email=args.signatory_email, today_date=today)
                    meta_path = out_dir / f"{today}-{brand.id}-meta.md"
                    shtt_path = out_dir / f"{today}-{brand.id}-shtt.md"
                    meta_path.write_text(meta_md, encoding="utf-8")
                    shtt_path.write_text(shtt_md, encoding="utf-8")
                    outputs.append(f"\n👉 Mẫu đơn khiếu nại: `{meta_path}` và `{shtt_path}`")

            # Alert post
            if args.alert:
                alert_pages = report.iter_by_band(band=RiskBand.HIGH)
                if args.alert_include_medium:
                    alert_pages = alert_pages + report.iter_by_band(band=RiskBand.MID)
                    alert_pages = sorted(alert_pages, key=lambda p: p.score.total, reverse=True)
                if alert_pages:
                    out_dir = Path(args.output_dir)
                    out_dir.mkdir(parents=True, exist_ok=True)
                    today = datetime.now(_IST).strftime("%Y-%m-%d")
                    alert_md = render_alert_post(brand=brand, pages=alert_pages,
                                                 include_medium=args.alert_include_medium)
                    alert_path = out_dir / f"{today}-{brand.id}-alert.md"
                    alert_path.write_text(alert_md, encoding="utf-8")
                    outputs.append(f"\n\n---\n\n📝 **BÀI POST CẢNH BÁO:**\n\n{alert_md}")
                    outputs.append(f"\n👉 File đã lưu: `{alert_path}`")

            # Reverse search
            if args.reverse:
                from src.reverse_search import render_reverse_search_section
                high_pages = report.iter_by_band(band=RiskBand.HIGH)
                page_avatar = None
                for sp in high_pages:
                    if sp.page.avatar_url and sp.page.avatar_url.startswith("http"):
                        page_avatar = sp.page.avatar_url
                        break
                outputs.append("\n\n---\n\n" + render_reverse_search_section(
                    brand_avatar_path=brand.avatar_path, page_avatar_url=page_avatar,
                ))
    finally:
        if browser_context is not None:
            try:
                browser_context.close()
            except Exception:
                pass
        if playwright is not None:
            playwright.stop()

    # === Output ===
    if args.report_json:
        print(_json.dumps(json_reports, indent=2, ensure_ascii=False))
    else:
        print("\n\n".join(outputs))

    # === Summary ===
    logging_util.summary(all_stats)

    # Exit code: partial failure if too many fetches failed
    if total_failed > 0 and total_failed > sum(s.get("fetched", 0) for s in all_stats.values()):
        return EXIT_PARTIAL_FAILURE

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
