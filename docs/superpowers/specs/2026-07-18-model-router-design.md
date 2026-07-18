# Design Spec: `model-router` Plugin

**Ngày:** 2026-07-18
**Tác giả:** Bo Bo (phối hợp ZCode)
**Remote:** `git@github.com:Thanhtran-165/model-router.git`
**Trạng thái:** Chờ user review

---

## 1. Mục đích (Purpose)

Plugin `model-router` cho phép người dùng ZCode gọi **3 model ngoài** (GLM, DeepSeek, Kimi) bằng lệnh thủ công `/mr`, bất kể main model hiện tại là gì. Người dùng **chỉ định tay** model nào sẽ xử lý task nào.

**Không phải là:**
- Orchestrator tự phân vai (user tự chọn model)
- Pipeline chain nhiều bước (one-shot task)
- Multi-agent song song (single-task per invocation)

## 2. Yêu cầu (Requirements)

### Functional
- **R1.** Lệnh `/mr <provider> "<task>"` gửi task tới provider được chọn, trả kết quả về.
- **R2.** Lệnh `/mr setup` (không provider) khởi động setup wizard cho lần đầu.
- **R3.** Lệnh `/mr setup <provider>` re-config 1 provider cụ thể.
- **R4.** Lệnh `/mr list` liệt kê các provider đã config + trạng thái (verified/unverified).
- **R5.** Lệnh `/mr` (không args) hiển thị hướng dẫn sử dụng.
- **R6.** Plugin tự động kích hoạt (auto-trigger) theo ngữ cảnh thông qua `description` trong command frontmatter — main agent ZCode sẽ dispatch khi user yêu cầu task có fit với 1 model cụ thể.
- **R7.** API key KHÔNG bao giờ commit lên git.

### Non-functional
- **N1.** Latency: < 2s overhead ngoài thời gian response của provider.
- **N2.** Setup wizard hoàn thành trong < 2 phút.
- **N3.** Plugin hoạt động độc lập với main model của ZCode.
- **N4.** Code Python thuần, không dependency ngoài stdlib (tránh xung đột môi trường).

## 3. Phạm vi (Scope)

### In scope (v1)
- 3 provider hard-coded trong config template: GLM, DeepSeek, Kimi.
- 4 lệnh: `/mr`, `/mr setup`, `/mr setup <provider>`, `/mr list`.
- HTTP routing tới Anthropic-compatible endpoint.
- Setup wizard interactive.
- Verify key bằng request ping.
- Error handling cho các case phổ biến (401, network, timeout).

### Out of scope (deferred)
- Thêm provider mới ngoài 3 (cần sửa config template).
- Pipeline chain nhiều model (`/mr deepseek "..." --then kimi "..."`).
- Caching response.
- Streaming output (chỉ non-streaming ở v1).
- Parallel multi-model call.
- Token/cost tracking.

## 4. Kiến trúc (Architecture)

### 4.1. Thành phần

```
┌──────────────────────────────────────────────────────────┐
│  ZCode Main Agent (GLM-5.2 hoặc bất kỳ)                  │
│                                                          │
│  User gõ: /mr deepseek "refactor X"                      │
│         ↓                                                │
│  Plugin command /mr được invoke                          │
│         ↓                                                │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────┐
│  scripts/router.py                                       │
│  - Parse args: provider, task                            │
│  - Load config từ ~/.zcode/model-router/config.json      │
│  - Gọi scripts/call_provider.py                          │
│  - Return response                                       │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ↓
┌──────────────────────────────────────────────────────────┐
│  HTTP POST → provider baseURL                            │
│  GLM:      https://api.z.ai/api/anthropic/v1/messages    │
│  DeepSeek: https://api.deepseek.com/anthropic/v1/messages│
│  Kimi:     https://api.moonshot.ai/anthropic/v1/messages │
└──────────────────────────────────────────────────────────┘
```

### 4.2. Cấu trúc file repo (commit lên GitHub — không có key)

```
model-router/
├── plugin.json                        ← khai báo plugin metadata
├── README.md                          ← hướng dẫn cài đặt + sử dụng
├── .gitignore                         ← loại trừ file có key
├── commands/
│   ├── mr.md                          ← lệnh /mr (main)
│   └── mr-setup.md                    ← lệnh /mr setup (alias)
├── scripts/
│   ├── router.py                      ← entry point, parse args + dispatch
│   ├── call_provider.py               ← HTTP call tới Anthropic-compat endpoint
│   ├── setup_wizard.py                ← interactive setup
│   ├── verify_key.py                  ← test 1 key bằng ping request
│   └── list_providers.py              ← liệt kê + trạng thái
└── config.example.json                ← template (commit, không có key)
```

### 4.3. Cấu trúc file trên máy user (ngoài git — có key)

```
~/.zcode/model-router/
└── config.json                        ← file thật, có key, KHÔNG commit
```

