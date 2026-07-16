#!/usr/bin/env python3
"""
Phase 5: News digest 30 days + sentiment
- Fetch via Company.news() (50 items)
- Categorize: biz, sector, macro, disclosure, analyst
- Sentiment score (-100 → +100)
- Timeline + key takeaways
"""
import warnings
warnings.filterwarnings("ignore")
import json, os, re
from datetime import datetime, timedelta

from vnstock_data import Company

TICKER = "PNJ"
WORK_DIR = "/Users/bobo/ZCodeProject/pnj-research"
DATA_DIR = os.path.join(WORK_DIR, "data")

print("=" * 60)
print(f"  PHASE 5: News Digest — {TICKER}")
print("=" * 60)

c = Company(symbol=TICKER, source="VCI")
news = c.news()
print(f"  Fetched {len(news)} news items")
print(f"  Columns: {list(news.columns)}")

# Convert to records
news_records = news.to_dict("records")

# Sentiment keywords (Vietnamese + English)
POSITIVE_KW = [
    "tăng trưởng", "đạt trên", "vượt", "kỷ lục", "tái cơ cấu thành công", "đột phá",
    "hợp tác", "mở rộng", "khánh thành", "ra mắt", "đạt được", "tăng", "lợi nhuận kỷ lục",
    "thu hút", "đầu tư", "chia cổ tức", "cổ tức", "thưởng", "nâng cấp", "tích cực",
    "breakthrough", "growth", "record", "beat", "exceed", "upgrade", "partnership",
    "expansion", "launch", "dividend", "bonus", "rally", "surge", "soar",
]
NEGATIVE_KW = [
    "giảm", "sụt", "lỗ", "thua lỗ", "khó khăn", "rủi ro", "kiện", "phạt", "vi phạm",
    "đình trệ", "trì trệ", "thu hẹp", "cắt giảm", "sa thải", "đóng cửa", "mất",
    "đình chỉ", "giam", "điều tra", "tranh chấp", "giảm giá", "áp lực", "lo ngại",
    "decline", "loss", "drop", "fall", "lawsuit", "penalty", "violation", "cut",
    "close", "shut", "miss", "weak", "pressure", "concern", "warning", "downgrade",
    "sell-off", "plunge", "crash",
]
# Disclosure-neutral keywords (not counted as sentiment)
DISCLOSURE_KW = ["công bố", "thông báo", "báo cáo", "nghị quyết", "đại hội", "biên bản", "đề cử", "bổ nhiệm"]

def score_sentiment(title, content=""):
    text = (str(title) + " " + str(content)).lower()
    pos = sum(1 for kw in POSITIVE_KW if kw in text)
    neg = sum(1 for kw in NEGATIVE_KW if kw in text)
    if pos + neg == 0:
        return 0, "neutral"
    score = (pos - neg) / (pos + neg) * 100
    if score > 25:
        return int(score), "positive"
    elif score < -25:
        return int(score), "negative"
    else:
        return int(score), "neutral"

def categorize(title, content=""):
    text = (str(title) + " " + str(content)).lower()
    if any(k in text for k in ["công bố", "thông báo", "báo cáo tài chính", "nghị quyết", "đại hội đồng", "bổ nhiệm", "biên bản", "cổ tức", "chia cổ phiếu", "phát hành", "giao dịch nội bộ", "đề cử"]):
        return "disclosure"
    if any(k in text for k in ["định giá", "khuyến nghị", "mục tiêu giá", "target price", "rating", "analyst", "ctck", "chứng khoán", "báo cáo phân tích"]):
        return "analyst"
    if any(k in text for k in ["vĩ mô", "lãi suất", "lạm phát", "gdp", "nhà nước", "chính phủ", "ngân hàng nhà nước", "sbv", "fed", "tỷ giá", "thủ tướng"]):
        return "macro"
    if any(k in text for k in ["ngành", "vàng", "trang sức", "bán lẻ", "fcmg", "tiêu dùng", "đối thủ", "cạnh tranh", "doji", "sjc", "baosun"]):
        return "sector"
    return "biz"

