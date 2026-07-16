# ASSUMPTIONS — PDF Skill Factory

> Đọc file này đầu tiên trước khi làm bất cứ việc gì trong dự án.
> Mọi quyết định thiết kế đều bắt nguồn từ đây. Nếu phát hiện giả định sai,
> dừng và cập nhật file này trước khi tiếp tục.

## Tên dự án

**PDF Skill Factory — AI-guided AI improvement for PDF understanding**

## Luận điểm trung tâm (theo brief gốc)

Dự án này KHÔNG phải là:

- clone RAGFlow rồi chạy;
- cài Docling/Marker/MinerU rồi đọc PDF;
- dựng hệ thống RAG local;
- làm chatbot hỏi đáp tài liệu đơn thuần;
- build một app local nặng.

Dự án này LÀ:

- học kiến trúc từ các repo mạnh;
- rút pattern thiết kế skill;
- tạo skill instruction riêng (`pdf-evidence`);
- tạo benchmark/eval riêng;
- tạo vòng tự cải thiện;
- version hóa skill;
- để AI sau này tự nâng cấp PDF Skill dựa trên lỗi thực tế.

Mục tiêu cuối cùng: **một cơ chế để AI học cách xử lý PDF tốt hơn qua mỗi lần thất bại.**

## ⚠️ PATCH 7 — Phạm vi cải thiện: KHÔNG fine-tune, KHÔNG train lại model

Dự án này **chỉ cải thiện ở tầng instruction / skill-spec / eval / policy / tool-routing**.

KHÔNG bao gồm:

- Fine-tune model (SFT, RLHF, DPO, v.v.);
- Train lại model từ đầu;
- Sửa trọng số model;
- Distill model;
- Sửa tokenizer hoặc embedding model.

Lý do: ở tầng skill, cải thiện có thể đạt được nhanh, rẻ, có thể hoàn tác, và
không phụ thuộc vào quyền truy cập GPU hay dữ liệu huấn luyện. Đây cũng là phạm vi
mà các repo nền tảng (Voyager, Reflexion, DSPy, GEPA, TextGrad) đã chứng minh hiệu quả.

Toàn bộ "cải thiện" trong dự án này được hiểu là:

- Sửa system prompt / instruction;
- Sửa/thêm policy (citation, evidence, table, legal, financial, OCR, multi-PDF);
- Thêm/bớt sub-skill và thay đổi routing;
- Cải thiện eval metric và benchmark coverage;
- Cập nhật skill memory (lesson learned).

## Giả định kỹ thuật

| # | Giả định | Hệ quả nếu sai |
|---|----------|----------------|
| A1 | Skill `pdf` hiện có ở `~/.zcode/skills/pdf/` phục vụ **tạo/render PDF**, không phải QA evidence-first. | Sẽ cần overhaut skill đó — KHÔNG làm trong dự án này. Skill mới tên `pdf-evidence`. |
| A2 | Parser có sẵn trong môi trường: `pdfplumber`, `pypdf`, `reportlab`. | Nếu thiếu, cài bằng `uv pip install` / `pip install`. |
| A3 | OCR/làm việc với scan PDF (PaddleOCR/Surya) chỉ được **mô tả trong policy**, KHÔNG cài đặt trong v0.1. | Fixture scan sẽ ở dạng "expected behavior" chứ không chạy OCR thật. |
| A4 | Benchmark dùng fixture tự tạo (reportlab sinh text), không tải PDF bản quyền. | Coverage pháp lý/tài chính thực tế còn hạn chế — REVIEW_REPORT.md ghi rõ. |
| A5 | Không cài `dspy`/`gepa`/`textgrad` trong v0.1. Modules chỉ mô tả SIGNATURE dạng text spec. | Loop GEPA thật nằm ở roadmap v0.7+. |
| A6 | Eval dùng metric rule-based (citation format, page-in-evidence, abstention) + 1 LLM-judge (groundedness). | `faithfulness_simple` là baseline heuristic, không phải metric cuối. |
| A7 | Factory là **bản thiết kế + research + scaffolding tối thiểu**, không phải ứng dụng chạy production. | Mọi code ở `scaffolding/` phục vụ demo loop, không phải production-grade. |
| A8 | Skill `pdf-evidence` được lưu ở `~/.zcode/skills/pdf-evidence/` sau khi copy từ `ZCodeProject/pdf-skill-factory/pdf-evidence/`. | Bản trong `ZCodeProject/` là nguồn sự thật; bản ở `~/.zcode/skills/` là bản chạy. |

## Phạm vi version hóa

```
v0.1 — baseline evidence/citation       ← scope dự án này
v0.2 — table extraction rules
v0.3 — legal comparison rules
v0.4 — financial report rules
v0.5 — OCR/scan robustness
v0.6 — multi-PDF synthesis
v0.7 — auto-eval and self-refine (GEPA-style)
v1.0 — stable release
```

Dự án này chỉ deliver **v0.1 baseline** + thiết kế cho v0.2–v1.0.

## Conventions tuân thủ

- `SKILL.md` < 500 dòng (theo skill-creator).
- Frontmatter chỉ `name` + `description`; version nếu có đặt trong `metadata.version`.
- Đẩy detail nặng vào `references/`, không để trong SKILL.md.
- Theo pattern `vn-rates-weekly` cho: workflow N bước, JSON output schema, pitfalls section, CHANGELOG format.
- Tên skill theo kebab-case; thư mục skill khớp tên.

## Ràng buộc chất lượng (brief mục 9)

1. Không viết chung chung.
2. Không chỉ liệt kê repo.
3. Không biến nhiệm vụ thành cài đặt RAGFlow/Dify/AnythingLLM.
4. Không nói "có thể" mà không đưa thiết kế cụ thể.
5. Không chấp nhận skill không có eval.
6. Không chấp nhận output không có citation policy.
7. Không chấp nhận output không có failure loop.
8. Không chấp nhận output không có versioning.
9. Không chấp nhận output không có skill memory.
10. Không chấp nhận output không có regression test.
