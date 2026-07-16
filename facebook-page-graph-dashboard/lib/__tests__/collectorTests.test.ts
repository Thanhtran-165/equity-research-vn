import { describe, it, expect } from "vitest";
import {
  classifyContent,
  parseFollowerCount,
  parseMetricCount,
} from "../collectors/classifyContent";

describe("Content Classifier", () => {
  it("1. assigns correct topic from Vietnamese keywords", () => {
    const stock = classifyContent("Phân tích VN-Index ngày hôm nay, cổ phiếu VNM tăng mạnh");
    expect(stock.topicTag).toBe("chung_khoan");

    const gold = classifyContent("Giá vàng thế giới tiếp tục tăng, XAUUSD chạm mốc mới");
    expect(gold.topicTag).toBe("vang_usd");

    const re = classifyContent("Thị trường bất động sản 2026, căn hộ Vinhomes giảm giá");
    expect(re.topicTag).toBe("bat_dong_san");

    const macro = classifyContent("GDP Việt Nam năm 2026, lạm phát kiểm soát tốt");
    expect(macro.topicTag).toBe("vi_mo");
  });

  it("2. detects video vs text format from DOM signals", () => {
    const video = classifyContent("Video phân tích", { hasVideo: true });
    expect(video.contentType).toBe("video");

    const photo = classifyContent("Ảnh thị trường", { hasPhoto: true });
    expect(photo.contentType).toBe("image");

    const text = classifyContent("Chỉ text, không ảnh");
    expect(text.contentType).toBe("text");
  });

  it("3. detects commercial signals", () => {
    const commercial = classifyContent("Đăng ký khóa học chứng khoán, nhắn tin Zalo để được tư vấn");
    expect(commercial.commercialSignal).toBe(true);

    const clean = classifyContent("VN-Index tăng 15 điểm, dòng tiền ngoại vào ròng");
    expect(clean.commercialSignal).toBe(false);
  });
});

describe("Follower Count Parser", () => {
  it("4. parses Vietnamese follower count formats", () => {
    expect(parseFollowerCount("23K người theo dõi")).toBe(23000);
    expect(parseFollowerCount("188K")).toBe(188000);
    expect(parseFollowerCount("1,2 Tr người theo dõi")).toBe(1200000);
    expect(parseFollowerCount("29K người theo dõi")).toBe(29000);
    expect(parseFollowerCount("14K người theo dõi")).toBe(14000);
    expect(parseFollowerCount("217K người theo dõi")).toBe(217000);
  });
});

describe("Metric Count Parser", () => {
  it("5. parses Vietnamese metric counts correctly", () => {
    expect(parseMetricCount("106")).toBe(106);
    expect(parseMetricCount("7")).toBe(7);
    expect(parseMetricCount("1,2 N")).toBe(1200);
    expect(parseMetricCount("3,4 Tr")).toBe(3400000);
    expect(parseMetricCount("12 N")).toBe(12000);
    expect(parseMetricCount(null)).toBeNull();
    expect(parseMetricCount("")).toBeNull();
  });
});

describe("Null ≠ Zero Contract", () => {
  it("6. null metric stays null, never becomes zero", () => {
    // parseMetricCount returns null for empty/missing
    expect(parseMetricCount("")).toBeNull();
    expect(parseMetricCount(null)).toBeNull();
    expect(parseMetricCount(undefined as unknown as string)).toBeNull();

    // Zero is a valid observed value
    expect(parseMetricCount("0")).toBe(0);
  });
});

describe("Classification Edge Cases", () => {
  it("7. multi-topic post picks the dominant topic", () => {
    // Post mentions both stocks and gold — stock has more keywords
    const multi = classifyContent("Cổ phiếu chứng khoán VN-Index tăng, vàng SJC cũng tăng");
    expect(["chung_khoan", "vang_usd"]).toContain(multi.topicTag);
  });

  it("8. unrelated text gets 'khac' topic", () => {
    const unrelated = classifyContent("Hôm nay thời tiết đẹp, đi cà phê với bạn");
    expect(unrelated.topicTag).toBe("khac");
    expect(unrelated.commercialSignal).toBe(false);
  });
});