### 4.4. Nội dung các file config

#### `config.example.json` (commit lên GitHub)

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

#### `~/.zcode/model-router/config.json` (chỉ trên máy user)

Giống `config.example.json` nhưng `apiKey` là key thật, `verified: true` sau khi setup wizard hoàn thành.

## 5. Luồng người dùng (User Flows)

### 5.1. Setup lần đầu

```
User: /mr setup

Plugin:
  Model Router Setup
  ==================
  
  Tôi sẽ cấu hình 3 nhà cung cấp model:
    1. GLM (Z.ai)        → https://api.z.ai/api/anthropic
    2. DeepSeek          → https://api.deepseek.com/anthropic
    3. Kimi (Moonshot)   → https://api.moonshot.ai/anthropic
  
  --- Provider 1/3: GLM (Z.ai) ---
  Bạn có API key cho GLM không? (y/n/skip-all): y
  Paste key (sẽ không hiển thị): ********
  Đang test... ✓ Key hợp lệ
  
  --- Provider 2/3: DeepSeek ---
  Bạn có API key cho DeepSeek không? (y/n): y
  Paste key: ********
  Đang test... ✓ Key hợp lệ
  
  --- Provider 3/3: Kimi (Moonshot) ---
  Bạn có API key cho Kimi không? (y/n): n
  → Đã skip. Có thể chạy `/mr setup kimi` sau.
  
  ✓ Đã lưu config: ~/.zcode/model-router/config.json
  ✓ 2/3 provider đã verify.
  
  Thử ngay: /mr deepseek "hello, giới thiệu bản thân"
```

### 5.2. Sử dụng hàng ngày

```
User: /mr deepseek "refactor file auth.py cho sạch hơn"

Plugin:
  → Provider: DeepSeek (deepseek-chat)
  → Model endpoint: https://api.deepseek.com/anthropic
  → Sending...
  
  [Response từ DeepSeek, format markdown như bình thường]
  
  → Token usage: input=847, output=1234
  → Time: 4.2s
```

### 5.3. Lỗi xác thực

```
User: /mr kimi "task gì đó"

Plugin:
  ✗ Lỗi: Kimi trả về HTTP 401 (Unauthorized)
  
  Nguyên nhân có thể:
    - API key sai hoặc hết hạn
    - Key không có quyền với model kimi-k2
  
  Khắc phục:
    /mr setup kimi    ← nhập lại key
```

### 5.4. Provider chưa setup

```
User: /mr glm "task gì đó"

Plugin:
  ✗ Provider "glm" chưa được cấu hình.
  
  Chạy: /mr setup glm
  Hoặc setup tất cả: /mr setup
```

### 5.5. Auto-trigger (tự động theo ngữ cảnh)

Main agent ZCode sẽ tự đề xuất dùng plugin khi:
- User nói "dùng deepseek để..." → main agent gợi ý `/mr deepseek "..."`
- User nói "kimi review giúp..." → main agent gợi ý `/mr kimi "..."`

Note: Auto-trigger KHÔNG tự động chạy — chỉ **đề xuất**, user xác nhận mới chạy.

## 6. Bảo mật (Security)

### 6.1. Nguyên tắc
- API key là bí mật cá nhân, KHÔNG BAO GIỜ commit lên git.
- Key chỉ lưu tại `~/.zcode/model-router/config.json`.
- File này permission `600` (rw cho owner only).

### 6.2. `.gitignore` (commit lên repo)

```gitignore
# Config có API key — KHÔNG commit
config.json
*.local.json

# Python
__pycache__/
*.pyc
.venv/

# OS
.DS_Store
```

### 6.3. Setup wizard bảo mật
- Khi user paste key, không echo ra terminal (dùng `getpass`).
- Sau khi lưu, set file permission `chmod 600`.
- Không log key ra stdout/stderr.

### 6.4. Verify key
- Test bằng request thật: `POST /v1/messages` với body `{"messages": [{"role": "user", "content": "ping"}], "max_tokens": 10}`.
- Thành công = HTTP 200 + có response body.
- Thất bại = HTTP 401/403 → báo user nhập lại.

## 7. Error Handling

| Mã lỗi / Tình huống | Hành vi |
|---------------------|---------|
| HTTP 401 Unauthorized | "API key sai/hết hạn. Chạy `/mr setup <provider>`" |
| HTTP 403 Forbidden | "Key không có quyền. Kiểm tra dashboard provider." |
| HTTP 429 Rate limit | "Quá nhiều request. Thử lại sau 60s." |
| HTTP 500/502/503 | "Provider đang lỗi. Thử lại sau." |
| Timeout (>30s) | "Provider không phản hồi. Kiểm tra mạng." |
| Network error | "Không kết nối được. Kiểm tra internet." |
| Config file thiếu | Tự tạo config rỗng, yêu cầu `/mr setup` |
| Provider không tồn tại | "Provider 'xxx' không hỗ trợ. Có sẵn: glm, deepseek, kimi" |
| Task trống | "Vui lòng nhập task. Vd: /mr deepseek \"hello\"" |

