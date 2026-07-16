/**
 * Build targeted peer expansion files from search agent results.
 *
 * Merges candidates from 3 search agents, dedupes, scores v3,
 * generates: expanded-targeted-candidates.csv, replacement-shortlist.csv,
 * public-benchmark-peer-set-v3-proposed.csv
 */
import { writeFileSync } from "fs";
import { join } from "path";

// ─── Candidate type ─────────────────────────────────────
interface Candidate {
  name: string;
  canonicalUrl: string;
  platform: string;
  objectType: string;
  operatingModel: string;
  category: string;
  subCategory: string;
  activeStatus: string;
  followerCount: number | null;
  audienceCountType: string;
  followerCountAsOf: string;
  lastPostObservedAt: string;
  observedPostCount: number;
  dominantTopics: string;
  dominantFormats: string;
  postingFrequencyEstimate: string;
  brokerageOrCommercialActivity: string;
  topicOverlapScore: number;
  audienceOverlapScore: number;
  formatSimilarityScore: number;
  operatingModelSimilarityScore: number;
  postingFrequencyScore: number;
  publicDataAvailabilityScore: number;
  scaleComparabilityScore: number;
  contentConsistencyScore: number;
  commercialNoiseRiskScore: number;
  identityConfidenceScore: number;
  verificationConfidence: string;
  lastVerifiedAt: string;
  notes: string;
}

function totalFitScoreV3(c: Partial<Candidate>): number {
  return (
    (c.topicOverlapScore ?? 3) * 0.20 +
    (c.audienceOverlapScore ?? 3) * 0.15 +
    (c.formatSimilarityScore ?? 3) * 0.10 +
    (c.operatingModelSimilarityScore ?? 3) * 0.20 +
    (c.postingFrequencyScore ?? 3) * 0.10 +
    (c.publicDataAvailabilityScore ?? 3) * 0.10 +
    (c.scaleComparabilityScore ?? 3) * 0.05 +
    (c.contentConsistencyScore ?? 3) * 0.05 +
    (c.identityConfidenceScore ?? 3) * 0.05 -
    (c.commercialNoiseRiskScore ?? 3) * 0.05
  );
}

function recommendedRole(c: Candidate, fit: number): string {
  // Groups and websites never direct
  if (c.objectType === "facebook_group") return "group_reference";
  if (c.objectType === "website") return "topic_reference";

  // Pure corporate/institutional → topic_reference
  if (c.operatingModel === "corporate_marketing" || c.operatingModel === "institutional_research") return "institutional_reference";
  if (c.operatingModel === "financial_news") return "topic_reference";
  if (c.operatingModel === "community_group") return "group_reference";

  // Core peer requirements
  if (fit >= 3.5 && c.operatingModelSimilarityScore >= 3 && c.topicOverlapScore >= 3 && c.publicDataAvailabilityScore >= 3 && c.activeStatus === "active" && c.verificationConfidence !== "low") {
    if (c.operatingModel.startsWith("stock")) return "direct_core_peer";
    if (c.operatingModel.startsWith("gold") || c.operatingModel.startsWith("commodity")) return "direct_core_peer";
    if (c.operatingModel.startsWith("real_estate")) return "direct_core_peer";
    if (c.operatingModel.startsWith("macro") || c.operatingModel.startsWith("social_finance")) return "direct_core_peer";
  }

  if (fit >= 3.0) return "watchlist";
  return "watchlist";
}

function esc(s: string | number | null | undefined): string {
  if (s == null) return "";
  const str = String(s);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) return `"${str.replace(/"/g, '""')}"`;
  return str;
}

// ─── All candidates from 3 search agents ────────────────
const now = "2026-07-10";
const allRaw: Omit<Candidate, "candidateId" | "totalFitScoreV3" | "recommendedRole">[] & { totalFitScoreV3?: number }[] = [];

// Helper to create candidate with defaults
function c(partial: Partial<Candidate> & { name: string; canonicalUrl: string }): Candidate {
  return {
    platform: "facebook",
    objectType: "facebook_page",
    operatingModel: "other",
    category: "other",
    subCategory: "",
    activeStatus: "active",
    followerCount: null,
    audienceCountType: "followers",
    followerCountAsOf: now,
    lastPostObservedAt: now,
    observedPostCount: 0,
    dominantTopics: "",
    dominantFormats: "",
    postingFrequencyEstimate: "unknown",
    brokerageOrCommercialActivity: "unverified",
    topicOverlapScore: 3,
    audienceOverlapScore: 3,
    formatSimilarityScore: 3,
    operatingModelSimilarityScore: 3,
    postingFrequencyScore: 3,
    publicDataAvailabilityScore: 3,
    scaleComparabilityScore: 3,
    contentConsistencyScore: 3,
    commercialNoiseRiskScore: 2,
    identityConfidenceScore: 3,
    verificationConfidence: "medium",
    lastVerifiedAt: now,
    notes: "",
    ...partial,
  };
}

