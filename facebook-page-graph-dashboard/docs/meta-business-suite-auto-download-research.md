# Meta Business Suite Auto-Download — Feasibility Research

> Mục tiêu: nghiên cứu khả năng giảm thao tác tải CSV thủ công mà vẫn **an toàn, hợp lệ, không bypass chính sách Meta**.

> ⚠️ Đây là tài liệu research only. Code auto-download CHƯA được implement mặc định. Mọi implementation phải được user duyệt riêng.

---

## 1. Official export / scheduled report

**Trạng thái**: ⚠️ **Not confirmed**.

- Meta Business Suite có nút **Export** thủ công (xem `meta-business-suite-export-research.md`).
- **Không tìm thấy tính năng "scheduled export" hoặc "email report" chính thức** cho Page Insights organic trong Meta Business Suite (tính đến 2026-07).
- Meta Ads Manager có scheduled email report, nhưng đó là cho **Ads**, không phải organic Insights.
- Một số tài khoản Enterprise có thể có "Automated Insights" nhưng không phải export CSV.

**Kết luận**: Không có scheduled export chính thức cho organic Page Insights. Phải tải thủ công.

---

## 2. Graph API fallback (`read_insights`)

**Trạng thái**: ❌ **Blocked bởi Business Verification**.

- Đây là hướng chuẩn để tự động hóa insight.
- Hiện App Review bị chặn vì user là cá nhân, chưa có pháp nhân xác minh.
- Sau khi có Business Verification → request `read_insights` Advanced Access → dùng được `/page-id/insights` và `/post-id/insights`.
- **Phase này không dùng** — đã rõ trong spec.

---

## 3. Browser automation (Playwright/Selenium)

**Trạng thái**: 🚫 **NOT RECOMMENDED FOR NOW — RISKY**.

### Rủi ro nghiêm trọng

| Rủi ro | Mô tả |
|---|---|
| **Violation of Meta ToS** | Meta's Platform Terms + Automated Scraping Terms cấm automation lên giao diện người dùng. |
| **Account ban** | Có thể khóa tài khoản Facebook người dùng vĩnh viễn. |
| **2FA/Captcha** | Cần bypass → vi phạm ngay lập tức. |
| **Cookie/session storage** | Lưu session Meta = lộ thông tin đăng nhập. |
| **DOM thay đổi liên tục** | Meta UI update thường xuyên → script dễ hỏng. |
| **Anti-bot detection** | Meta có hệ thống detect bot mạnh (đã dùng cho Ads fraud). |

### Nếu có implement sau này

Chỉ khi có sự đồng ý rõ ràng của user, trên **browser session cá nhân của chính họ**, không headless, không save cookie/password. Kể cả vậy:

- 🔴 Rủi ro tài khoản bị ban vẫn cao.
- 🔴 Có thể vi phạm Meta Platform Terms Section 4 (Automated Queries).
- 🔴 Có thể vi phạm Meta scrape policies.

**Kết luận**: **KHÔNG implement trong phase này. Chỉ nghiên cứu.**

---

## 4. Semi-automation khuyến nghị ✅

**Đây là hướng ưu tiên, an toàn nhất, đã implement dưới dạng optional script.**

### Workflow

```
1. User mở Meta Business Suite bằng trình duyệt của mình
2. User tự click Export → file download về thư mục Downloads (hoặc thư mục cấu hình)
3. Script watch-meta-exports.ts (optional) detect file mới:
   - Match pattern: *.csv, *.xlsx, có chứa "insights"/"facebook"/"meta"
   - Chờ file size ổn định 5-10 giây (download xong)
   - Copy vào /imports/incoming hoặc gọi local API import
4. App tự parse + preview + mapping
5. User confirm mapping trong /imports
```

### Đặc điểm

| Thuộc tính | Giá trị |
|---|---|
| **User-driven** | ✅ User chủ động export, không bị ép |
| **No login** | ✅ Không động vào session Meta |
| **No scrape** | ✅ Không parse giao diện Meta |
| **No 2FA bypass** | ✅ Không bao giờ đụng tới auth |
| **No cookie storage** | ✅ Script chỉ xem filesystem |
| **Reduced friction** | ✅ Bỏ bước upload manual |
| **Tự config** | `META_EXPORTS_WATCH_DIR=/Users/bobo/Downloads` |
| **Off by default** | `META_EXPORTS_AUTO_IMPORT=false` |

### Env vars

```bash
META_EXPORTS_WATCH_DIR=         # path tới thư mục cần theo dõi (mặc định: ~/Downloads)
META_EXPORTS_AUTO_IMPORT=false  # true = import ngay sau detect; false = chỉ copy vào /imports/incoming
```

---

## 5. Gmail / Email import (nếu có scheduled report)

**Trạng thái**: ❌ **Not implementable now**.

- Phần 1 đã kết luận: **Meta chưa có scheduled email report cho organic Page Insights**.
- Nếu sau này Meta thêm tính năng này:
  - Cần xin user cấp quyền Gmail rõ ràng (OAuth scope `gmail.readonly`).
  - Đọc attachment từ email sender `@facebookmail.com`.
  - Filter theo subject line chứa "Insights report" / "Báo cáo Insights".
  - Parse attachment bằng cùng pipeline CSV/XLSX.

**Kết luận**: Không feasible ở hiện tại.

---

## 6. Feasibility Matrix

| Method | Automation level | Compliance risk | Engineering complexity | Reliability | Recommendation |
|---|---|---|---|---|---|
| **Manual upload** | None | ✅ None | ✅ Low | ✅ High (user-driven) | **✅ Recommended now** |
| **Watched Downloads folder** | Semi (file detection) | ✅ None | 🟡 Medium (filesystem watch) | ✅ High | **✅ Recommended for local convenience** |
| **Scheduled email import** | High | 🟡 Conditional (need Gmail OAuth) | 🟡 Medium | 🟡 Depends on Meta feature | 🟡 Conditional (chờ Meta hỗ trợ) |
| **Browser automation** | Very High | 🔴 High (TOS + ban risk) | 🔴 High (maintenance) | 🔴 Low (DOM changes) | 🔴 **NOT recommended now** |
| **Graph API `read_insights`** | Very High | ✅ None | ✅ Low | ✅ High | 🟢 **Future — chờ Business Verification** |

---

## 7. Kết luận

1. **Manual upload**: giữ làm mặc định, đã có ở `/imports`.
2. **Watched Downloads folder**: implement optional script `scripts/watch-meta-exports.ts` (off by default).
3. **Scheduled email import**: chờ Meta hỗ trợ — không làm bây giờ.
4. **Browser automation**: **KHÔNG làm**. Rủi ro cao, vi phạm ToS.
5. **Graph API `read_insights`**: là endgame khi có Business Verification, không cần trong phase này.

### Nguyên tắc an toàn được áp dụng

- ✅ Không tự động login Meta.
- ✅ Không dùng username/password.
- ✅ Không lưu cookie/session của Meta.
- ✅ Không bypass 2FA/captcha.
- ✅ Không scrape giao diện Meta Business Suite.
- ✅ Không chạy Playwright/Selenium để tải CSV.
- ✅ Không giả lập user behavior để né kiểm soát.
- ✅ Chỉ xử lý file mà **user đã tự tải về**.
