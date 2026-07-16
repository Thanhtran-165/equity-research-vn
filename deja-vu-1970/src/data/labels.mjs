// src/data/labels.mjs — reusable bilingual part labels
export const PART_LABELS = {
  question: { vi: "Câu hỏi", en: "Question" },
  history: { vi: "Bối cảnh lịch sử", en: "Historical context" },
  now: { vi: "Bối cảnh hiện tại", en: "Current context" },
  same: { vi: "Điểm giống", en: "Similarities" },
  diff: { vi: "Điểm khác", en: "Differences" },
  data: { vi: "Dữ liệu", en: "Data" },
  rebuttal: { vi: "Phản biện", en: "Rebuttal" },
  concl: { vi: "Kết luận", en: "Conclusion" },
  inv: { vi: "Ý nghĩa đầu tư", en: "Investment relevance" },
  conf: { vi: "Độ tin cậy", en: "Confidence" },
};

export function lab(key, lang) {
  return PART_LABELS[key]?.[lang] || key;
}
