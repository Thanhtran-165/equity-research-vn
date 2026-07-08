from __future__ import annotations

import re
import time
import random
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from src.models import Brand


# Regex: giữ URL profile/page Facebook.
# A.1 FIX: chấp nhận profile.php?id=, /people/Name/pfbid (FB gán cho profile mới).
# Chỉ loại groups/, pages/, watch/, share/, posts/, photos/, videos/ (deep links).
_PAGE_URL_RE = re.compile(
    r"^https?://(?:www\.|m\.|web\.)?facebook\.com/"
    r"(?!groups/|pages/|watch/|share/|sharer|sharer\.php|permalink\.php)"
    r"(profile\.php\?id=\d+"  # profile.php?id=<numeric>
    r"|people/[\w%.\-]+/pfbid[\w]+"  # /people/Name/pfbid<hash>
    r"|[\w.\-]+)"  # /<username>
    r"(?:/?(?:posts|photos|videos|reel|reels|events|shop|live)?/?.*)?$",
    re.IGNORECASE,
)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]


def build_dorks(brand: Brand) -> list[str]:
    """Sinh 5-10 dork queries từ brand info."""
    name = brand.display_name
    primary_alias = brand.aliases[0] if brand.aliases else name
    exclude_official = f"-site:facebook.com/{brand.official_username}"
    # Loại trừ từ khóa dễ gây nhiễu (nội dung về con vật/sản phẩm chung)
    # Chỉ dùng khi brand name có khả năng trùng từ phổ thông
    noise_filter = ""
    lower_name = name.lower()
    common_words = {"chim cút", "chim cut", "chimcút", "chimcut", "thịt", "trứng", "nuôi"}
    if any(w in lower_name for w in common_words):
        noise_filter = '-"nuôi" -"nấu" -"chế biến" -"thức ăn" -"giống"'

    dorks = [
        f'site:facebook.com "{name}" {exclude_official} {noise_filter}'.strip(),
        f'"{name}" site:facebook.com inurl:"{brand.official_username}"',
        f'"{primary_alias}" site:facebook.com "liên hệ" OR "hotline"',
        f'"{name}" site:facebook.com "chính sách" OR "khuyến mãi"',
        f'site:facebook.com "{name}" -"{brand.official_username}" {noise_filter}'.strip(),
    ]
    # Thêm dork cho mỗi alias phụ
    for alias in brand.aliases[1:3]:
        dorks.append(f'"{alias}" site:facebook.com {exclude_official}')
    # Dedup giữ thứ tự
    seen = set()
    out = []
    for d in dorks:
        d = re.sub(r'\s+', ' ', d).strip()  # collapse whitespace
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out[:10]


def extract_fb_page_urls(html: str) -> list[str]:
    """Parse HTML search results, trả về list URL Facebook page (đã normalize)."""
    soup = BeautifulSoup(html, "html.parser")
    raw_urls: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # DDG wrap URL trong /l/?uddg=
        if "uddg=" in href:
            from urllib.parse import parse_qs, unquote
            qs = parse_qs(urlparse(href).query)
            if "uddg" in qs:
                href = unquote(qs["uddg"][0])
        raw_urls.append(href)
    eligible: list[str] = []
    seen_slugs: set[str] = set()
    for url in raw_urls:
        m = _PAGE_URL_RE.match(url)
        if not m:
            continue
        slug = m.group(1)
        if slug.lower() in seen_slugs:
            continue
        seen_slugs.add(slug.lower())
        # Normalize URL (bỏ fragment, bỏ trailing slash)
        normalized = f"https://www.facebook.com/{slug}"
        eligible.append(normalized)
    return eligible


def filter_eligible_urls(urls: list[str], brand: Brand) -> list[str]:
    """Loại URL chính chủ, dedup."""
    official_urls = {
        brand.official_page_url.rstrip("/").lower(),
        f"https://www.facebook.com/{brand.official_username}".lower(),
    }
    out = []
    seen = set()
    for url in urls:
        u = url.rstrip("/").lower()
        if u in official_urls:
            continue
        if u in seen:
            continue
        seen.add(u)
        out.append(url.rstrip("/"))
    return out