// ── STOCK BROKERS / KOL / ANALYSTS ──────────────────────
const stockCandidates: Candidate[] = [
  c({ name: "Chứng Khoán 5 phút", canonicalUrl: "https://facebook.com/TuyenDauTu/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", followerCount: 23628, topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "Multi-platform video investor support; 23.6K likes; YouTube 18.7K subs" }),
  c({ name: "SmartF", canonicalUrl: "https://facebook.com/smartf.page/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", followerCount: 91870, topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 3, verificationConfidence: "medium", notes: "In-depth financial/securities analysis; ~91.9K likes; strong video content" }),
  c({ name: "Bò và Gấu", canonicalUrl: "https://facebook.com/bovagau/", objectType: "facebook_page", operatingModel: "social_finance_creator", category: "meme_finance", followerCount: 991000, topicOverlapScore: 3, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 5, publicDataAvailabilityScore: 5, scaleComparabilityScore: 1, commercialNoiseRiskScore: 3, verificationConfidence: "high", notes: "700K-991K followers; DNSE-affiliated; Gen-Z finance entertainment" }),
  c({ name: "Thuận Phái Sinh VN", canonicalUrl: "https://facebook.com/thuanphaisinhvn/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "Derivatives + critical KOL analysis (already in peer set as core_peer)" }),
  c({ name: "Ichimoku Quốc Cường", canonicalUrl: "https://facebook.com/ichimoku.quoccuong/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", followerCount: 188535, topicOverlapScore: 5, audienceOverlapScore: 4, operatingModelSimilarityScore: 5, postingFrequencyScore: 5, publicDataAvailabilityScore: 4, scaleComparabilityScore: 2, verificationConfidence: "high", notes: "~188K likes; ITP co-founder; daily VNIndex livestreams; Ichimoku educator" }),
  c({ name: "Ichimoku Trịnh Phát", canonicalUrl: "https://facebook.com/IchimokuTrinhPhat.ITP/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", topicOverlapScore: 5, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 3, verificationConfidence: "medium", notes: "Ichimoku trading education; sector trends; big money flow analysis" }),
  c({ name: "CLB ICHIMOKU", canonicalUrl: "https://facebook.com/CLB.ICHIMOKU/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", topicOverlapScore: 5, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 3, verificationConfidence: "medium", notes: "Community/club posting daily stock analysis videos" }),
  c({ name: "The Reviewer", canonicalUrl: "https://facebook.com/100090652970156/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", topicOverlapScore: 5, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "In-depth personal stock-analysis videos (NAF, F88, LPBS, HPDE)" }),
  c({ name: "Dòng Tiền Thông Minh", canonicalUrl: "https://facebook.com/100083129686846/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Banking stocks & smart cash flow commentary" }),
  c({ name: "Sơn Chứng Khoán", canonicalUrl: "https://facebook.com/927906937079284", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", topicOverlapScore: 5, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Stock market commentator; persona-style market takes" }),
  c({ name: "Vnstockmarket.com", canonicalUrl: "https://facebook.com/Vnstockmarket.co/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", followerCount: 3181, topicOverlapScore: 5, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 5, verificationConfidence: "medium", notes: "Equity research & valuation models; 3.2K likes" }),
  c({ name: "Daniel Nguyen", canonicalUrl: "https://facebook.com/daniel.nguyen.75491856/", objectType: "facebook_profile", operatingModel: "stock_broker", category: "stock_market", followerCount: 75000, brokerageOrCommercialActivity: "confirmed", topicOverlapScore: 5, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 2, commercialNoiseRiskScore: 4, verificationConfidence: "low", notes: "Runs paid stock room via Zalo; ~75K likes; scam risk — verify credentials" }),
  c({ name: "Soigia82", canonicalUrl: "https://facebook.com/Soigia82/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, commercialNoiseRiskScore: 3, verificationConfidence: "low", notes: "Market commentary (stocks, gold, BTC/XAUUSD) with Zalo room; Hanoi-based" }),
  c({ name: "Chứng Khoán Thực Chiến", canonicalUrl: "https://facebook.com/chungkhoanthucchien.pro/", objectType: "facebook_page", operatingModel: "stock_broker", category: "stock_market", followerCount: 246, topicOverlapScore: 5, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 5, commercialNoiseRiskScore: 3, verificationConfidence: "low", notes: "VNIndex & derivatives analysis; 1:1 free consulting; ~246 likes" }),
  c({ name: "Trinity Securities Group", canonicalUrl: "https://facebook.com/Trinitysecuritiesgroup/", objectType: "facebook_page", operatingModel: "institutional_research", category: "stock_market", topicOverlapScore: 5, audienceOverlapScore: 3, operatingModelSimilarityScore: 2, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 3, verificationConfidence: "medium", notes: "Daily Vietnam market updates; Thai-listed parent; English+Vietnamese content" }),
  c({ name: "Genstock Investing Academy", canonicalUrl: "https://facebook.com/genstock2023/", objectType: "facebook_page", operatingModel: "investment_educator", category: "stock_market", topicOverlapScore: 5, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "Investment academy in Hanoi; MENTOR 1:1 program" }),
  c({ name: "SRTC – Đào tạo nhà đầu tư", canonicalUrl: "https://facebook.com/trungtamnghiencuukhoahocvadaotaochungkhoanSRTC/", objectType: "facebook_page", operatingModel: "investment_educator", category: "stock_market", followerCount: 6215, topicOverlapScore: 5, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "Securities brokerage & advisory training center; Hanoi; 6.2K likes" }),
  c({ name: "START-UP SIC", canonicalUrl: "https://facebook.com/startup.sic/", objectType: "facebook_page", operatingModel: "investment_educator", category: "stock_market", followerCount: 14764, topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 2, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Securities basics courses for students; 14.8K likes" }),
  c({ name: "CFA Community Vietnam", canonicalUrl: "https://facebook.com/CFACommunityVietnam/", objectType: "facebook_page", operatingModel: "investment_educator", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 2, postingFrequencyScore: 2, publicDataAvailabilityScore: 4, scaleComparabilityScore: 3, verificationConfidence: "medium", notes: "CFA members/candidates/experts network; professional community" }),
  c({ name: "Dương Ngọc Trinh (FC)", canonicalUrl: "https://facebook.com/FCDuongNgocTrinh/", objectType: "facebook_page", operatingModel: "stock_creator", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 3, verificationConfidence: "low", notes: "VTV host (VTVMoney) financial-literacy personality; TEDx speaker" }),
  c({ name: "Vietnam Finance Society", canonicalUrl: "https://facebook.com/vfsociety/", objectType: "facebook_page", operatingModel: "investment_educator", category: "stock_market", followerCount: 7301, topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 2, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Community of Vietnamese finance professionals; 7.3K likes" }),
];

// ── GOLD / COMMODITY CREATORS ───────────────────────────
const goldCandidates: Candidate[] = [
  c({ name: "DFF Vietnam (Trần Duy Phương)", canonicalUrl: "https://facebook.com/dffvn.official/", objectType: "facebook_page", operatingModel: "gold_creator", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 3, verificationConfidence: "medium", notes: "Official page of gold expert Trần Duy Phương; gold buy/invest commentary (already in peer set as core_peer)" }),
  c({ name: "Huỳnh Trung Khánh", canonicalUrl: "unverified", objectType: "facebook_profile", operatingModel: "gold_creator", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 2, publicDataAvailabilityScore: 2, scaleComparabilityScore: 2, verificationConfidence: "low", notes: "VGTA Vice Chairman; World Gold Council advisor; FB URL unverified" }),
  c({ name: "King Traders (Hoang Vy Master)", canonicalUrl: "https://facebook.com/thitruongphaisinh/", objectType: "facebook_page", operatingModel: "commodity_creator", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "Gold/XAUUSD trading strategies; Fed rate outlook videos; HCMC" }),
  c({ name: "Hua Cuong (Shane Hua)", canonicalUrl: "https://facebook.com/ShaneHua.Investor/", objectType: "facebook_profile", operatingModel: "commodity_creator", category: "gold_usd", followerCount: 16900, topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "First Vietnamese CEWA-M analyst; daily XAUUSD technical analysis; ~16.9K" }),
  c({ name: "Master Bollinger Bands (Nguyen Phuoc Hai)", canonicalUrl: "https://facebook.com/masterbollingerbands/", objectType: "facebook_page", operatingModel: "commodity_creator", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "Regular 'Phân tích VÀNG - BẠC - DXY' videos" }),
  c({ name: "Nghiêm Duy", canonicalUrl: "https://facebook.com/nghiemduy93/", objectType: "facebook_profile", operatingModel: "gold_creator", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 5, verificationConfidence: "low", notes: "VN vs world gold price-gap analysis videos" }),
  c({ name: "Lão Già Bắt Sóng", canonicalUrl: "https://facebook.com/laogiadautu86", objectType: "facebook_page", operatingModel: "gold_creator", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Gold analysis page ('Tại sao vàng VN luôn giá cao')" }),
  c({ name: "XAGUSD.Insights", canonicalUrl: "https://facebook.com/XAGUSD.Insights", objectType: "facebook_page", operatingModel: "commodity_creator", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Gold/silver trading signals; AI-flagged reversals" }),
  c({ name: "QTradeGold (Anh Quân Trader)", canonicalUrl: "https://facebook.com/QTradeGold/", objectType: "facebook_page", operatingModel: "social_finance_creator", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "Gold price entertainment/livestream trading; social real-time banter" }),
  c({ name: "BCR Vietnam", canonicalUrl: "https://facebook.com/bcrvietnam/", objectType: "facebook_page", operatingModel: "commodity_creator", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 3, commercialNoiseRiskScore: 4, verificationConfidence: "low", notes: "Broker-affiliated; world gold sessions analysis tagged #Gold #XAUUSD" }),
  c({ name: "Gold Pro", canonicalUrl: "https://facebook.com/100076052146472", objectType: "facebook_page", operatingModel: "commodity_creator", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Gold trading education; curated TA resources for beginners" }),
  c({ name: "MH Markets Vietnam", canonicalUrl: "https://facebook.com/61565662204355", objectType: "facebook_page", operatingModel: "commodity_creator", category: "gold_usd", topicOverlapScore: 3, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 3, commercialNoiseRiskScore: 4, verificationConfidence: "low", notes: "XAUUSD technical analysis; HCMC; broker-affiliated" }),
];

// ── REAL ESTATE CREATORS / BROKERS ──────────────────────
const reCandidates: Candidate[] = [
  c({ name: "Doctor Housing (Nguyễn Duy Chuyền)", canonicalUrl: "https://facebook.com/ceonguyenduychuyen", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", followerCount: 746000, topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 1, verificationConfidence: "medium", notes: "RE appraiser; How 2 Money host; ~746K followers; market trend commentary" }),
  c({ name: "Shark Hưng (Phạm Thành Hưng)", canonicalUrl: "https://facebook.com/petre.seymour.justice/", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", followerCount: 1900000, topicOverlapScore: 3, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 1, commercialNoiseRiskScore: 3, verificationConfidence: "low", notes: "Vice Chairman Cen Group; Shark Tank; ~1.9M followers; BĐS rumors, proptech" }),
  c({ name: "Nguyễn Văn Hanh BĐS", canonicalUrl: "https://facebook.com/datrungvietnam/", objectType: "facebook_page", operatingModel: "real_estate_broker", category: "real_estate", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "RE-investment creator; land-use-fee analysis; Vinhomes; gold-vs-RE strategy" }),
  c({ name: "Đinh Sơn Thủy", canonicalUrl: "https://facebook.com/dinhsonthuybds", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "'Chu kỳ Vàng BĐS 2025–2030' cycle analysis; best investment timing" }),
  c({ name: "Lê Xuân Nga", canonicalUrl: "https://facebook.com/lexuannganghemoigioi", objectType: "facebook_page", operatingModel: "real_estate_broker", category: "real_estate", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Veteran investor since 2009; new real-estate cycle content" }),
  c({ name: "Dương Đình Châu", canonicalUrl: "https://facebook.com/duongdinhchaubds", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "RE investment advisor; capital flows; investment valuation; cash-flow analysis" }),
  c({ name: "NewsRealVN", canonicalUrl: "https://facebook.com/NewsRealVN", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Deep RE-cycle analysis framing it as interest-rate/cash-flow problem" }),
  c({ name: "Vũ Ngọc Khoa", canonicalUrl: "https://facebook.com/ngockhoafca/", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", followerCount: 21700, topicOverlapScore: 3, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 3, verificationConfidence: "medium", notes: "Weekly Phú Quốc RE investment videos; ~21.7K likes" }),
  c({ name: "Nhà Đất Hùng Thuận", canonicalUrl: "https://facebook.com/nhadathungthuan/", objectType: "facebook_page", operatingModel: "real_estate_broker", category: "real_estate", followerCount: 252000, topicOverlapScore: 3, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 1, commercialNoiseRiskScore: 3, verificationConfidence: "low", notes: "Familiar BĐS community face; ~252K followers" }),
  c({ name: "Đăng Dương", canonicalUrl: "https://facebook.com/dangduongofficial", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Broker → investor journey; analytical/educational RE-invest content" }),
  c({ name: "Beyond360 VN Property", canonicalUrl: "https://facebook.com/Beyond360VNProperty", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 3, verificationConfidence: "low", notes: "Monthly VN property market updates; cycle analysis" }),
  c({ name: "Hội Môi giới BĐS VN (VARS)", canonicalUrl: "https://facebook.com/hoimoigioibds/", objectType: "facebook_page", operatingModel: "real_estate_broker", category: "real_estate", followerCount: 19800, topicOverlapScore: 3, audienceOverlapScore: 2, operatingModelSimilarityScore: 2, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 3, commercialNoiseRiskScore: 3, verificationConfidence: "medium", notes: "Official broker association; professional brokers; ~19.8K likes" }),
  c({ name: "Rich Nguyen (Rich Nguyễn)", canonicalUrl: "unverified", objectType: "facebook_page", operatingModel: "real_estate_creator", category: "real_estate", followerCount: 981000, topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low", notes: "RE investment strategist; author 'Bất động sản Vi mô'; ~981K followers; URL unverified" }),
];

// ── MACRO / SOCIAL-FINANCE / EDUCATORS ─────────────────
const macroCandidates: Candidate[] = [
  c({ name: "Hieu.TV (Nguyễn Ngọc Hiếu)", canonicalUrl: "https://facebook.com/hieuhiinvest", objectType: "facebook_page", operatingModel: "macro_creator", category: "personal_finance", followerCount: 9249, topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "Financial freedom; multi-asset (stocks, gold); podcast host; 9.2K likes; impersonation risk" }),
  c({ name: "Thạc sĩ Tài chính (MFin)", canonicalUrl: "https://facebook.com/thacsitaichinhmfin/", objectType: "facebook_page", operatingModel: "macro_creator", category: "personal_finance", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "MFIN Talkshow series on Vietnam's financial innovation; 48+ episodes" }),
  c({ name: "AFA Research and Education", canonicalUrl: "https://facebook.com/like.AFAResearchAndEducation/", objectType: "facebook_page", operatingModel: "macro_creator", category: "macro_economics", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 3, verificationConfidence: "low", notes: "'Phân tích kinh tế vĩ mô ứng dụng trong đầu tư' program; macro education" }),
  c({ name: "Fandi Finance & Invest", canonicalUrl: "https://facebook.com/Fandi.FinanceandInvest/", objectType: "facebook_page", operatingModel: "macro_creator", category: "macro_economics", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "medium", notes: "Weekly news decoding gold rush; multi-asset positioning (stocks, gold, macro)" }),
  c({ name: "FinPeace (Nguyễn Tuấn Anh)", canonicalUrl: "https://facebook.com/tuananhfinpeace/", objectType: "facebook_page", operatingModel: "macro_creator", category: "personal_finance", topicOverlapScore: 4, audienceOverlapScore: 4, operatingModelSimilarityScore: 4, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Multi-asset investor (gold + stocks); wealth-building education; CafeBiz coverage" }),
  c({ name: "Giang Ơi (Thu Giang)", canonicalUrl: "https://facebook.com/giangoivlog/", objectType: "facebook_page", operatingModel: "social_finance_creator", category: "personal_finance", topicOverlapScore: 2, audienceOverlapScore: 4, operatingModelSimilarityScore: 3, postingFrequencyScore: 4, publicDataAvailabilityScore: 5, scaleComparabilityScore: 2, verificationConfidence: "high", notes: "Personal/family finance storytelling; podcast Giang Ơi Radio; large multi-platform" }),
  c({ name: "TS. Lê Thẩm Dương", canonicalUrl: "https://facebook.com/lethamduong.edu.vn/", objectType: "facebook_page", operatingModel: "social_finance_creator", category: "personal_finance", followerCount: 1100000, topicOverlapScore: 2, audienceOverlapScore: 3, operatingModelSimilarityScore: 2, postingFrequencyScore: 4, publicDataAvailabilityScore: 5, scaleComparabilityScore: 1, verificationConfidence: "high", notes: "1.1M+ likes; Personal Finance seminar series; author; 64 known fake pages" }),
  c({ name: "Mr. Why (Phạm Ngọc Anh)", canonicalUrl: "https://facebook.com/phamngocanhask/", objectType: "facebook_page", operatingModel: "social_finance_creator", category: "personal_finance", topicOverlapScore: 2, audienceOverlapScore: 3, operatingModelSimilarityScore: 2, postingFrequencyScore: 4, publicDataAvailabilityScore: 4, scaleComparabilityScore: 2, commercialNoiseRiskScore: 3, verificationConfidence: "medium", notes: "Personal development + finance coach; ASK Training; Wake Up Việt Nam" }),
  c({ name: "Money With Mina", canonicalUrl: "https://facebook.com/MoneywithMina/", objectType: "facebook_page", operatingModel: "macro_creator", category: "personal_finance", topicOverlapScore: 3, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "Vietnamese personal finance and financial literacy education" }),
  c({ name: "Tu Pham (Phạm Quang Tú)", canonicalUrl: "https://facebook.com/phamquangtu/", objectType: "facebook_page", operatingModel: "investment_educator", category: "personal_finance", topicOverlapScore: 3, audienceOverlapScore: 3, operatingModelSimilarityScore: 3, postingFrequencyScore: 3, publicDataAvailabilityScore: 4, scaleComparabilityScore: 4, verificationConfidence: "low", notes: "'Tiền sinh lãi' philosophy; personal finance/investment educator" }),
];

// ── FACEBOOK GROUPS (group_reference only) ──────────────
const groupCandidates: Candidate[] = [
  c({ name: "CỘNG ĐỒNG CHỨNG KHOÁN", canonicalUrl: "https://facebook.com/groups/congdongchungkhoanchinhthuc/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 5, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "medium" }),
  c({ name: "CHỨNG KHOÁN VIỆT NAM", canonicalUrl: "https://facebook.com/groups/399427430492995/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 5, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "Diễn Đàn Chứng Khoán Việt Nam", canonicalUrl: "https://facebook.com/groups/361289263335428/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "F189: DIỄN ĐÀN CHỨNG KHOÁN, TIỀN SỐ", canonicalUrl: "https://facebook.com/groups/chungkhoanf319/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 5, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "medium" }),
  c({ name: "CHỨNG KHOÁN VIỆT", canonicalUrl: "https://facebook.com/groups/chungkhoans/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 5, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "medium" }),
  c({ name: "Chứng Khoán (tamlyck)", canonicalUrl: "https://facebook.com/groups/tamlyck/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "Cộng đồng phân tích kỹ thuật chứng khoán", canonicalUrl: "https://facebook.com/groups/330927140944781/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 5, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "Phân Tích Chứng Khoán", canonicalUrl: "https://facebook.com/groups/phantichchungkhoan.net/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 5, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "Tự Học Chứng Khoán", canonicalUrl: "https://facebook.com/groups/tuhocchungkhoan/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "medium" }),
  c({ name: "Chứng Khoán Thực Chiến (group)", canonicalUrl: "https://facebook.com/groups/Congdongdautuchungkhoanthucchien/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "Đầu tư từ Đâu? Đầu tư từ Đây!", canonicalUrl: "https://facebook.com/groups/dautudauday/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "medium" }),
  c({ name: "Cộng đồng Sinh viên Đầu tư Chứng Khoán", canonicalUrl: "https://facebook.com/groups/congdongsinhviendautuchungkhoan/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 3, audienceOverlapScore: 2, operatingModelSimilarityScore: 1, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "medium" }),
  c({ name: "Cộng Đồng Phái Sinh", canonicalUrl: "https://facebook.com/groups/743390503477089/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "CHỨNG KHOÁN PHÁI SINH", canonicalUrl: "https://facebook.com/groups/376265849471849/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "Yêu chứng khoán - Nghiện tấu hài", canonicalUrl: "https://facebook.com/groups/bovagau/", objectType: "facebook_group", operatingModel: "community_group", category: "meme_finance", topicOverlapScore: 3, audienceOverlapScore: 4, operatingModelSimilarityScore: 2, postingFrequencyScore: 5, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "medium" }),
  c({ name: "Diễn Đàn Vàng Việt Nam", canonicalUrl: "https://facebook.com/groups/diendanvangvnnews/", objectType: "facebook_group", operatingModel: "community_group", category: "gold_usd", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "Tài chính & Đầu tư Bất động sản (REFI)", canonicalUrl: "https://facebook.com/groups/refi/", objectType: "facebook_group", operatingModel: "community_group", category: "real_estate", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "Cộng đồng KOL Bất Động Sản Việt Nam", canonicalUrl: "https://facebook.com/KOLBDSVN/", objectType: "facebook_group", operatingModel: "community_group", category: "real_estate", topicOverlapScore: 3, audienceOverlapScore: 2, operatingModelSimilarityScore: 1, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "Cộng đồng BẤT ĐỘNG SẢN", canonicalUrl: "https://facebook.com/groups/congdongbds8/", objectType: "facebook_group", operatingModel: "community_group", category: "real_estate", topicOverlapScore: 3, audienceOverlapScore: 2, operatingModelSimilarityScore: 1, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "CaFe Chứng Khoán (dautuck247)", canonicalUrl: "https://facebook.com/groups/dautuck247/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 3, operatingModelSimilarityScore: 1, postingFrequencyScore: 4, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
  c({ name: "Đầu tư chứng khoán định lượng (Quant)", canonicalUrl: "https://facebook.com/groups/dautuchungkhoandinhluong/", objectType: "facebook_group", operatingModel: "community_group", category: "stock_market", topicOverlapScore: 4, audienceOverlapScore: 2, operatingModelSimilarityScore: 1, postingFrequencyScore: 3, publicDataAvailabilityScore: 3, scaleComparabilityScore: 1, verificationConfidence: "low" }),
];

// ─── Merge + dedupe ─────────────────────────────────────
const all = [...stockCandidates, ...goldCandidates, ...reCandidates, ...macroCandidates, ...groupCandidates];
const seen = new Set<string>();
const deduped: Candidate[] = [];
for (const cand of all) {
  const key = cand.canonicalUrl.toLowerCase().replace(/\/+$/, "");
  if (seen.has(key) || seen.has(cand.name.toLowerCase())) continue;
  seen.add(key);
  seen.add(cand.name.toLowerCase());
  deduped.push(cand);
}

// ─── Score + assign candidateId + recommendedRole ───────
const scored = deduped.map((cand, i) => {
  const fit = totalFitScoreV3(cand);
  const role = recommendedRole(cand, fit);
  return { ...cand, candidateId: `EXP-${String(i + 1).padStart(3, "0")}`, totalFitScoreV3: parseFloat(fit.toFixed(2)), recommendedRole: role };
});

// ─── Write expanded-targeted-candidates.csv ─────────────
const csvHeaders = [
  "candidateId","name","canonicalUrl","platform","objectType","operatingModel",
  "category","subCategory","activeStatus","followerCount","audienceCountType",
  "followerCountAsOf","lastPostObservedAt","observedPostCount","dominantTopics",
  "dominantFormats","postingFrequencyEstimate","brokerageOrCommercialActivity",
  "topicOverlapScore","audienceOverlapScore","formatSimilarityScore",
  "operatingModelSimilarityScore","postingFrequencyScore","publicDataAvailabilityScore",
  "scaleComparabilityScore","contentConsistencyScore","commercialNoiseRiskScore",
  "identityConfidenceScore","totalFitScoreV3","recommendedRole",
  "verificationConfidence","lastVerifiedAt","notes",
];

const csvLines = [csvHeaders.join(",")];
for (const c of scored) {
  csvLines.push([
    esc(c.candidateId), esc(c.name), esc(c.canonicalUrl), esc(c.platform), esc(c.objectType),
    esc(c.operatingModel), esc(c.category), esc(c.subCategory), esc(c.activeStatus),
    esc(c.followerCount), esc(c.audienceCountType), esc(c.followerCountAsOf),
    esc(c.lastPostObservedAt), esc(c.observedPostCount), esc(c.dominantTopics),
    esc(c.dominantFormats), esc(c.postingFrequencyEstimate), esc(c.brokerageOrCommercialActivity),
    esc(c.topicOverlapScore), esc(c.audienceOverlapScore), esc(c.formatSimilarityScore),
    esc(c.operatingModelSimilarityScore), esc(c.postingFrequencyScore), esc(c.publicDataAvailabilityScore),
    esc(c.scaleComparabilityScore), esc(c.contentConsistencyScore), esc(c.commercialNoiseRiskScore),
    esc(c.identityConfidenceScore), esc(c.totalFitScoreV3), esc(c.recommendedRole),
    esc(c.verificationConfidence), esc(c.lastVerifiedAt), esc(c.notes),
  ].join(","));
}

const outDir = join(process.cwd(), "data", "benchmark");
writeFileSync(join(outDir, "expanded-targeted-candidates.csv"), csvLines.join("\n") + "\n");

// ─── Build replacement shortlist (top 10 by fit score, not groups) ────
const nonGroup = scored.filter(c => c.objectType !== "facebook_group" && c.canonicalUrl !== "unverified");
const byVertical = { stock: [] as typeof scored, gold: [] as typeof scored, re: [] as typeof scored, macro: [] as typeof scored };
for (const c of nonGroup) {
  if (c.operatingModel.startsWith("stock") || c.operatingModel === "investment_educator") byVertical.stock.push(c);
  else if (c.operatingModel.startsWith("gold") || c.operatingModel.startsWith("commodity")) byVertical.gold.push(c);
  else if (c.operatingModel.startsWith("real_estate")) byVertical.re.push(c);
  else byVertical.macro.push(c);
}
for (const k of Object.keys(byVertical) as (keyof typeof byVertical)[]) byVertical[k].sort((a: { totalFitScoreV3: number }, b: { totalFitScoreV3: number }) => b.totalFitScoreV3 - a.totalFitScoreV3);

const shortlist = [
  ...byVertical.stock.slice(0, 4),
  ...byVertical.gold.slice(0, 2),
  ...byVertical.re.slice(0, 2),
  ...byVertical.macro.slice(0, 2),
];

const shortlistHeaders = ["rank","name","canonicalUrl","objectType","operatingModel","totalFitScoreV3","verificationConfidence","vertical","why_fit","why_not","metric_visibility","notes"];
const shortlistLines = [shortlistHeaders.join(",")];
shortlist.forEach((c, i) => {
  const vertical = c.operatingModel.startsWith("stock") || c.operatingModel === "investment_educator" ? "stock" :
    c.operatingModel.startsWith("gold") || c.operatingModel.startsWith("commodity") ? "gold" :
    c.operatingModel.startsWith("real_estate") ? "real_estate" : "macro";
  shortlistLines.push([
    esc(i + 1), esc(c.name), esc(c.canonicalUrl), esc(c.objectType), esc(c.operatingModel),
    esc(c.totalFitScoreV3), esc(c.verificationConfidence), esc(vertical),
    esc(`fit=${c.totalFitScoreV3}; topicOverlap=${c.topicOverlapScore}; opModel=${c.operatingModelSimilarityScore}`),
    esc(c.scaleComparabilityScore <= 2 ? "scale mismatch" : c.verificationConfidence === "low" ? "URL/confidence low" : ""),
    esc(c.publicDataAvailabilityScore >= 4 ? "reactions+comments+shares visible" : "partial visibility"),
    esc(c.notes),
  ].join(","));
});
writeFileSync(join(outDir, "replacement-shortlist.csv"), shortlistLines.join("\n") + "\n");

// ─── Peer Set v3 proposed ───────────────────────────────
// Core peers: top candidates by fit score + existing 7 external core peers that remain
// Exclude URLs already in existing core peer set
const existingUrls = new Set([
  "https://facebook.com/nguoiquansat.thongtintaichinh/",
  "https://facebook.com/VTVIndex/",
  "https://facebook.com/dffvn.official/",
  "https://facebook.com/Kafi.vn/",
  "https://facebook.com/thoibaonganhang.vn/",
  "https://facebook.com/ChungkhoanVFS/",
  "https://facebook.com/thuanphaisinhvn/",
].map(u => u.toLowerCase().replace(/\/+$/, "")));
const v3Core = scored.filter(c => c.recommendedRole === "direct_core_peer" && !existingUrls.has(c.canonicalUrl.toLowerCase().replace(/\/+$/, ""))).slice(0, 5);
// Keep existing 7 + add up to 5 new = 12 max
const v3Headers = ["name","canonicalUrl","objectType","operatingModel","scaleBand","benchmarkRole","collectionFrequency","recommendedPostsPerCollection","fitScore","verificationConfidence","notes"];
const v3Lines: string[] = [v3Headers.join(",")];

// Existing 7 external core peers (already in DB)
const existingCore = [
  { name: "Người Quan Sát", url: "https://facebook.com/nguoiquansat.thongtintaichinh/", type: "facebook_page", model: "stock_creator", scale: "medium", fit: 4.45, conf: "high", notes: "563K - closest analytical peer" },
  { name: "VTV Index / VTV Money", url: "https://facebook.com/VTVIndex/", type: "facebook_page", model: "stock_creator", scale: "small", fit: 4.30, conf: "medium", notes: "Same video format + VN-Index/macro" },
  { name: "DFFVN (Dòng tiền Đầu tư)", url: "https://facebook.com/dffvn.official/", type: "facebook_page", model: "gold_creator", scale: "micro", fit: 3.80, conf: "medium", notes: "Multi-asset video analysis" },
  { name: "Kafi.vn", url: "https://facebook.com/Kafi.vn/", type: "facebook_page", model: "stock_creator", scale: "small", fit: 3.75, conf: "medium", notes: "Multi-commodity daily" },
  { name: "Thời Báo Ngân Hàng", url: "https://facebook.com/thoibaonganhang.vn/", type: "facebook_page", model: "macro_creator", scale: "small", fit: 3.75, conf: "medium", notes: "Banking/rates/FX/gold outlet" },
  { name: "Chứng khoán Nhất Việt - VFS", url: "https://facebook.com/ChungkhoanVFS/", type: "facebook_page", model: "stock_creator", scale: "micro", fit: 3.60, conf: "medium", notes: "Multi-asset page stocks/FX/gold" },
  { name: "Thuận Phái Sinh VN", url: "https://facebook.com/thuanphaisinhvn/", type: "facebook_page", model: "stock_creator", scale: "micro", fit: 3.50, conf: "medium", notes: "Niche stock critique text" },
];
for (const e of existingCore) {
  v3Lines.push([esc(e.name), esc(e.url), esc(e.type), esc(e.model), esc(e.scale), "direct_core_peer", "weekly", 4, esc(e.fit), esc(e.conf), esc(e.notes)].join(","));
}
// New proposed core peers
for (const c of v3Core) {
  const scale = !c.followerCount ? "micro" : c.followerCount < 20000 ? "micro" : c.followerCount < 100000 ? "small" : c.followerCount < 500000 ? "medium" : "large";
  v3Lines.push([esc(c.name), esc(c.canonicalUrl), esc(c.objectType), esc(c.operatingModel), esc(scale), "direct_core_peer", "weekly", 4, esc(c.totalFitScoreV3), esc(c.verificationConfidence), esc("PROPOSED v3 — " + c.notes)].join(","));
}

// Extended creator peers (next tier)
const extendedPeers = scored.filter(c => c.recommendedRole === "watchlist" && c.objectType !== "facebook_group" && c.totalFitScoreV3 >= 3.2).slice(0, 10);
for (const c of extendedPeers) {
  const scale = !c.followerCount ? "micro" : c.followerCount < 20000 ? "micro" : c.followerCount < 100000 ? "small" : c.followerCount < 500000 ? "medium" : "large";
  v3Lines.push([esc(c.name), esc(c.canonicalUrl), esc(c.objectType), esc(c.operatingModel), esc(scale), "watchlist", "biweekly", 3, esc(c.totalFitScoreV3), esc(c.verificationConfidence), esc("PROPOSED v3 extended — " + c.notes)].join(","));
}

// Topic references (groups + institutional)
const topicRefs = scored.filter(c => c.objectType === "facebook_group" || c.operatingModel === "institutional_research").slice(0, 12);
for (const c of topicRefs) {
  v3Lines.push([esc(c.name), esc(c.canonicalUrl), esc(c.objectType), esc(c.operatingModel), esc("unknown"), "topic_reference", "monthly", 0, esc(c.totalFitScoreV3), esc(c.verificationConfidence), esc("PROPOSED v3 topic ref — " + c.notes)].join(","));
}

writeFileSync(join(outDir, "public-benchmark-peer-set-v3-proposed.csv"), v3Lines.join("\n") + "\n");

// ─── Summary stats ──────────────────────────────────────
console.log("=== Targeted Peer Expansion Summary ===");
console.log("Total candidates (deduped):", scored.length);
const byModel: Record<string, number> = {};
const byType: Record<string, number> = {};
const byRole: Record<string, number> = {};
for (const c of scored) {
  byModel[c.operatingModel] = (byModel[c.operatingModel] || 0) + 1;
  byType[c.objectType] = (byType[c.objectType] || 0) + 1;
  byRole[c.recommendedRole] = (byRole[c.recommendedRole] || 0) + 1;
}
console.log("\nBy operating model:", JSON.stringify(byModel, null, 2));
console.log("\nBy objectType:", JSON.stringify(byType, null, 2));
console.log("\nBy recommended role:", JSON.stringify(byRole, null, 2));
console.log("\nReplacement shortlist:", shortlist.length, "candidates");
console.log("Proposed v3 core (existing 7 + new):", 7 + v3Core.length);
console.log("\nFiles written:");
console.log("  data/benchmark/expanded-targeted-candidates.csv");
console.log("  data/benchmark/replacement-shortlist.csv");
console.log("  data/benchmark/public-benchmark-peer-set-v3-proposed.csv");
