// src/data/i18n.mjs
// Bilingual UI strings. Vietnamese first (default), English second.
// Used by both client (via LangProvider t()) and server (via pick()).

export const DICTIONARY = {
  // Brand & nav
  brand: { vi: "Déjà Vu 1970–1980?", en: "Déjà Vu 1970–1980?" },
  nav_overview: { vi: "Tổng quan", en: "Overview" },
  nav_timeline: { vi: "Timeline", en: "Timeline" },
  nav_scorecard: { vi: "Bảng điểm", en: "Scorecard" },
  nav_commodities: { vi: "Hàng hóa", en: "Commodities" },
  nav_chapters: { vi: "Chương", en: "Chapters" },
  nav_sources: { vi: "Nguồn", en: "Sources" },
  nav_about: { vi: "Phương pháp", en: "Method" },

  // Theme/lang toggle
  theme_dark: { vi: "🌙 Tối", en: "🌙 Dark" },
  theme_light: { vi: "☀️ Sáng", en: "☀️ Light" },

  // Hero homepage
  hero_eyebrow: { vi: "Nghiên cứu vĩ mô lịch sử · v1.0 · cập nhật", en: "Macro-historical research · v1.0 · updated" },
  hero_title: { vi: "Déjà Vu 1970–1980?", en: "Déjà Vu 1970–1980?" },
  hero_sub: {
    vi: "So sánh định lượng, dựa trên bằng chứng giữa chế độ kinh tế-tài chính 1965–1985 và 2020–hiện tại. 16 chiều. Hơn 12 hàng hóa. Hơn 40 biểu đồ. Không phải dự báo — là phép so sánh trung thực.",
    en: "A quantitative, evidence-linked comparison between the 1965–1985 economic-financial regime and 2020–present. Sixteen dimensions. Twelve-plus commodities. Forty-plus charts. Not a forecast — an honest analogy.",
  },
  hero_thesis_label: { vi: "Luận đề.", en: "Thesis." },
  hero_thesis: {
    vi: "Hiện tại gợi nhớ chế độ 1970–1980 theo nhiều cách — xung đột địa chính trị, rủi ro năng lượng, lạm phát dai dẳng, chính sách tiền tệ khó nới lỏng, tái cấu trúc hệ thống tiền tệ, hàng hóa chiến lược và một cuộc cách mạng năng suất đang hình thành. Nhưng nợ công cao hơn, tài chính hóa sâu hơn, vị thế năng lượng Mỹ thay đổi, vai trò của Trung Quốc, cấu trúc toàn cầu hóa mới, yen carry trade và sự trỗi dậy của AI có thể khiến kết quả khác xa lịch sử. ",
    en: "The present evokes the 1970–1980 regime in many ways — geopolitical conflict, energy risk, persistent inflation, hard-to-loosen monetary policy, a reshuffling of the monetary system, strategic commodities, and a nascent productivity revolution. But higher public debt, deeper financialization, a changed US energy position, the role of China, the structure of globalization, the yen carry trade, and the rise of AI may push the outcome far from history. ",
  },
  hero_thesis_emph: {
    vi: "Lịch sử gieo vần — không nhất thiết lặp lại.",
    en: "History rhymes — it does not necessarily repeat.",
  },

  // At a glance section
  glance_title: { vi: "Tóm tắt nhanh", en: "At a glance" },
  glance_score_label: { vi: "Điểm Déjà Vu (TB / 5)", en: "Déjà Vu score (avg / 5)" },
  glance_score_note: { vi: "trên 16 chiều · trọng số 0.2P / 0.3S / 0.3M / 0.2O", en: "across 16 dimensions · weighted 0.2P / 0.3S / 0.3M / 0.2O" },
  glance_strong_label: { vi: "Tương đồng mạnh", en: "Strongest echoes" },
  glance_strong_note: { vi: "chiều mà phép so sánh giữ được cấu trúc", en: "dimensions where analogy holds structurally" },
  glance_div_label: { vi: "Chiều khác biệt", en: "Divergent dimensions" },
  glance_div_note: { vi: "nơi phép so sánh phá vỡ", en: "where the analogy breaks" },
  glance_comm_label: { vi: "Hàng hóa đã chấm", en: "Commodities scored" },
  glance_comm_note: { vi: "nhóm năng lượng / kim loại / hạt nhân / nông nghiệp", en: "across energy / metals / nuclear / agri" },

  // Scorecard labels
  pill_strong: { vi: "Tương đồng mạnh", en: "Strong similarity" },
  pill_medium: { vi: "Tương đồng trung bình", en: "Medium similarity" },
  pill_weak: { vi: "Tương đồng yếu", en: "Weak similarity" },
  pill_surface: { vi: "Tương đồng bề mặt", en: "Surface similarity" },
  pill_divergent: { vi: "Khác biệt chi phối", en: "Differences dominate" },
  pill_insufficient: { vi: "Không đủ bằng chứng", en: "Insufficient evidence" },

  confidence: { vi: "Độ tin cậy", en: "Confidence" },
  high: { vi: "Cao", en: "High" },
  medium: { vi: "Trung bình", en: "Medium" },
  low: { vi: "Thấp", en: "Low" },

  // Verdict verdict mapping (for scorecard storage values -> display)
  verdict_strong: { vi: "Tương đồng mạnh", en: "Strong similarity" },
  verdict_medium: { vi: "Tương đồng trung bình", en: "Medium similarity" },
  verdict_weak: { vi: "Tương đồng yếu", en: "Weak similarity" },
  verdict_surface: { vi: "Tương đồng bề mặt", en: "Surface similarity" },
  verdict_divergent: { vi: "Khác biệt chi phối", en: "Differences dominate" },
  verdict_insufficient: { vi: "Không đủ bằng chứng", en: "Insufficient evidence" },

  // Common chapter parts
  part_question: { vi: "Câu hỏi", en: "Question" },
  part_history: { vi: "Bối cảnh lịch sử", en: "Historical context" },
  part_now: { vi: "Bối cảnh hiện tại", en: "Current context" },
  part_same: { vi: "Điểm giống", en: "Similarities" },
  part_diff: { vi: "Điểm khác", en: "Differences" },
  part_data: { vi: "Dữ liệu", en: "Data" },
  part_rebuttal: { vi: "Phản biện", en: "Rebuttal" },
  part_concl: { vi: "Kết luận", en: "Conclusion" },
  part_inv: { vi: "Ý nghĩa đầu tư", en: "Investment relevance" },
  part_conf: { vi: "Độ tin cậy", en: "Confidence" },

  // Footer
  footer_tagline: {
    vi: "— research microsite. So sánh lịch sử định lượng, không phải lời khuyên đầu tư hay dự báo. Xem ",
    en: "— research microsite. Quantitative historical analogy, not investment advice or forecast. See ",
  },
  footer_sources_label: { vi: "phương pháp & giới hạn", en: "methodology & limitations" },
  footer_sources_pre: {
    vi: "Nguồn sơ cấp: FRED (Federal Reserve Economic Data, St. Louis Fed) · World Bank Commodity Price Data (Pink Sheet) · Robert Shiller Online Data (Yale) · World Bank WDI. ",
    en: "Primary sources: FRED (Federal Reserve Economic Data, St. Louis Fed) · World Bank Commodity Price Data (Pink Sheet) · Robert Shiller Online Data (Yale) · World Bank WDI. ",
  },
  footer_sources_link: { vi: "Đầy đủ nguồn →", en: "Full source registry →" },

  // Common
  source_label: { vi: "Nguồn", en: "Source" },
  updated_label: { vi: "Cập nhật", en: "Updated" },
  insufficient_data: { vi: "Không đủ dữ liệu sơ cấp — thiếu nguồn chính.", en: "Insufficient primary data — no usable source." },
  derived: { vi: "tính toán", en: "derived" },
  insufficient: { vi: "thiếu", en: "insufficient" },
  ok: { vi: "OK", en: "OK" },
  back_to_chapters: { vi: "← Tất cả chương", en: "← All chapters" },
  tests: { vi: "Kiểm định", en: "Tests" },
  chapter_word: { vi: "Chương", en: "Chapter" },

  // Generic labels
  trigger: { vi: "Điều kiện kích hoạt", en: "Trigger" },
  confirmation: { vi: "Tín hiệu xác nhận", en: "Confirmation" },
  invalidation: { vi: "Tín hiệu bác bỏ", en: "Invalidation" },
  asset_sensitivity: { vi: "Độ nhạy tài sản", en: "Asset sensitivity" },
  historical_analogue: { vi: "Tương đồng lịch sử", en: "Historical analogue" },
  confidence_label: { vi: "Độ tin cậy", en: "Confidence" },
};

// Quick helper for server components: get current lang from cookie (default vi).
export function langFromHeaders(headers) {
  try {
    const ck = headers?.get?.("cookie") || "";
    const m = ck.match(/dejavu-lang=(vi|en)/);
    return m ? m[1] : "vi";
  } catch { return "vi"; }
}