def _query_ddg(query: str, timeout: int = 15) -> str:
    """Query DuckDuckGo HTML endpoint."""
    url = "https://html.duckduckgo.com/html/"
    headers = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
    }
    resp = requests.post(url, data={"q": query}, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _query_bing(query: str, timeout: int = 15) -> str:
    """Fallback Bing HTML."""
    url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
    headers = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept-Language": "vi,en-US;q=0.9,en;q=0.8",
    }
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _query_google_playwright(query: str, timeout_ms: int = 25000, headless: bool = False) -> str:
    """Query Google bằng Chromium (Playwright).
    Headed mode (mặc định) tránh bot detection tốt hơn headless."""
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    with sync_playwright() as p:
        launch_args = {
            "headless": headless,
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        browser = p.chromium.launch(**launch_args)
        try:
            context = browser.new_context(
                user_agent=random.choice(_USER_AGENTS),
                locale="vi-VN",
                viewport={"width": 1366, "height": 900},
            )
            # Hide webdriver flag (thêm entropy anti-detect)
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}&hl=vi&num=30"
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            # Click "Tôi đồng ý" cookie consent nếu có (Google EU/VN)
            try:
                page.click("button#L2AGLb", timeout=2000)
                page.wait_for_timeout(500)
            except PWTimeout:
                pass
            # Đợi kết quả hiện
            try:
                page.wait_for_selector("div#search, div#rso", timeout=8000)
            except PWTimeout:
                pass
            page.wait_for_timeout(1500)  # thêm thời gian render JS
            return page.content()
        finally:
            browser.close()


def _dedup_urls(urls: list[str]) -> list[str]:
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _scrape_directory_with_context(context, names_to_search: set[str]) -> list[str]:
    """Scrape /public/ dùng browser context có sẵn (login hoặc ephemeral)."""
    import re
    import sys
    import time

    sys_paths = {
        "login", "reg", "help", "pages", "groups", "watch",
        "home.php", "stories", "bookmarks", "settings",
        "notifications", "events", "marketplace", "gaming",
        "people", "directory", "friends", "find-friends",
        "public", "policy.php", "policies", "about", "ads",
        "plugins", "sharer", "share", "dialog", "tr",
        "unsupportedbrowser", "data", "commerce", "jobs",
        "mobile", "mobile_pro", "l.php",
    }

    all_urls: list[str] = []
    page = context.new_page()
    try:
        for name in names_to_search:
            url = f"https://www.facebook.com/public/{name}"
            try:
                page.goto(url, timeout=25000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)
                for _ in range(3):
                    try:
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(1500)
                    except Exception:
                        page.wait_for_timeout(500)
            except Exception as e:
                print(f"[!] Error fetching {url}: {e}", file=sys.stderr)
                continue

            try:
                html = page.content()
            except Exception:
                page.wait_for_timeout(2000)
                html = page.content()

            urls_found: set[str] = set()
            # Pattern 1: /<slug>
            for m in re.finditer(
                r'facebook\.com/([\w.\-]+)(?=["\'<\s?])', html
            ):
                slug = m.group(1)
                if slug.lower() in sys_paths:
                    continue
                if len(slug) < 3 or slug.startswith("p?"):
                    continue
                urls_found.add(f"https://www.facebook.com/{slug}")

            # Pattern 2: /people/<Name>/pfbid<hash>/ + ?id=<numeric>
            for m in re.finditer(
                r'facebook\.com/(people/[\w%.\-]+/pfbid[\w]+)(?:/?(?:\?id=(\d+))?)?',
                html,
            ):
                people_path = m.group(1)
                profile_id = m.group(2)
                if profile_id:
                    urls_found.add(
                        f"https://www.facebook.com/profile.php?id={profile_id}"
                    )
                else:
                    urls_found.add(f"https://www.facebook.com/{people_path}")

            all_urls.extend(urls_found)
            print(f"[*] /public/{name}: +{len(urls_found)} profiles", file=sys.stderr)
            time.sleep(2)  #礼貌 delay
    finally:
        page.close()

    return all_urls


