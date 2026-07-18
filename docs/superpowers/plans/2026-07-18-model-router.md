# model-router Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a ZCode plugin `model-router` that lets users route tasks to GLM, DeepSeek, or Kimi via the `/mr` command, with user-managed config (API keys never committed to git).

**Architecture:** Python stdlib-only scripts invoked by a ZCode command. A single `/mr` entrypoint dispatches to `setup`, `list`, or `<provider> "<task>"` subcommands. Config lives at `~/.zcode/model-router/config.json` (chmod 600, gitignored). HTTP calls use Anthropic Messages API format to each provider's Anthropic-compatible endpoint.

**Tech Stack:** Python 3.14 stdlib only (`urllib.request`, `json`, `argparse`, `getpass`, `os`, `sys`, `time`, `pathlib`), pytest for tests, ZCode plugin format (plugin.json + commands/*.md).

**Reference spec:** `docs/superpowers/specs/2026-07-18-model-router-design.md`

**Plugin install path:** `~/.zcode/plugins/model-router/` (so ZCode auto-discovers it)
**Repo path:** `/Users/bobo/ZCodeProject/model-router/` (git repo pushed to `git@github.com:Thanhtran-165/model-router.git`)

---

## File Structure

```
/Users/bobo/ZCodeProject/model-router/           ← git repo (NO keys)
├── plugin.json                                   ← plugin metadata
├── README.md                                     ← install + usage guide
├── .gitignore                                    ← exclude config.json
├── config.example.json                           ← template (committed, no keys)
├── commands/
│   └── mr.md                                     ← /mr command prompt for ZCode
├── src/
│   └── model_router/
│       ├── __init__.py
│       ├── config.py                             ← load/save config, paths
│       ├── providers.py                          ← provider registry (3 default)
│       ├── http_client.py                        ← Anthropic-compat HTTP call
│       ├── errors.py                             ← typed errors + HTTP code mapping
│       ├── router.py                             ← CLI entrypoint dispatcher
│       ├── setup_wizard.py                       ← interactive setup
│       ├── verify_key.py                         ← ping-test a key
│       └── list_providers.py                     ← list configured providers
└── tests/
    ├── __init__.py
    ├── test_config.py
    ├── test_providers.py
    ├── test_http_client.py
    ├── test_errors.py
    ├── test_router.py
    ├── test_setup_wizard.py
    └── test_list_providers.py
```

**Symlink for ZCode discovery:** `~/.zcode/plugins/model-router` → `/Users/bobo/ZCodeProject/model-router`

**Per-user config (NOT in repo):** `~/.zcode/model-router/config.json`

---

## Task 0: Repo scaffold

**Files:**
- Create: `/Users/bobo/ZCodeProject/model-router/plugin.json`
- Create: `/Users/bobo/ZCodeProject/model-router/.gitignore`
- Create: `/Users/bobo/ZCodeProject/model-router/README.md`
- Create: `/Users/bobo/ZCodeProject/model-router/config.example.json`
- Create: `/Users/bobo/ZCodeProject/model-router/src/model_router/__init__.py` (empty)
- Create: `/Users/bobo/ZCodeProject/model-router/tests/__init__.py` (empty)

- [ ] **Step 1: Create directory tree**

```bash
mkdir -p /Users/bobo/ZCodeProject/model-router/{commands,src/model_router,tests}
```

- [ ] **Step 2: Write `plugin.json`**

```json
{
  "name": "model-router",
  "version": "1.0.0",
  "description": "Route tasks to GLM, DeepSeek, or Kimi via the /mr command.",
  "author": { "name": "Thanhtran-165" },
  "license": "MIT",
  "homepage": "https://github.com/Thanhtran-165/model-router",
  "commands": "commands"
}
```

- [ ] **Step 3: Write `.gitignore`**

```gitignore
# Real config contains API keys — NEVER commit
config.json
*.local.json

# Python
__pycache__/
*.pyc
*.pyo
.venv/
.pytest_cache/

# OS
.DS_Store
```

- [ ] **Step 4: Write `config.example.json`**

```json
{
  "version": "1.0",
  "providers": {
    "glm": {
      "name": "GLM (Z.ai)",
      "baseURL": "https://api.z.ai/api/anthropic",
      "model": "glm-4.6",
      "apiKey": "PASTE_YOUR_ZAI_KEY_HERE",
      "verified": false
    },
    "deepseek": {
      "name": "DeepSeek",
      "baseURL": "https://api.deepseek.com/anthropic",
      "model": "deepseek-chat",
      "apiKey": "PASTE_YOUR_DEEPSEEK_KEY_HERE",
      "verified": false
    },
    "kimi": {
      "name": "Kimi (Moonshot)",
      "baseURL": "https://api.moonshot.ai/anthropic",
      "model": "kimi-k2",
      "apiKey": "PASTE_YOUR_KIMI_KEY_HERE",
      "verified": false
    }
  }
}
```

- [ ] **Step 5: Write `README.md` (stub — expanded in Task 11)**

```markdown
# model-router

ZCode plugin to route tasks to GLM (Z.ai), DeepSeek, and Kimi (Moonshot) via `/mr`.

## Install

See full guide in Task 11. Quick version:

1. Clone this repo into `~/.zcode/plugins/model-router/`
2. Run `/mr setup` inside ZCode to configure API keys
3. Use `/mr deepseek "your task"`

Full docs: TODO (Task 11 fills this in).
```

- [ ] **Step 6: Write empty `src/model_router/__init__.py` and `tests/__init__.py`**

```python
# model_router package
```

```python
# tests package
```

- [ ] **Step 7: Write `pytest.ini` for path setup**

```ini
[pytest]
pythonpath = src
testpaths = tests
```

- [ ] **Step 8: Init git, commit, push**

```bash
cd /Users/bobo/ZCodeProject/model-router
git init
git checkout -b main
git add .
git commit -m "chore: scaffold model-router plugin repo"
git remote add origin git@github.com:Thanhtran-165/model-router.git
git push -u origin main
```

- [ ] **Step 9: Verify scaffold**

```bash
cd /Users/bobo/ZCodeProject/model-router
ls -la
ls src/model_router/
```

Expected: see `plugin.json`, `.gitignore`, `README.md`, `config.example.json`, `commands/`, `src/model_router/`, `tests/`.

---

## Task 1: Errors module (foundation)

**Files:**
- Create: `src/model_router/errors.py`
- Test: `tests/test_errors.py`

**Why first:** Other modules import errors. Build foundation before dependents.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_errors.py
import pytest
from model_router.errors import (
    ModelRouterError,
    ConfigNotFoundError,
    ProviderNotFoundError,
    ProviderNotConfiguredError,
    AuthError,
    RateLimitError,
    ServerError,
    NetworkError,
    TimeoutError as RouterTimeoutError,
    map_http_status,
)


def test_base_error_inherits_exception():
    err = ModelRouterError("boom")
    assert isinstance(err, Exception)
    assert str(err) == "boom"


def test_config_not_found_inherits_base():
    err = ConfigNotFoundError("/some/path")
    assert isinstance(err, ModelRouterError)


def test_provider_not_found_message_lists_available():
    err = ProviderNotFoundError("xxx", available=["glm", "deepseek", "kimi"])
    assert "xxx" in str(err)
    assert "glm" in str(err)


def test_provider_not_configured_includes_setup_hint():
    err = ProviderNotConfiguredError("glm")
    assert "glm" in str(err)
    assert "/mr setup" in str(err)


def test_map_http_status_401_returns_auth_error():
    err = map_http_status(401, "glm")
    assert isinstance(err, AuthError)
    assert "glm" in str(err)


def test_map_http_status_403_returns_auth_error():
    err = map_http_status(403, "deepseek")
    assert isinstance(err, AuthError)


def test_map_http_status_429_returns_rate_limit_error():
    err = map_http_status(429, "kimi")
    assert isinstance(err, RateLimitError)
    assert "60" in str(err)


def test_map_http_status_500_returns_server_error():
    err = map_http_status(500, "glm")
    assert isinstance(err, ServerError)


def test_map_http_status_502_returns_server_error():
    err = map_http_status(502, "glm")
    assert isinstance(err, ServerError)


def test_map_http_status_503_returns_server_error():
    err = map_http_status(503, "glm")
    assert isinstance(err, ServerError)


def test_map_http_status_404_returns_server_error():
    err = map_http_status(404, "glm")
    assert isinstance(err, ServerError)


def test_map_http_status_unknown_returns_base_error():
    err = map_http_status(418, "glm")
    assert isinstance(err, ModelRouterError)
    assert "418" in str(err)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_errors.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'model_router'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/model_router/errors.py
"""Typed errors for model-router and HTTP status mapping."""


class ModelRouterError(Exception):
    """Base error for all model-router failures."""


class ConfigNotFoundError(ModelRouterError):
    """Config file does not exist on disk."""

    def __init__(self, path: str):
        super().__init__(
            f"Config file not found at {path}.\n"
            f"Run `/mr setup` to create it."
        )


class ProviderNotFoundError(ModelRouterError):
    """Requested provider slug is not in the registry."""

    def __init__(self, provider: str, available: list[str]):
        avail_str = ", ".join(available)
        super().__init__(
            f"Unknown provider '{provider}'. Available: {avail_str}"
        )


class ProviderNotConfiguredError(ModelRouterError):
    """Provider exists in registry but user has not set a real key."""

    def __init__(self, provider: str):
        super().__init__(
            f"Provider '{provider}' is not configured.\n"
            f"Run `/mr setup {provider}` to add your API key."
        )


class AuthError(ModelRouterError):
    """HTTP 401/403 — bad or unauthorized key."""

    def __init__(self, provider: str):
        super().__init__(
            f"{provider} rejected the API key (HTTP 401/403).\n"
            f"Likely causes: wrong key, expired key, or no permission for the model.\n"
            f"Fix: /mr setup {provider}"
        )


class RateLimitError(ModelRouterError):
    """HTTP 429 — too many requests."""

    def __init__(self, provider: str):
        super().__init__(
            f"{provider} rate-limited the request (HTTP 429).\n"
            f"Wait ~60 seconds and retry."
        )


class ServerError(ModelRouterError):
    """HTTP 5xx or other provider-side error."""

    def __init__(self, provider: str, status: int):
        super().__init__(
            f"{provider} returned HTTP {status} (server-side error).\n"
            f"Retry in a few minutes. If persistent, check the provider's status page."
        )


class NetworkError(ModelRouterError):
    """Connection failed or DNS error."""

    def __init__(self, detail: str):
        super().__init__(
            f"Network error: {detail}\n"
            f"Check your internet connection and try again."
        )


class TimeoutError(ModelRouterError):
    """Request exceeded the timeout."""

    def __init__(self, provider: str, seconds: int):
        super().__init__(
            f"{provider} did not respond within {seconds}s.\n"
            f"Check your connection or retry with a shorter task."
        )


def map_http_status(status: int, provider: str) -> ModelRouterError:
    """Map an HTTP status code to the right typed error."""
    if status in (401, 403):
        return AuthError(provider)
    if status == 429:
        return RateLimitError(provider)
    if status >= 500 or status == 404:
        return ServerError(provider, status)
    return ModelRouterError(f"{provider} returned unexpected HTTP {status}.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_errors.py -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/bobo/ZCodeProject/model-router
git add src/model_router/errors.py tests/test_errors.py
git commit -m "feat(errors): typed errors + HTTP status mapping"
```

---

## Task 2: Provider registry

**Files:**
- Create: `src/model_router/providers.py`
- Test: `tests/test_providers.py`

**Why:** Single source of truth for the 3 providers. Used by config, router, http_client.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_providers.py
import pytest
from model_router.providers import (
    DEFAULT_PROVIDERS,
    get_provider,
    ProviderNotFoundError,
)


def test_default_providers_has_three():
    assert set(DEFAULT_PROVIDERS.keys()) == {"glm", "deepseek", "kimi"}


def test_glm_endpoint():
    p = DEFAULT_PROVIDERS["glm"]
    assert p["baseURL"] == "https://api.z.ai/api/anthropic"
    assert p["model"] == "glm-4.6"
    assert p["name"] == "GLM (Z.ai)"


def test_deepseek_endpoint():
    p = DEFAULT_PROVIDERS["deepseek"]
    assert p["baseURL"] == "https://api.deepseek.com/anthropic"
    assert p["model"] == "deepseek-chat"


def test_kimi_endpoint():
    p = DEFAULT_PROVIDERS["kimi"]
    assert p["baseURL"] == "https://api.moonshot.ai/anthropic"
    assert p["model"] == "kimi-k2"


def test_get_provider_returns_copy():
    p = get_provider("glm")
    p["apiKey"] = "mutated"
    # Mutating the returned dict must not change the registry
    assert DEFAULT_PROVIDERS["glm"]["apiKey"] != "mutated"


def test_get_provider_unknown_raises():
    with pytest.raises(ProviderNotFoundError) as exc:
        get_provider("openai")
    assert "openai" in str(exc.value)
    assert "glm" in str(exc.value)


def test_get_provider_lists_all_available():
    try:
        get_provider("nope")
    except ProviderNotFoundError as e:
        msg = str(e)
        assert "glm" in msg
        assert "deepseek" in msg
        assert "kimi" in msg
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_providers.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/model_router/providers.py
"""Registry of supported providers. Single source of truth for endpoints."""

import copy

from .errors import ProviderNotFoundError


DEFAULT_PROVIDERS: dict[str, dict] = {
    "glm": {
        "name": "GLM (Z.ai)",
        "baseURL": "https://api.z.ai/api/anthropic",
        "model": "glm-4.6",
        "apiKey": "",
        "verified": False,
    },
    "deepseek": {
        "name": "DeepSeek",
        "baseURL": "https://api.deepseek.com/anthropic",
        "model": "deepseek-chat",
        "apiKey": "",
        "verified": False,
    },
    "kimi": {
        "name": "Kimi (Moonshot)",
        "baseURL": "https://api.moonshot.ai/anthropic",
        "model": "kimi-k2",
        "apiKey": "",
        "verified": False,
    },
}


def get_provider(slug: str) -> dict:
    """Return a deep copy of a provider's default config.

    Raises ProviderNotFoundError if slug is not in the registry.
    """
    if slug not in DEFAULT_PROVIDERS:
        raise ProviderNotFoundError(slug, list(DEFAULT_PROVIDERS.keys()))
    return copy.deepcopy(DEFAULT_PROVIDERS[slug])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_providers.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/bobo/ZCodeProject/model-router
git add src/model_router/providers.py tests/test_providers.py
git commit -m "feat(providers): registry for GLM/DeepSeek/Kimi defaults"
```

---

## Task 3: Config module

**Files:**
- Create: `src/model_router/config.py`
- Test: `tests/test_config.py`

**Why:** All other modules need to load/save user config at `~/.zcode/model-router/config.json`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import json
import os
import pytest
from pathlib import Path

from model_router import config as config_module
from model_router.config import (
    get_config_path,
    load_config,
    save_config,
    ensure_config_exists,
    ConfigNotFoundError,
)


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Redirect CONFIG_DIR to a temp dir for each test."""
    fake_home = tmp_path / "home"
    fake_config_dir = fake_home / ".zcode" / "model-router"
    monkeypatch.setattr(config_module, "CONFIG_DIR", fake_config_dir)
    monkeypatch.setattr(config_module, "CONFIG_PATH", fake_config_dir / "config.json")
    return fake_config_dir


def test_config_path_is_under_zcode(isolated_config):
    path = get_config_path()
    assert ".zcode" in str(path)
    assert path.name == "config.json"


def test_load_config_raises_when_missing(isolated_config):
    with pytest.raises(ConfigNotFoundError):
        load_config()


def test_ensure_config_exists_creates_from_defaults(isolated_config):
    cfg = ensure_config_exists()
    assert (isolated_config / "config.json").exists()
    assert "glm" in cfg["providers"]
    assert "deepseek" in cfg["providers"]
    assert "kimi" in cfg["providers"]
    # Default config has no real keys
    assert cfg["providers"]["glm"]["apiKey"] == ""


def test_ensure_config_exists_idempotent(isolated_config):
    # Pre-populate with a real key
    ensure_config_exists()
    path = isolated_config / "config.json"
    data = json.loads(path.read_text())
    data["providers"]["glm"]["apiKey"] = "real-key-xyz"
    path.write_text(json.dumps(data, indent=2))

    # Second call must not overwrite
    cfg = ensure_config_exists()
    assert cfg["providers"]["glm"]["apiKey"] == "real-key-xyz"


def test_save_then_load_roundtrip(isolated_config):
    ensure_config_exists()
    cfg = load_config()
    cfg["providers"]["deepseek"]["apiKey"] = "sk-test"
    cfg["providers"]["deepseek"]["verified"] = True
    save_config(cfg)

    reloaded = load_config()
    assert reloaded["providers"]["deepseek"]["apiKey"] == "sk-test"
    assert reloaded["providers"]["deepseek"]["verified"] is True


def test_save_config_sets_file_permissions(isolated_config):
    ensure_config_exists()
    cfg = load_config()
    save_config(cfg)

    path = isolated_config / "config.json"
    mode = path.stat().st_mode & 0o777
    # On macOS, mode should be 0o600 after save
    assert mode == 0o600


def test_load_config_returns_merged_with_defaults(isolated_config):
    """If config file has a missing provider, it should be filled in from defaults."""
    ensure_config_exists()
    path = isolated_config / "config.json"
    # Remove kimi from saved config
    data = json.loads(path.read_text())
    del data["providers"]["kimi"]
    path.write_text(json.dumps(data))

    cfg = load_config()
    # kimi should be re-added from defaults
    assert "kimi" in cfg["providers"]


def test_load_config_merges_new_fields(isolated_config):
    """If a provider gains a new field in defaults, it should appear after load."""
    ensure_config_exists()
    path = isolated_config / "config.json"
    data = json.loads(path.read_text())
    # Remove 'verified' field from glm
    del data["providers"]["glm"]["verified"]
    path.write_text(json.dumps(data))

    cfg = load_config()
    assert "verified" in cfg["providers"]["glm"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/model_router/config.py
"""Load/save user config at ~/.zcode/model-router/config.json.

Keys live ONLY in this file (never in the repo). File mode is 0o600.
"""

import copy
import json
import os
from pathlib import Path

from .errors import ConfigNotFoundError
from .providers import DEFAULT_PROVIDERS


CONFIG_DIR = Path.home() / ".zcode" / "model-router"
CONFIG_PATH = CONFIG_DIR / "config.json"


def get_config_path() -> Path:
    """Return the absolute path to the user's config file."""
    return CONFIG_PATH


def _default_config() -> dict:
    """Return a fresh config built from DEFAULT_PROVIDERS."""
    return {
        "version": "1.0",
        "providers": copy.deepcopy(DEFAULT_PROVIDERS),
    }


def _merge_with_defaults(saved: dict) -> dict:
    """Merge a saved config with defaults so missing providers/fields are filled."""
    defaults = _default_config()
    merged = defaults
    for slug, saved_prov in saved.get("providers", {}).items():
        if slug in merged["providers"]:
            merged["providers"][slug].update(saved_prov)
        else:
            merged["providers"][slug] = saved_prov
    return merged


def ensure_config_exists() -> dict:
    """Create config from defaults if missing. Return current config.

    Idempotent: never overwrites an existing config.
    """
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        cfg = _default_config()
        save_config(cfg)
        return cfg
    return load_config()


def load_config() -> dict:
    """Load and return config. Raises ConfigNotFoundError if missing."""
    if not CONFIG_PATH.exists():
        raise ConfigNotFoundError(str(CONFIG_PATH))
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigNotFoundError(
            f"{CONFIG_PATH} is corrupt or empty: {e}"
        )
    return _merge_with_defaults(saved)


def save_config(cfg: dict) -> None:
    """Write config to disk with mode 0o600."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Write atomically: temp file then rename
    tmp = CONFIG_PATH.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG_PATH)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_config.py -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/bobo/ZCodeProject/model-router
git add src/model_router/config.py tests/test_config.py
git commit -m "feat(config): load/save user config with chmod 600 + default merge"
```

---

## Task 4: HTTP client (Anthropic Messages API)

**Files:**
- Create: `src/model_router/http_client.py`
- Test: `tests/test_http_client.py`

**Why:** The core call to provider. Must handle errors correctly before router can use it.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_http_client.py
import json
import urllib.error
import socket
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from model_router import http_client as hc
from model_router.http_client import call_provider, HTTPTimeoutError
from model_router.errors import AuthError, RateLimitError, ServerError, NetworkError


def _make_response(body: dict, status: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = json.dumps(body).encode("utf-8")
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _make_http_error(status: int, body: dict) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="https://example.com",
        code=status,
        msg="error",
        hdrs=None,
        fp=BytesIO(json.dumps(body).encode("utf-8")),
    )


def test_call_provider_success_returns_text():
    provider_cfg = {
        "baseURL": "https://api.deepseek.com/anthropic",
        "model": "deepseek-chat",
        "apiKey": "sk-test",
    }
    resp_body = {
        "content": [{"type": "text", "text": "Hello from DeepSeek!"}],
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }
    with patch("urllib.request.urlopen", return_value=_make_response(resp_body)) as m:
        result = call_provider(provider_cfg, "hello", provider_name="deepseek")
    assert result["text"] == "Hello from DeepSeek!"
    assert result["input_tokens"] == 10
    assert result["output_tokens"] == 5
    # Verify request shape
    req = m.call_args.args[0]
    body = json.loads(req.data)
    assert body["model"] == "deepseek-chat"
    assert body["messages"] == [{"role": "user", "content": "hello"}]
    assert body["max_tokens"] > 0
    assert req.headers["x-api-key"] == "sk-test"
    assert req.headers["Content-type"] == "application/json"
    assert req.headers["Anthropic-version"] == "2023-06-01"


def test_call_provider_uses_anthropic_messages_path():
    provider_cfg = {
        "baseURL": "https://api.z.ai/api/anthropic",
        "model": "glm-4.6",
        "apiKey": "sk",
    }
    captured_url = {}

    def fake_urlopen(req, timeout=None):
        captured_url["url"] = req.full_url
        return _make_response({
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        })

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        call_provider(provider_cfg, "hi", provider_name="glm")
    assert captured_url["url"] == "https://api.z.ai/api/anthropic/v1/messages"


def test_call_provider_strips_trailing_slash_in_baseurl():
    provider_cfg = {
        "baseURL": "https://api.moonshot.ai/anthropic/",
        "model": "kimi-k2",
        "apiKey": "sk",
    }
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        return _make_response({
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        })

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        call_provider(provider_cfg, "hi", provider_name="kimi")
    assert captured["url"] == "https://api.moonshot.ai/anthropic/v1/messages"


def test_call_provider_401_raises_auth_error():
    provider_cfg = {"baseURL": "https://x", "model": "m", "apiKey": "bad"}
    err = _make_http_error(401, {"error": {"message": "unauthorized"}})
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(AuthError):
            call_provider(provider_cfg, "hi", provider_name="glm")


def test_call_provider_403_raises_auth_error():
    provider_cfg = {"baseURL": "https://x", "model": "m", "apiKey": "bad"}
    err = _make_http_error(403, {"error": {"message": "forbidden"}})
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(AuthError):
            call_provider(provider_cfg, "hi", provider_name="glm")


def test_call_provider_429_raises_rate_limit_error():
    provider_cfg = {"baseURL": "https://x", "model": "m", "apiKey": "sk"}
    err = _make_http_error(429, {"error": {"message": "slow down"}})
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(RateLimitError):
            call_provider(provider_cfg, "hi", provider_name="deepseek")


def test_call_provider_500_raises_server_error():
    provider_cfg = {"baseURL": "https://x", "model": "m", "apiKey": "sk"}
    err = _make_http_error(500, {"error": {"message": "internal"}})
    with patch("urllib.request.urlopen", side_effect=err):
        with pytest.raises(ServerError):
            call_provider(provider_cfg, "hi", provider_name="kimi")


def test_call_provider_urllib_timeout_raises_timeout_error():
    provider_cfg = {"baseURL": "https://x", "model": "m", "apiKey": "sk"}
    with patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
        with pytest.raises(HTTPTimeoutError):
            call_provider(provider_cfg, "hi", provider_name="glm", timeout_seconds=5)


def test_call_provider_network_error_raises_network_error():
    provider_cfg = {"baseURL": "https://x", "model": "m", "apiKey": "sk"}
    with patch("urllib.request.urlopen", side_effect=ConnectionError("no route")):
        with pytest.raises(NetworkError):
            call_provider(provider_cfg, "hi", provider_name="glm")


def test_call_provider_extracts_text_from_content_blocks():
    provider_cfg = {"baseURL": "https://x", "model": "m", "apiKey": "sk"}
    body = {
        "content": [
            {"type": "text", "text": "part 1"},
            {"type": "text", "text": "part 2"},
        ],
        "usage": {"input_tokens": 3, "output_tokens": 7},
    }
    with patch("urllib.request.urlopen", return_value=_make_response(body)):
        result = call_provider(provider_cfg, "hi", provider_name="glm")
    assert result["text"] == "part 1part 2"


def test_call_provider_missing_content_returns_empty():
    provider_cfg = {"baseURL": "https://x", "model": "m", "apiKey": "sk"}
    body = {"usage": {"input_tokens": 1, "output_tokens": 0}}
    with patch("urllib.request.urlopen", return_value=_make_response(body)):
        result = call_provider(provider_cfg, "hi", provider_name="glm")
    assert result["text"] == ""
    assert result["output_tokens"] == 0


def test_call_provider_task_truncation_warning_when_too_long(capfd):
    provider_cfg = {"baseURL": "https://x", "model": "m", "apiKey": "sk"}
    long_task = "x" * 9000
    body = {"content": [{"type": "text", "text": "ok"}], "usage": {"input_tokens": 1, "output_tokens": 1}}
    with patch("urllib.request.urlopen", return_value=_make_response(body)):
        call_provider(provider_cfg, long_task, provider_name="glm")
    out = capfd.readouterr().out
    assert "warning" in out.lower() or "long" in out.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_http_client.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/model_router/http_client.py
"""HTTP client for Anthropic-compatible endpoints (GLM/DeepSeek/Kimi)."""

import json
import socket
import sys
import urllib.error
import urllib.request

from .errors import (
    AuthError,
    ModelRouterError,
    NetworkError,
    RateLimitError,
    ServerError,
    map_http_status,
)


ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_TIMEOUT_SECONDS = 60
LONG_TASK_WARN_THRESHOLD = 8000  # chars
DEFAULT_MAX_TOKENS = 4096


class HTTPTimeoutError(ModelRouterError):
    """urllib-level socket timeout."""


def _build_url(baseURL: str) -> str:
    base = baseURL.rstrip("/")
    return f"{base}/v1/messages"


def _build_body(model: str, task: str, max_tokens: int = DEFAULT_MAX_TOKENS) -> bytes:
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": task}],
    }
    return json.dumps(payload).encode("utf-8")


def _build_request(url: str, api_key: str, body: bytes) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-type": "application/json",
            "x-api-key": api_key,
            "Anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )


def _extract_text(response_body: dict) -> str:
    blocks = response_body.get("content", []) or []
    parts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
    return "".join(parts)


def _extract_usage(response_body: dict) -> tuple[int, int]:
    usage = response_body.get("usage", {}) or {}
    return usage.get("input_tokens", 0), usage.get("output_tokens", 0)


def call_provider(
    provider_cfg: dict,
    task: str,
    provider_name: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    """Send task to provider and return {text, input_tokens, output_tokens}.

    Raises typed errors from .errors on failure.
    """
    if len(task) > LONG_TASK_WARN_THRESHOLD:
        sys.stderr.write(
            f"warning: task is {len(task)} chars (> {LONG_TASK_WARN_THRESHOLD}); "
            f"this may be slow or truncated.\n"
        )

    url = _build_url(provider_cfg["baseURL"])
    body = _build_body(provider_cfg["model"], task, max_tokens=max_tokens)
    req = _build_request(url, provider_cfg["apiKey"], body)

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        err = map_http_status(e.code, provider_name)
        raise err from e
    except socket.timeout as e:
        raise HTTPTimeoutError(
            f"{provider_name} did not respond within {timeout_seconds}s."
        ) from e
    except (ConnectionError, urllib.error.URLError) as e:
        raise NetworkError(str(e)) from e

    try:
        response_body = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise ServerError(provider_name, 200) from e

    text = _extract_text(response_body)
    input_tokens, output_tokens = _extract_usage(response_body)
    return {
        "text": text,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_http_client.py -v`
Expected: PASS (13 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/bobo/ZCodeProject/model-router
git add src/model_router/http_client.py tests/test_http_client.py
git commit -m "feat(http): Anthropic-compatible client with typed error handling"
```

---

## Task 5: Verify-key module

**Files:**
- Create: `src/model_router/verify_key.py`
- Test: `tests/test_verify_key.py`

**Why:** Used by setup wizard to confirm a key actually works. Thin wrapper over http_client.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_verify_key.py
import json
import pytest
from unittest.mock import patch, MagicMock

from model_router.verify_key import verify_key, VerifyResult


def _ok_response():
    resp = MagicMock()
    resp.status = 200
    resp.read.return_value = json.dumps({
        "content": [{"type": "text", "text": "ok"}],
        "usage": {"input_tokens": 2, "output_tokens": 1},
    }).encode("utf-8")
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_verify_key_success_returns_ok():
    cfg = {"baseURL": "https://x", "model": "m", "apiKey": "good"}
    with patch("urllib.request.urlopen", return_value=_ok_response()):
        result = verify_key(cfg, provider_name="glm")
    assert result.ok is True
    assert result.message == "Key is valid"


def test_verify_key_401_returns_not_ok():
    import urllib.error
    from io import BytesIO
    cfg = {"baseURL": "https://x", "model": "m", "apiKey": "bad"}
    err = urllib.error.HTTPError(
        "https://x", 401, "bad", None,
        BytesIO(json.dumps({"error": {"message": "unauthorized"}}).encode()),
    )
    with patch("urllib.request.urlopen", side_effect=err):
        result = verify_key(cfg, provider_name="glm")
    assert result.ok is False
    assert "401" in result.message or "rejected" in result.message.lower()


def test_verify_key_network_error_returns_not_ok():
    cfg = {"baseURL": "https://x", "model": "m", "apiKey": "good"}
    with patch("urllib.request.urlopen", side_effect=ConnectionError("dns fail")):
        result = verify_key(cfg, provider_name="glm")
    assert result.ok is False
    assert "network" in result.message.lower() or "dns" in result.message.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_verify_key.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/model_router/verify_key.py
"""Verify that an API key works against a provider's endpoint.

Sends a tiny 'ping' task; success = key is good.
"""

from dataclasses import dataclass

from .errors import ModelRouterError
from .http_client import call_provider


@dataclass
class VerifyResult:
    ok: bool
    message: str


def verify_key(provider_cfg: dict, provider_name: str) -> VerifyResult:
    """Send a small ping and return VerifyResult.

    Never raises — returns VerifyResult(ok=False, message=...) on any error.
    """
    try:
        result = call_provider(
            provider_cfg,
            task="ping",
            provider_name=provider_name,
            timeout_seconds=15,
            max_tokens=10,
        )
        return VerifyResult(ok=True, message="Key is valid")
    except ModelRouterError as e:
        return VerifyResult(ok=False, message=str(e))
    except Exception as e:
        return VerifyResult(ok=False, message=f"Unexpected error: {e}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_verify_key.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/bobo/ZCodeProject/model-router
git add src/model_router/verify_key.py tests/test_verify_key.py
git commit -m "feat(verify): ping-test an API key against a provider"
```

---

## Task 6: Setup wizard

**Files:**
- Create: `src/model_router/setup_wizard.py`
- Test: `tests/test_setup_wizard.py`

**Why:** Interactive UX for first-run. Most complex module — needs careful testing.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_setup_wizard.py
import json
import pytest
from unittest.mock import patch, MagicMock

from model_router import config as config_module
from model_router.setup_wizard import run_setup, _setup_one_provider


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    fake_dir = tmp_path / ".zcode" / "model-router"
    monkeypatch.setattr(config_module, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(config_module, "CONFIG_PATH", fake_dir / "config.json")
    return fake_dir


def test_run_setup_all_providers_skipped(isolated_config, capsys):
    inputs = iter(["n", "n", "n"])
    with patch("builtins.input", side_effect=lambda *a, **k: next(inputs)):
        run_setup(target=None)
    out = capsys.readouterr().out
    assert "skip" in out.lower() or "saved" in out.lower()


def test_run_setup_one_provider_with_valid_key(isolated_config, capsys):
    # User says yes to glm, pastes key, key verifies OK
    from model_router.verify_key import VerifyResult
    inputs = iter(["y", "sk-glm-123", "n", "n"])
    with patch("builtins.input", side_effect=lambda *a, **k: next(inputs)), \
         patch("model_router.setup_wizard.verify_key", return_value=VerifyResult(ok=True, message="Key is valid")):
        run_setup(target=None)
    cfg = config_module.load_config()
    assert cfg["providers"]["glm"]["apiKey"] == "sk-glm-123"
    assert cfg["providers"]["glm"]["verified"] is True


def test_run_setup_one_provider_with_invalid_key(isolated_config, capsys):
    # User pastes bad key, verify fails, asks again, user gives 'skip'
    from model_router.verify_key import VerifyResult
    inputs = iter(["y", "bad-key", "n"])  # yes, bad key, then skip retry
    with patch("builtins.input", side_effect=lambda *a, **k: next(inputs)), \
         patch("model_router.setup_wizard.verify_key", return_value=VerifyResult(ok=False, message="401 rejected")):
        run_setup(target=None)
    cfg = config_module.load_config()
    # Key should not be saved when verification failed
    assert cfg["providers"]["glm"]["apiKey"] == ""
    assert cfg["providers"]["glm"]["verified"] is False


def test_run_setup_specific_provider_only(isolated_config, capsys):
    from model_router.verify_key import VerifyResult
    inputs = iter(["y", "sk-ds-456"])
    with patch("builtins.input", side_effect=lambda *a, **k: next(inputs)), \
         patch("model_router.setup_wizard.verify_key", return_value=VerifyResult(ok=True, message="ok")):
        run_setup(target="deepseek")
    cfg = config_module.load_config()
    assert cfg["providers"]["deepseek"]["apiKey"] == "sk-ds-456"
    assert cfg["providers"]["deepseek"]["verified"] is True
    # Other providers untouched
    assert cfg["providers"]["glm"]["apiKey"] == ""
    assert cfg["providers"]["kimi"]["apiKey"] == ""


def test_run_setup_unknown_target_raises(isolated_config):
    from model_router.errors import ProviderNotFoundError
    with pytest.raises(ProviderNotFoundError):
        run_setup(target="openai")


def test_setup_one_provider_skip_all_short_circuits(isolated_config):
    # When user picks 'skip-all', remaining providers are not prompted
    inputs = iter(["skip-all"])
    prompts_seen = []

    def fake_input(prompt=""):
        prompts_seen.append(prompt)
        return next(inputs)

    cfg = config_module.ensure_config_exists()
    with patch("builtins.input", side_effect=fake_input):
        result = _setup_one_provider(cfg, "glm", total=3, index=1)
    assert result == "skip-all"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_setup_wizard.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/model_router/setup_wizard.py
"""Interactive setup wizard for configuring API keys."""

import getpass
import sys

from .config import ensure_config_exists, save_config
from .errors import ProviderNotFoundError
from .providers import DEFAULT_PROVIDERS
from .verify_key import verify_key


def _print_header():
    print()
    print("Model Router Setup")
    print("=" * 40)
    print()


def _prompt_yes_no_skip(prompt: str) -> str:
    """Return 'y', 'n', or 'skip-all'."""
    while True:
        ans = input(prompt).strip().lower()
        if ans in ("y", "yes"):
            return "y"
        if ans in ("n", "no"):
            return "n"
        if ans == "skip-all":
            return "skip-all"


def _prompt_api_key(provider_name: str) -> str:
    """Use getpass so the key is not echoed to terminal."""
    return getpass.getpass(f"  Paste API key for {provider_name}: ").strip()


def _setup_one_provider(
    cfg: dict, slug: str, total: int, index: int
) -> str:
    """Configure a single provider. Returns 'ok', 'skip', or 'skip-all'."""
    prov = cfg["providers"][slug]
    name = prov["name"]
    print(f"--- Provider {index}/{total}: {name} ({slug}) ---")
    print(f"  Endpoint: {prov['baseURL']}")
    print(f"  Model:    {prov['model']}")
    choice = _prompt_yes_no_skip(
        f"  Have an API key for {name}? (y/n/skip-all): "
    )
    if choice == "skip-all":
        print(f"  → Skipping all remaining providers.")
        return "skip-all"
    if choice == "n":
        print(f"  → Skipped. Run `/mr setup {slug}` later.")
        return "skip"

    # User has a key — prompt and verify
    while True:
        key = _prompt_api_key(name)
        if not key:
            print("  Empty key. Try again or press Ctrl+C to abort.")
            continue
        print(f"  Testing key...")
        result = verify_key(prov, provider_name=slug)
        if result.ok:
            prov["apiKey"] = key
            prov["verified"] = True
            print(f"  ✓ Key is valid")
            return "ok"
        else:
            print(f"  ✗ Verification failed: {result.message}")
            retry = _prompt_yes_no_skip(
                f"  Try another key for {name}? (y/n): "
            )
            if retry == "n":
                print(f"  → Skipped. Provider {slug} remains unconfigured.")
                return "skip"


def run_setup(target: str | None = None) -> None:
    """Run setup wizard. If target is None, prompt for all 3 providers.

    If target is a slug, only configure that provider.
    """
    if target is not None and target not in DEFAULT_PROVIDERS:
        raise ProviderNotFoundError(target, list(DEFAULT_PROVIDERS.keys()))

    cfg = ensure_config_exists()

    if target is not None:
        _print_header()
        print(f"Re-configuring single provider: {target}")
        print()
        _setup_one_provider(cfg, target, total=1, index=1)
        save_config(cfg)
        print()
        print(f"✓ Saved config.")
        print(f"Try: /mr {target} \"hello\"")
        return

    _print_header()
    print("I will configure 3 model providers:")
    for i, slug in enumerate(DEFAULT_PROVIDERS, start=1):
        print(f"  {i}. {DEFAULT_PROVIDERS[slug]['name']}")
    print()

    total = len(DEFAULT_PROVIDERS)
    skip_all = False
    for i, slug in enumerate(DEFAULT_PROVIDERS, start=1):
        if skip_all:
            break
        result = _setup_one_provider(cfg, slug, total=total, index=i)
        if result == "skip-all":
            skip_all = True

    save_config(cfg)
    verified_count = sum(
        1 for p in cfg["providers"].values() if p.get("verified")
    )
    print()
    print(f"✓ Saved config: ~/.zcode/model-router/config.json")
    print(f"✓ {verified_count}/{total} providers verified.")
    print()
    print(f"Try: /mr deepseek \"hello, introduce yourself\"")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_setup_wizard.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/bobo/ZCodeProject/model-router
git add src/model_router/setup_wizard.py tests/test_setup_wizard.py
git commit -m "feat(setup): interactive wizard with key verification"
```

---

## Task 7: List-providers module

**Files:**
- Create: `src/model_router/list_providers.py`
- Test: `tests/test_list_providers.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_list_providers.py
import pytest
from unittest.mock import patch

from model_router import config as config_module
from model_router.list_providers import list_providers


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    fake_dir = tmp_path / ".zcode" / "model-router"
    monkeypatch.setattr(config_module, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(config_module, "CONFIG_PATH", fake_dir / "config.json")
    return fake_dir


def test_list_shows_three_providers(isolated_config, capsys):
    config_module.ensure_config_exists()
    list_providers()
    out = capsys.readouterr().out
    assert "glm" in out.lower()
    assert "deepseek" in out.lower()
    assert "kimi" in out.lower()


def test_list_marks_unconfigured_providers(isolated_config, capsys):
    config_module.ensure_config_exists()
    list_providers()
    out = capsys.readouterr().out
    # Fresh config — all should be unconfigured
    assert "not configured" in out.lower() or "unconfigured" in out.lower() or "✗" in out


def test_list_marks_verified_providers(isolated_config, capsys):
    config_module.ensure_config_exists()
    cfg = config_module.load_config()
    cfg["providers"]["deepseek"]["apiKey"] = "sk-x"
    cfg["providers"]["deepseek"]["verified"] = True
    config_module.save_config(cfg)

    list_providers()
    out = capsys.readouterr().out
    assert "✓" in out  # at least one verified


def test_list_shows_endpoint_and_model(isolated_config, capsys):
    config_module.ensure_config_exists()
    list_providers()
    out = capsys.readouterr().out
    assert "api.z.ai" in out
    assert "glm-4.6" in out
    assert "deepseek-chat" in out
    assert "kimi-k2" in out


def test_list_when_no_config_suggests_setup(isolated_config, capsys):
    # Don't call ensure_config_exists; load will raise
    list_providers()
    out = capsys.readouterr().out
    assert "/mr setup" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_list_providers.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/model_router/list_providers.py
"""Print a table of configured providers and their status."""

from .config import load_config
from .errors import ConfigNotFoundError
from .providers import DEFAULT_PROVIDERS


def _status_marker(prov: dict) -> str:
    if prov.get("verified"):
        return "✓ verified"
    if prov.get("apiKey") and prov["apiKey"] not in ("", "PASTE_YOUR_*_KEY_HERE"):
        return "⚠ key set, unverified"
    return "✗ not configured"


def list_providers() -> None:
    try:
        cfg = load_config()
    except ConfigNotFoundError:
        print("No config found. Run `/mr setup` first.")
        return

    print()
    print("Configured providers")
    print("=" * 60)
    for slug in DEFAULT_PROVIDERS:
        prov = cfg["providers"].get(slug)
        if not prov:
            continue
        print(f"  {slug:<10} {prov['name']}")
        print(f"             endpoint: {prov['baseURL']}")
        print(f"             model:    {prov['model']}")
        print(f"             status:   {_status_marker(prov)}")
        print()
    path = "~/.zcode/model-router/config.json"
    print(f"Config file: {path}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_list_providers.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/bobo/ZCodeProject/model-router
git add src/model_router/list_providers.py tests/test_list_providers.py
git commit -m "feat(list): show provider status table"
```

---

## Task 8: Router (CLI dispatcher)

**Files:**
- Create: `src/model_router/router.py`
- Test: `tests/test_router.py`

**Why:** Entry point — the function the command will call. Pulls together all modules.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_router.py
import pytest
from unittest.mock import patch, MagicMock

from model_router import config as config_module
from model_router.router import dispatch, print_help


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    fake_dir = tmp_path / ".zcode" / "model-router"
    monkeypatch.setattr(config_module, "CONFIG_DIR", fake_dir)
    monkeypatch.setattr(config_module, "CONFIG_PATH", fake_dir / "config.json")
    return fake_dir


def test_dispatch_no_args_prints_help(capsys):
    dispatch([])
    out = capsys.readouterr().out
    assert "/mr" in out
    assert "setup" in out
    assert "list" in out


def test_dispatch_help_flag_prints_help(capsys):
    dispatch(["--help"])
    out = capsys.readouterr().out
    assert "/mr" in out


def test_dispatch_list_calls_list_providers(capsys):
    config_module.ensure_config_exists()
    dispatch(["list"])
    out = capsys.readouterr().out
    assert "glm" in out


def test_dispatch_setup_no_target_calls_run_setup(isolated_config):
    with patch("model_router.router.run_setup") as m:
        dispatch(["setup"])
    m.assert_called_once_with(target=None)


def test_dispatch_setup_with_target(isolated_config):
    with patch("model_router.router.run_setup") as m:
        dispatch(["setup", "deepseek"])
    m.assert_called_once_with(target="deepseek")


def test_dispatch_unknown_provider_prints_error(capsys):
    dispatch(["openai", "hello"])
    out = capsys.readouterr().out
    assert "openai" in out
    assert "glm" in out  # available list


def test_dispatch_provider_not_configured_prints_error(isolated_config, capsys):
    config_module.ensure_config_exists()  # all empty
    dispatch(["deepseek", "hello"])
    out = capsys.readouterr().out
    assert "not configured" in out.lower() or "/mr setup" in out


def test_dispatch_provider_with_valid_config_calls_http(isolated_config, capsys):
    config_module.ensure_config_exists()
    cfg = config_module.load_config()
    cfg["providers"]["deepseek"]["apiKey"] = "sk-x"
    cfg["providers"]["deepseek"]["verified"] = True
    config_module.save_config(cfg)

    fake_result = {"text": "hi from deepseek", "input_tokens": 3, "output_tokens": 4}
    with patch("model_router.router.call_provider", return_value=fake_result) as m:
        dispatch(["deepseek", "refactor my code"])
    out = capsys.readouterr().out
    assert "hi from deepseek" in out
    # Verify call_provider got the right provider cfg
    called_cfg = m.call_args.args[0]
    assert called_cfg["apiKey"] == "sk-x"
    assert m.call_args.args[1] == "refactor my code"


def test_dispatch_provider_no_task_prints_error(isolated_config, capsys):
    config_module.ensure_config_exists()
    cfg = config_module.load_config()
    cfg["providers"]["glm"]["apiKey"] = "sk-x"
    cfg["providers"]["glm"]["verified"] = True
    config_module.save_config(cfg)

    dispatch(["glm"])
    out = capsys.readouterr().out
    assert "task" in out.lower() or "usage" in out.lower()


def test_dispatch_strips_quotes_around_task(isolated_config, capsys):
    config_module.ensure_config_exists()
    cfg = config_module.load_config()
    cfg["providers"]["kimi"]["apiKey"] = "sk-x"
    cfg["providers"]["kimi"]["verified"] = True
    config_module.save_config(cfg)

    fake_result = {"text": "ok", "input_tokens": 1, "output_tokens": 1}
    with patch("model_router.router.call_provider", return_value=fake_result) as m:
        dispatch(["kimi", '"hello world"'])
    assert m.call_args.args[1] == "hello world"


def test_dispatch_handles_http_error_gracefully(isolated_config, capsys):
    config_module.ensure_config_exists()
    cfg = config_module.load_config()
    cfg["providers"]["glm"]["apiKey"] = "sk-bad"
    cfg["providers"]["glm"]["verified"] = True
    config_module.save_config(cfg)

    from model_router.errors import AuthError
    with patch("model_router.router.call_provider", side_effect=AuthError("glm")):
        dispatch(["glm", "hello"])
    out = capsys.readouterr().out
    assert "401" in out or "rejected" in out.lower() or "/mr setup glm" in out


def test_print_help_contains_examples(capsys):
    print_help()
    out = capsys.readouterr().out
    assert "/mr deepseek" in out
    assert "/mr setup" in out
    assert "/mr list" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_router.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/model_router/router.py
"""CLI dispatcher. Parses args and routes to setup/list/<provider>."""

import sys

from .config import load_config
from .errors import (
    ConfigNotFoundError,
    ModelRouterError,
    ProviderNotConfiguredError,
    ProviderNotFoundError,
)
from .http_client import call_provider
from .list_providers import list_providers
from .providers import DEFAULT_PROVIDERS
from .setup_wizard import run_setup


def print_help() -> None:
    print()
    print("model-router — route tasks to GLM, DeepSeek, or Kimi")
    print("=" * 60)
    print()
    print("Usage:")
    print("  /mr <provider> \"<task>\"      Send task to provider")
    print("  /mr setup                     Configure API keys (all providers)")
    print("  /mr setup <provider>          Re-configure a single provider")
    print("  /mr list                      Show configured providers")
    print("  /mr                           Show this help")
    print()
    print("Providers: " + ", ".join(DEFAULT_PROVIDERS.keys()))
    print()
    print("Examples:")
    print('  /mr deepseek "refactor this function"')
    print('  /mr glm "write tests for auth.py"')
    print('  /mr kimi "review this diff"')


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def _dispatch_provider(provider: str, task_args: list[str]) -> None:
    try:
        cfg = load_config()
    except ConfigNotFoundError:
        print(f"✗ No config found. Run `/mr setup` first.")
        return

    prov_cfg = cfg["providers"].get(provider)
    if not prov_cfg:
        # Shouldn't happen — provider was validated earlier — but be safe
        raise ProviderNotFoundError(provider, list(DEFAULT_PROVIDERS.keys()))

    if not prov_cfg.get("apiKey") or prov_cfg["apiKey"].startswith("PASTE_"):
        print(f"✗ Provider '{provider}' is not configured.")
        print(f"  Run: /mr setup {provider}")
        return

    if not task_args:
        print(f"✗ Missing task.")
        print(f'  Usage: /mr {provider} "<your task>"')
        return

    task = _strip_quotes(" ".join(task_args))

    print(f"→ Provider: {prov_cfg['name']} ({prov_cfg['model']})")
    print(f"→ Endpoint: {prov_cfg['baseURL']}")
    print(f"→ Sending...")
    print()
    try:
        result = call_provider(prov_cfg, task, provider_name=provider)
    except ModelRouterError as e:
        print(f"✗ {e}")
        return

    print(result["text"])
    print()
    print(f"→ Tokens: input={result['input_tokens']}, output={result['output_tokens']}")


def dispatch(argv: list[str]) -> int:
    """Main dispatcher. Returns exit code (0=success, 1=error)."""
    if not argv or argv[0] in ("-h", "--help", "help"):
        print_help()
        return 0

    cmd = argv[0]
    rest = argv[1:]

    if cmd == "setup":
        target = rest[0] if rest else None
        if target is not None and target not in DEFAULT_PROVIDERS:
            try:
                raise ProviderNotFoundError(target, list(DEFAULT_PROVIDERS.keys()))
            except ProviderNotFoundError as e:
                print(f"✗ {e}")
                return 1
        try:
            run_setup(target=target)
        except (KeyboardInterrupt, EOFError):
            print("\nSetup aborted.")
        return 0

    if cmd == "list":
        list_providers()
        return 0

    if cmd in DEFAULT_PROVIDERS:
        try:
            _dispatch_provider(cmd, rest)
        except ProviderNotFoundError as e:
            print(f"✗ {e}")
            return 1
        return 0

    # Unknown command or provider
    try:
        raise ProviderNotFoundError(cmd, list(DEFAULT_PROVIDERS.keys()))
    except ProviderNotFoundError as e:
        print(f"✗ {e}")
        return 1


def main() -> None:
    """Entry point when invoked as `python -m model_router.router`."""
    code = dispatch(sys.argv[1:])
    sys.exit(code)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest tests/test_router.py -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Commit**

```bash
cd /Users/bobo/ZCodeProject/model-router
git add src/model_router/router.py tests/test_router.py
git commit -m "feat(router): CLI dispatcher wiring setup/list/provider together"
```

---

## Task 9: Command file for ZCode

**Files:**
- Create: `commands/mr.md`
- Modify: `plugin.json` (already has `"commands": "commands"`)

- [ ] **Step 1: Write `commands/mr.md`**

```markdown
---
description: |
  Route a task to an external model (GLM, DeepSeek, or Kimi) via the model-router plugin. Use when the user explicitly names one of these providers, e.g. "use deepseek to refactor X", "have kimi review this diff", "let glm write tests for Y". Typical triggers: "dùng deepseek", "kimi review", "glm viết test", "send this to deepseek/kimi/glm". Also handles first-time configuration via `/mr setup` and listing configured providers via `/mr list`. Cú pháp: `/mr <provider> "<task>"` hoặc `/mr setup` hoặc `/mr list`.
argument-hint: "[provider] [\"task\"] | setup [provider] | list"
---

You are the model-router command handler. The user invoked `/mr` with these arguments:

```
$ARGUMENTS
```

## Behavior

1. If `$ARGUMENTS` is empty, run `python3 -m model_router.router` (no args) to show help.

2. Run the router with the parsed arguments:

```bash
cd /Users/bobo/ZCodeProject/model-router && python3 -m model_router.router $ARGUMENTS
```

3. If the user has not yet configured API keys, the router will tell them to run `/mr setup`. Do NOT attempt to fix this automatically — surface the message.

4. For `/mr setup`: the wizard is interactive — it prompts for input via `input()` and `getpass.getpass()`. Run it in the foreground so the user can answer prompts. Do NOT pipe answers automatically.

5. For `/mr <provider> "<task>"`: the script makes a real HTTP call. Wait for completion and relay the full response text to the user verbatim. Do NOT summarize or paraphrase the model's output.

6. If the router returns an error message (lines starting with `✗`), relay it verbatim to the user and suggest the documented fix (e.g. `/mr setup <provider>`).

7. After a successful call, also relay the trailing `→ Tokens: ...` line so the user sees token usage.

## Examples the user might invoke

- `/mr setup` — first-time configuration
- `/mr setup deepseek` — reconfigure only DeepSeek's key
- `/mr list` — show which providers are configured
- `/mr deepseek "refactor auth.py"` — send a task to DeepSeek
- `/mr glm "write tests for utils.py"` — send a task to GLM
- `/mr kimi "review this PR diff"` — send a task to Kimi
- `/mr` — show help

## Notes

- API keys live in `~/.zcode/model-router/config.json` (chmod 600, never in git).
- Plugin install path: `/Users/bobo/ZCodeProject/model-router/`.
- The router uses Python stdlib only — no `pip install` needed.
```

- [ ] **Step 2: Smoke-test the command flow manually**

Run (help):
```bash
cd /Users/bobo/ZCodeProject/model-router && python3 -m model_router.router
```
Expected: prints help text with examples.

Run (unknown provider):
```bash
cd /Users/bobo/ZCodeProject/model-router && python3 -m model_router.router openai "hello"
```
Expected: `✗ Unknown provider 'openai'. Available: glm, deepseek, kimi`.

Run (list before setup — note this will create a real config in `~/.zcode/`; that's intended):
```bash
cd /Users/bobo/ZCodeProject/model-router && python3 -m model_router.router list
```
Expected: table with 3 providers, all marked `✗ not configured`.

- [ ] **Step 3: Commit**

```bash
cd /Users/bobo/ZCodeProject/model-router
git add commands/mr.md
git commit -m "feat(command): /mr command file for ZCode"
```

---

## Task 10: Install the plugin into ZCode

**Files:**
- Modify: `~/.zcode/plugins/model-router` (symlink)

**Why:** ZCode auto-discovers plugins in `~/.zcode/plugins/`. Symlink keeps source in the git repo.

- [ ] **Step 1: Check existing plugins dir layout**

```bash
ls -la ~/.zcode/plugins/ 2>/dev/null
```

- [ ] **Step 2: Create symlink**

```bash
ln -s /Users/bobo/ZCodeProject/model-router ~/.zcode/plugins/model-router
ls -la ~/.zcode/plugins/model-router
```

Expected: symlink points to the repo dir.

- [ ] **Step 3: Verify plugin is discoverable**

```bash
ls ~/.zcode/plugins/model-router/plugin.json
cat ~/.zcode/plugins/model-router/plugin.json
```

Expected: file exists, valid JSON.

- [ ] **Step 4: Restart ZCode (manual step — ask user to do this)**

Tell the user: "Please restart ZCode for the plugin to be picked up. Then run `/mr` to verify the command is available."

- [ ] **Step 5: Verify `/mr` appears in ZCode**

After user restarts, they should be able to type `/mr` in ZCode and see the command autocomplete / run.

---

## Task 11: Full README + final commit

**Files:**
- Modify: `README.md` (replace stub from Task 0)

- [ ] **Step 1: Write full README.md**

````markdown
# model-router

A ZCode plugin to route coding tasks to external models: **GLM (Z.ai)**, **DeepSeek**, and **Kimi (Moonshot)** — from inside ZCode via the `/mr` command.

## Why?

Your ZCode main agent might be GLM, but sometimes you want a second opinion from DeepSeek, or Kimi's strength on a specific task. `model-router` lets you ping any of the three on demand — without switching tools or editing ZCode's main config.

## Quick start

```bash
# 1. Clone the repo into the ZCode plugins dir
git clone git@github.com:Thanhtran-165/model-router.git ~/.zcode/plugins/model-router

# 2. Restart ZCode (so the plugin is discovered)

# 3. Inside ZCode, configure your API keys:
/mr setup
```

The setup wizard will prompt for each provider's API key and verify it works.

## Usage

```text
/mr deepseek "refactor auth.py for clarity"
/mr glm "write tests for utils.py"
/mr kimi "review this diff"
/mr list                  # see which providers are configured
/mr setup deepseek        # reconfigure one provider's key
/mr                       # show help
```

## Where are my API keys stored?

In `~/.zcode/model-router/config.json` with file mode `0600` (owner-read-write only).

**They are NEVER committed to git.** The repo ships with `config.example.json` as a template; your real config lives outside the repo.

If you accidentally expose a key:
1. Revoke it immediately at the provider's dashboard (Z.ai / DeepSeek / Moonshot).
2. Run `/mr setup <provider>` to enter a fresh key.

## Supported providers

| Slug      | Provider        | Endpoint                              | Default model |
|-----------|-----------------|---------------------------------------|---------------|
| `glm`     | Z.ai            | `https://api.z.ai/api/anthropic`      | `glm-4.6`     |
| `deepseek`| DeepSeek        | `https://api.deepseek.com/anthropic`  | `deepseek-chat` |
| `kimi`    | Moonshot        | `https://api.moonshot.ai/anthropic`   | `kimi-k2`     |

All three expose Anthropic-compatible endpoints, so this plugin uses a single HTTP client (Anthropic Messages API format).

## How it works

1. `/mr <provider> "<task>"` → `model_router.router` parses args.
2. Loads `~/.zcode/model-router/config.json`.
3. Sends an Anthropic Messages API request to the provider's endpoint.
4. Relays the model's response back into the ZCode chat.

No external dependencies — pure Python 3 stdlib.

## Development

```bash
git clone git@github.com:Thanhtran-165/model-router.git
cd model-router
python3 -m pytest -v
```

### Layout

```
model-router/
├── plugin.json              # ZCode plugin metadata
├── commands/mr.md           # /mr command definition
├── config.example.json      # template (committed, no keys)
├── src/model_router/        # the Python package
│   ├── router.py            # CLI entrypoint
│   ├── config.py            # load/save user config
│   ├── providers.py         # 3 default providers
│   ├── http_client.py       # Anthropic-compat HTTP
│   ├── errors.py            # typed errors
│   ├── setup_wizard.py      # interactive setup
│   ├── verify_key.py        # key verification
│   └── list_providers.py    # /mr list
└── tests/                   # pytest suite
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `✗ Provider 'X' is not configured` | `/mr setup X` |
| `✗ ... rejected the API key (HTTP 401/403)` | `/mr setup X` with a valid key |
| `✗ ... rate-limited (HTTP 429)` | Wait ~60s and retry |
| `/mr` not found in ZCode | Restart ZCode; check `~/.zcode/plugins/model-router/plugin.json` exists |
| Config file missing | Run `/mr setup` — it creates the file |

## License

MIT
````

- [ ] **Step 2: Update `plugin.json` to v1.0.0 (already v1.0.0, no change needed — verify only)**

```bash
cat /Users/bobo/ZCodeProject/model-router/plugin.json | grep version
```

Expected: `"version": "1.0.0"`.

- [ ] **Step 3: Run full test suite**

```bash
cd /Users/bobo/ZCodeProject/model-router && python3 -m pytest -v
```

Expected: all tests pass (12 + 7 + 8 + 13 + 3 + 6 + 5 + 12 = 66 tests).

- [ ] **Step 4: Commit + push final**

```bash
cd /Users/bobo/ZCodeProject/model-router
git add README.md
git commit -m "docs(readme): full install + usage + troubleshooting guide"
git push origin main
```

- [ ] **Step 5: Tag v1.0.0**

```bash
cd /Users/bobo/ZCodeProject/model-router
git tag -a v1.0.0 -m "v1.0.0: initial release — /mr command with GLM/DeepSeek/Kimi"
git push origin v1.0.0
```

---

## Spec coverage check (self-review)

Mapping every spec requirement to a task:

| Spec requirement | Task |
|------------------|------|
| R1: `/mr <provider> "<task>"` | Task 8 (router) + Task 9 (command) |
| R2: `/mr setup` (no provider) | Task 6 (wizard) + Task 8 |
| R3: `/mr setup <provider>` | Task 6 + Task 8 |
| R4: `/mr list` | Task 7 + Task 8 |
| R5: `/mr` shows help | Task 8 (`print_help`) |
| R6: Auto-trigger via description | Task 9 (description frontmatter) |
| R7: Keys never in git | Task 0 (`.gitignore`) + Task 3 (chmod 600) |
| N1: <2s overhead | Achieved by design (no SDK load) |
| N2: <2min setup | Achieved by wizard (Task 6) |
| N3: Independent of main model | Achieved (HTTP calls, no ZCode model binding) |
| N4: Stdlib only | Achieved (verified in Task 4) |
| Error handling §7 | Task 1 (errors) + Task 4 (http_client) + Task 8 (router catch) |
| Testing §8 | Each task has unit tests; Task 11 step 3 runs full suite |
| Security §6 | Task 0 gitignore + Task 3 chmod 600 + Task 6 getpass |

**Gaps found:** None. All requirements covered.

**Type consistency check:** `VerifyResult`, `call_provider` return dict keys (`text`, `input_tokens`, `output_tokens`), `dispatch(argv)` signature, `run_setup(target=...)` — all consistent across tasks.

---

## Plan complete

Plan saved to: `docs/superpowers/plans/2026-07-18-model-router.md`

Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** — Execute tasks in this session, batch execution with checkpoints for review.

Which approach?