## 8. Testing Strategy

### 8.1. Unit test (scripts/test_*.py)
- `test_parse_args`: parse `/mr deepseek "task"` đúng provider + task.
- `test_load_config`: load config thành công, xử lý file thiếu.
- `test_format_request`: format Anthropic-compat body đúng.
- `test_handle_errors`: map HTTP code → message đúng.

### 8.2. Integration test (cần API key thật)
- Setup wizard → verify 3 provider (skip nếu user không có key).
- `/mr <provider> "ping"` → nhận response.
- `/mr list` → hiển thị đúng trạng thái.

### 8.3. Manual smoke test
1. Cài plugin mới → `/mr setup` → nhập 3 key.
2. `/mr list` → thấy 3 provider verified.
3. `/mr deepseek "hello"` → nhận response.
4. Xóa 1 key → `/mr setup deepseek` → re-verify.
5. Đổi key sai → `/mr deepseek "..."` → thấy lỗi 401 rõ ràng.

## 9. Dependencies

### Python stdlib only (không cần pip install):
- `urllib.request` — HTTP calls
- `json` — parse/format JSON
- `os`, `sys` — filesystem, exit codes
- `getpass` — input API key an toàn
- `argparse` — parse command args
- `time` — retry logic

**Lý do:** Tránh xung đột môi trường, cài là chạy được.

## 10. File Structure chi tiết

### `plugin.json`
```json
{
  "name": "model-router",
  "version": "1.0.0",
  "description": "Route tasks tới GLM, DeepSeek, Kimi qua lệnh /mr",
  "author": "Thanhtran-165",
  "homepage": "https://github.com/Thanhtran-165/model-router",
  "commands": ["commands/"],
  "scripts": ["scripts/"]
}
```

### `commands/mr.md` (lệnh chính)
```markdown
---
description: |
  Route một task tới model ngoài (GLM/DeepSeek/Kimi). Dùng khi user muốn 
  dùng model cụ thể cho task cụ thể, ví dụ: "dùng deepseek để refactor", 
  "kimi review code này", "glm viết test". Cú pháp: /mr <provider> "<task>".
  Không args → hiện help. `setup` → wizard config. `list` → liệt kê provider.
---

Thực thi scripts/router.py với args từ user.
```

### `scripts/router.py` (entry point)
```python
#!/usr/bin/env python3
"""Entry point cho /mr command."""
import sys
from call_provider import call_provider
from setup_wizard import run_setup
from list_providers import list_providers

def main():
    args = sys.argv[1:]
    if not args:
        print_help()
        return
    if args[0] == "setup":
        run_setup(args[1:] if len(args) > 1 else None)
    elif args[0] == "list":
        list_providers()
    elif args[0] in ("help", "-h", "--help"):
        print_help()
    else:
        provider = args[0]
        task = " ".join(args[1:]).strip('"').strip("'")
        if not task:
            print(f"✗ Thiếu task. Vd: /mr {provider} \"hello\"")
            return
        call_provider(provider, task)

if __name__ == "__main__":
    main()
```

## 11. Tham chiếu nguồn (Verified Endpoints)

- **GLM (Z.ai) Anthropic endpoint:** `https://api.z.ai/api/anthropic` — đã có trong `~/.zcode/cli/config.json`
- **DeepSeek Anthropic API docs:** https://api-docs.deepseek.com/guides/anthropic_api/ — endpoint `https://api.deepseek.com/anthropic`
- **Kimi (Moonshot) Anthropic endpoint:** `https://api.moonshot.ai/anthropic` — docs: https://platform.kimi.ai/docs/guide/claude-code-kimi

## 12. Câu hỏi mở (Open Questions)

Không có. Tất cả quyết định đã chốt:
- Tên: `model-router` ✓
- Models: GLM + DeepSeek + Kimi ✓
- Cơ chế: HTTP routing tới Anthropic-compat endpoint ✓
- Kích hoạt: lệnh thủ công + auto-trigger gợi ý ✓
- Output: user chỉ định tay model ✓
- Config: Tùy chọn 2 (user-managed, key không commit) ✓

## 13. Quyết định tương lai (Future Decisions)

Sau v1 chạy ổn, có thể cân nhắc:
- **v1.1:** Streaming output (hiển thị response từng chunk).
- **v1.2:** Pipeline chain (`/mr deepseek "..." --then kimi "..."`).
- **v2.0:** Auto-routing theo task type (plugin tự chọn model).
- **v2.0:** Cost/token tracking dashboard.
- **v2.0:** Thêm provider ngoài 3 mặc định qua config động.