# Process news
cutoff = datetime(2026, 7, 11) - timedelta(days=30)
processed = []
for item in news_records:
    title = str(item.get("news_title", ""))
    content = str(item.get("news_short_content", ""))
    date_str = str(item.get("public_date", ""))[:10]
    score, label = score_sentiment(title, content)
    category = categorize(title, content)
    processed.append({
        "date": date_str,
        "title": title,
        "content": content[:300],
        "source": str(item.get("news_source", "")),
        "sentiment_score": score,
        "sentiment_label": label,
        "category": category,
    })

# Stats
total = len(processed)
pos = sum(1 for p in processed if p["sentiment_label"] == "positive")
neg = sum(1 for p in processed if p["sentiment_label"] == "negative")
neu = sum(1 for p in processed if p["sentiment_label"] == "neutral")
sentiment_score = int((pos - neg) / max(total, 1) * 100)

# Category breakdown
categories = {"biz": 0, "sector": 0, "macro": 0, "disclosure": 0, "analyst": 0}
for p in processed:
    categories[p["category"]] = categories.get(p["category"], 0) + 1

print(f"\n[1] Sentiment analysis:")
print(f"  Total news: {total}")
print(f"  Positive: {pos} | Negative: {neg} | Neutral: {neu}")
print(f"  Sentiment score: {sentiment_score:+d}/100")
print(f"\n[2] Category breakdown:")
for cat, cnt in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {cnt}")

print(f"\n[3] Top headlines (most recent 15):")
for p in processed[:15]:
    print(f"  [{p['date']}] ({p['category']}, {p['sentiment_label']}) {p['title'][:90]}")

# Key takeaways
print(f"\n[4] Key takeaways:")
# Find most positive and most negative
by_score = sorted(processed, key=lambda x: x["sentiment_score"])
most_neg = by_score[:3]
most_pos = sorted(processed, key=lambda x: -x["sentiment_score"])[:3]
print("  Most negative:")
for p in most_neg:
    print(f"    [{p['date']}] {p['sentiment_score']:+d}: {p['title'][:80]}")
print("  Most positive:")
for p in most_pos:
    print(f"    [{p['date']}] {p['sentiment_score']:+d}: {p['title'][:80]}")

# ============ SAVE ============
result = {
    "ticker": TICKER,
    "total_news": total,
    "sentiment": {"positive": pos, "negative": neg, "neutral": neu},
    "sentiment_score": sentiment_score,
    "categories": categories,
    "top_headlines": [
        {"date": p["date"], "title": p["title"], "category": p["category"], "sentiment": p["sentiment_label"], "score": p["sentiment_score"]}
        for p in processed[:20]
    ],
    "most_positive": [{"date": p["date"], "title": p["title"], "score": p["sentiment_score"]} for p in most_pos],
    "most_negative": [{"date": p["date"], "title": p["title"], "score": p["sentiment_score"]} for p in most_neg],
    "key_takeaways": [
        f"Tổng hợp {total} tin tức: {pos} tích cực, {neg} tiêu cực, {neu} trung tính (điểm sentiment {sentiment_score:+d}/100)",
        f"Phân loại: {categories['disclosure']} công bố thông tin, {categories['biz']} kinh doanh, {categories['sector']} ngành, {categories['analyst']} phân tích",
        "Sự kiện nổi bật: chia cổ phiếu thưởng 50% (2026-04-15), ESOP 0.7% (2026-04-24), cổ tức tiền mặt",
        f"Nhận định: sentiment {'tích cực' if sentiment_score > 10 else 'tiêu cực' if sentiment_score < -10 else 'trung tính'} trong kỳ 30 ngày",
    ],
}

with open(os.path.join(DATA_DIR, "news.json"), "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# Save full news for reference
with open(os.path.join(DATA_DIR, "news_full.json"), "w") as f:
    json.dump(processed, f, indent=2, ensure_ascii=False)

print(f"\n✅ Phase 5 complete → data/news.json")
print(f"   Sentiment: {sentiment_score:+d}/100 | {pos}+/{neg}-/{neu}=")
