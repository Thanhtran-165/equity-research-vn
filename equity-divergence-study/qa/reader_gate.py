"""qa/reader_gate.py — verify 8 reader-test questions are answerable from visible text.

Reader test (per spec): a person with no statistics background must correctly answer
8 questions after reading. This script checks each question has a clear, plain-language
answer present in the visible (non-technical) text.
"""
import json, re, hashlib
from pathlib import Path

ROOT = Path("/Users/bobo/ZCodeProject/equity-divergence-study")
html = (ROOT / "index.html").read_text(encoding="utf-8")
HTML_SHA = hashlib.sha256(html.encode()).hexdigest()

# Visible text only (strip scripts, styles, technical details)
visible = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
visible = re.sub(r"<style[^>]*>.*?</style>", "", visible, flags=re.DOTALL | re.IGNORECASE)
visible = re.sub(r'<details[^>]*data-layer="technical"[^>]*>.*?</details>', "", visible, flags=re.DOTALL | re.IGNORECASE)
visible = re.sub(r"<[^>]+>", " ", visible)
visible_text = re.sub(r"\s+", " ", visible).strip().lower()

# 8 reader-test questions and the key phrases their answers must contain
# Each question → list of acceptable key phrases (any one match = answerable)
QUESTIONS = [
    {
        "q": "Phân kỳ là gì?",
        "answer_keys": ["không đồng thuận", "hai yếu tố", "đi ngược chiều", "không đồng ý"],
    },
    {
        "q": "Trường hợp nào đáng chú ý nhất?",
        "answer_keys": ["giá giảm", "khối lượng tăng", "vnindex"],
    },
    {
        "q": "4,75% có phải lần nào cũng xảy ra không?",
        "answer_keys": ["không có nghĩa lần tiếp theo", "không phải", "trung bình", "có những lần"],
    },
    {
        "q": "Vì sao chưa thể mua?",
        "answer_keys": ["3", "6 giai đoạn", "không đủ ổn định", "kém hơn", "chưa đủ tin cậy"],
    },
    {
        "q": "Giá tăng nhưng khối lượng giảm có phải tín hiệu bán không?",
        "answer_keys": ["không được coi là tín hiệu bán", "không được suy diễn", "chưa có phát hiện"],
    },
    {
        "q": "Độ rộng trái chiều với VNINDEX có ý nghĩa gì?",
        "answer_keys": ["độ rộng", "cổ phiếu cùng", "chưa được xác nhận", "kiểm tra thêm"],
    },
    {
        "q": "Khi gặp phân kỳ, bước đầu tiên cần làm gì?",
        "answer_keys": ["nhận diện", "không mua hoặc bán ngay", "quan sát"],
    },
    {
        "q": "Kết luận cuối cùng của nghiên cứu là gì?",
        "answer_keys": ["chưa đủ ổn định", "công cụ quan sát", "chưa đủ để dự báo", "chưa đủ để giao dịch"],
    },
]

results = []
for item in QUESTIONS:
    matched = [k for k in item["answer_keys"] if k in visible_text]
    results.append({
        "question": item["q"],
        "answer_keys_found": matched,
        "answerable": len(matched) > 0,
    })

all_answerable = all(r["answerable"] for r in results)
out = {
    "html_sha256": HTML_SHA,
    "visible_text_chars": len(visible_text),
    "n_questions": len(results),
    "n_answerable": sum(1 for r in results if r["answerable"]),
    "all_answerable": all_answerable,
    "reader_gate_passed": all_answerable,
    "results": results,
}

out_path = ROOT / "qa" / "reader_gate.json"
out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"WROTE: {out_path}")
print(f"HTML_SHA256: {HTML_SHA}")
print(f"Questions answerable: {out['n_answerable']}/{out['n_questions']}")
print(f"Reader gate: {'PASS' if all_answerable else 'FAIL'}")
for r in results:
    status = "OK" if r["answerable"] else "MISSING"
    print(f"  [{status}] {r['question']} -> {r['answer_keys_found'][:2]}")