def _scrape_fb_public_directory(
    brand: Brand,
    headless: bool = False,
    browser_context=None,
) -> list[str]:
    """Scrape https://www.facebook.com/public/<name> bằng Playwright.

    Đây là PHƯƠNG PHÁP CHÍNH để phát hiện profile 'stolen_profile_renamed' —
    kẻ gian giấu username nhưng KHÔNG giấu được display name.
    /public/ index theo display name → trả về mọi profile có tên đó.

    Args:
        browser_context: nếu truyền vào, dùng context này (login sẵn hoặc ephemeral)
                         thay vì tạo browser mới.

    Returns list of profile URLs.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    import re

    # Sinh list tên cần search (display name + aliases, normalized cho URL)
    names_to_search = set()
    for alias in brand.aliases:
        clean = re.sub(r"\s+", "-", alias.strip())
        clean = re.sub(r"[^\w\-]", "", clean)
        if clean:
            names_to_search.add(clean)

    all_urls: list[str] = []

    # Nếu có context truyền vào, dùng context đó
    if browser_context is not None:
        all_urls.extend(_scrape_directory_with_context(browser_context, names_to_search))
        return _dedup_urls(all_urls)

    # Tạo browser riêng (như cũ)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )

    # Sinh list tên cần search (display name + aliases, normalized cho URL)
    names_to_search = set()
    for alias in brand.aliases:
        # /public/ dùng dash thay space
        clean = re.sub(r"\s+", "-", alias.strip())
        clean = re.sub(r"[^\w\-]", "", clean)
        if clean:
            names_to_search.add(clean)

    all_urls: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            context = browser.new_context(
                user_agent=random.choice(_USER_AGENTS),
                locale="vi-VN",
                viewport={"width": 1366, "height": 900},
            )
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = context.new_page()

            for name in names_to_search:
                url = f"https://www.facebook.com/public/{name}"
                try:
                    page.goto(url, timeout=25000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)
                    # Scroll để load thêm — handle navigation race
                    for _ in range(3):
                        try:
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            page.wait_for_timeout(1500)
                        except Exception:
                            page.wait_for_timeout(500)
                except PWTimeout:
                    print(f"[!] Timeout fetching {url}", file=__import__("sys").stderr)
                    continue

                # Parse HTML trực tiếp (tránh evaluate context destroyed)
                try:
                    html = page.content()
                except Exception:
                    page.wait_for_timeout(2000)
                    html = page.content()

                # Regex parse profile links từ HTML — 2 patterns:
                # 1. facebook.com/<username>  (profile có username ready)
                # 2. facebook.com/people/<DisplayName>/pfbid<hash>/  (profile mới,
                #    FB gán veneer URL vì chưa có username)
                sys_paths = {
                    "login", "reg", "help", "pages", "groups", "watch",
                    "home.php", "stories", "bookmarks", "settings",
                    "notifications", "events", "marketplace", "gaming",
                    "people", "directory", "friends", "find-friends",
                    "public", "policy.php", "policies", "about", "ads",
                    "plugins", "sharer", "share", "dialog", "tr",
                    "unsupportedbrowser", "data", "watch", "gaming",
                    "commerce", "jobs", "mobile", "mobile_pro", "l.php",
                }
                urls_found: set[str] = set()

                # Pattern 1: /<slug> (có username)
                for m in re.finditer(
                    r'facebook\.com/([\w.\-]+)(?=["\'<\s?])', html
                ):
                    slug = m.group(1)
                    if slug.lower() in sys_paths:
                        continue
                    if len(slug) < 3 or slug.startswith("p?"):
                        continue
                    urls_found.add(f"https://www.facebook.com/{slug}")

                # Pattern 2: /people/<Name>/pfbid<hash>/  (profile mới chưa có username)
                # Capture full URL đến pfbid, có thể có ?id=<numeric> phía sau
                for m in re.finditer(
                    r'facebook\.com/(people/[\w%.\-]+/pfbid[\w]+)(?:/?(?:\?id=(\d+))?)?',
                    html,
                ):
                    people_path = m.group(1)
                    profile_id = m.group(2)
                    # Prefer profile.php?id= vì đó là canonical, stable URL
                    if profile_id:
                        urls_found.add(
                            f"https://www.facebook.com/profile.php?id={profile_id}"
                        )
                    else:
                        urls_found.add(
                            f"https://www.facebook.com/{people_path}"
                        )

                all_urls.extend(urls_found)
                print(f"[*] /public/{name}: +{len(urls_found)} profiles", file=__import__("sys").stderr)
        finally:
            browser.close()

    # Dedup
    seen = set()
    unique = []
    for u in all_urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def search_pages(
    brand: Brand,
    max_queries: int = 10,
    sleep_range=(2, 5),
    use_playwright: bool = True,
    use_fb_directory: bool = True,
    browser_context=None,
) -> list[str]:
    """Tìm profile/page nghi ngờ. Trả về list URL.

    Discovery methods (theo thứ tự ưu tiên):
    1. FB public directory (/public/<name>) — bắt được stolen_profile_renamed
    2. Search engine dorks (Google/DDG/Bing) — bắt keyword_username pages

    Args:
        browser_context: nếu truyền vào, dùng context chung cho cả 2 methods.
    """
    all_urls: list[str] = []

    # Method 1 (preferred): FB public directory — index theo display name
    if use_fb_directory:
        try:
            print(f"[*] Scraping FB public directory for {brand.display_name}...", file=__import__("sys").stderr)
            dir_urls = _scrape_fb_public_directory(
                brand, headless=False, browser_context=browser_context,
            )
            all_urls.extend(dir_urls)
        except Exception as e:
            print(f"[!] FB directory failed: {e}", file=__import__("sys").stderr)

    # Method 2 (fallback): search engine dorks
    if use_playwright:
        dorks = build_dorks(brand)[:max_queries]
        for i, dork in enumerate(dorks):
            html: str | None = None
            try:
                html = _query_google_playwright(dork)
            except Exception as e:
                print(f"[!] Playwright Google failed: {e}", file=__import__("sys").stderr)
            if not html:
                try:
                    html = _query_ddg(dork)
                except requests.RequestException:
                    try:
                        time.sleep(random.uniform(*sleep_range))
                        html = _query_bing(dork)
                    except requests.RequestException:
                        continue
            if html:
                all_urls.extend(extract_fb_page_urls(html))
            if i < len(dorks) - 1:
                time.sleep(random.uniform(*sleep_range))

    return filter_eligible_urls(all_urls, brand)
