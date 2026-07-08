"""Browser session helpers — dùng Chrome profile có sẵn (đã login).

Hỗ trợ 2 cách:
- launch_persistent_context: skill mở Chrome với profile user (yêu cầu Chrome đóng)
- launch ephemeral: tạo context tạm (như cũ)

Lợi ích khi dùng Chrome profile có login FB sẵn:
- Fetch metadata 100% stable (không bị login wall)
- Thấy cover photo (og:image chỉ có avatar)
- Graph search FB đầy đủ hơn /public/
- Thấy activity/recent posts
"""
from __future__ import annotations

import os
from pathlib import Path


# macOS default Chrome profile path
_DEFAULT_CHROME_PROFILE = Path.home() / "Library/Application Support/Google/Chrome"
_DEFAULT_PROFILE_DIR = "Default"


def get_chrome_user_data_dir() -> Path | None:
    """Trả về Chrome user data dir nếu tồn tại."""
    if _DEFAULT_CHROME_PROFILE.exists():
        return _DEFAULT_CHROME_PROFILE
    return None


def is_chrome_running() -> bool:
    """Check Chrome đang chạy không (macOS)."""
    import subprocess
    try:
        result = subprocess.run(
            ["pgrep", "-f", "Google Chrome"],
            capture_output=True, text=True, timeout=2,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


def launch_logged_in_context(
    playwright,
    headless: bool = False,
    profile_dir: str = _DEFAULT_PROFILE_DIR,
    user_data_dir: Path | None = None,
):
    """Mở Chrome với profile có sẵn login.

    Playwright không cho dùng user_data_dir mặc định của Chrome production
    (lỗi 'DevTools remote debugging requires a non-default data directory').
    Nên mình COPY profile sang thư mục tạm trong .cache/chrome_profile/.

    Args:
        playwright: playwright instance
        headless: True để chạy ẩn (không mở window)
        profile_dir: tên profile trong Chrome (Default, Profile 1, ...)
        user_data_dir: override Chrome user data dir

    Returns:
        (browser_context, should_close_browser)

    Raises:
        RuntimeError: nếu Chrome đang chạy (lock profile)
    """
    if is_chrome_running():
        raise RuntimeError(
            "Google Chrome đang chạy. Vui lòng đóng Chrome hoàn toàn "
            "(Cmd+Q) trước khi chạy skill với --use-chrome-profile. "
            "Playwright cần copy profile (cookies, login data) sang location khác."
        )

    src_udd = user_data_dir or get_chrome_user_data_dir()
    if src_udd is None or not src_udd.exists():
        raise RuntimeError(
            f"Chrome user data dir không tồn tại: {src_udd}\n"
            "Cài Chrome hoặc chỉ định path qua --chrome-profile-path"
        )

    src_profile = src_udd / profile_dir
    if not src_profile.exists():
        raise RuntimeError(
            f"Chrome profile không tồn tại: {src_profile}\n"
            f"Các profile có sẵn: {[p.name for p in src_udd.iterdir() if p.is_dir() and (p / 'Cookies').exists()]}"
        )

    # Copy profile sang location tạm (Playwright yêu cầu non-default data dir)
    import shutil
    dest_udd = Path(".cache/chrome_profile").resolve()
    dest_udd.mkdir(parents=True, exist_ok=True)
    dest_profile = dest_udd / "Default"

    # Nếu đã copy rồi, skip (giữ session từ lần trước)
    if not (dest_profile / "Cookies").exists():
        print(f"[*] Copying Chrome profile to {dest_udd}...", file=__import__("sys").stderr)
        # Chỉ copy những file cần thiết (Cookies, Login Data, Preferences, Local State)
        # không copy toàn bộ (lớn quá + có thể conflict)
        # Cách 1: copy toàn bộ Default + Local State — đơn giản, chậm
        # Cách 2: copy selective — nhanh hơn, có thể miss
        # Dùng cách 1 cho chắc
        shutil.copytree(
            src_profile, dest_profile,
            ignore=shutil.ignore_patterns(
                "Cache*", "Code Cache", "GPUCache", "Service Worker",
                "Storage", "IndexedDB", "*.log",
            ),
            dirs_exist_ok=True,
        )
        # Local State ở parent level (cần cho decryption keys)
        local_state_src = src_udd / "Local State"
        if local_state_src.exists():
            shutil.copy2(local_state_src, dest_udd / "Local State")
        print(f"[*] Profile copied (cookies + login data)", file=__import__("sys").stderr)

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=str(dest_udd),
        channel="chrome",
        headless=headless,
        viewport={"width": 1366, "height": 900},
        locale="vi-VN",
        args=["--disable-blink-features=AutomationControlled"],
    )
    context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return context, True


def launch_ephemeral_context(
    playwright,
    headless: bool = False,
):
    """Mở context tạm (không dùng profile Chrome user). Như cũ."""
    browser = playwright.chromium.launch(
        headless=headless,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        locale="vi-VN",
        viewport={"width": 1366, "height": 900},
    )
    context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return context, browser
