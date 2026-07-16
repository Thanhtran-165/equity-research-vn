/**
 * Seed dữ liệu mẫu để demo UI khi CHƯA có Facebook token.
 * Chạy: npm run seed
 *
 * Lưu ý:KHÔNG ghi token thật vào DB. Seed chỉ tạo pages/posts/comments giả.
 */
import { PrismaClient } from "@prisma/client";
import { detectTopic } from "../lib/topics";
import {
  moderateComment,
} from "../lib/moderation";
import { deriveSnapshot } from "../lib/benchmark";

const prisma = new PrismaClient();

const NOW = Date.now();
const DAY = 24 * 60 * 60 * 1000;

function iso(daysAgo: number): string {
  return new Date(NOW - daysAgo * DAY).toISOString();
}

function dateStr(daysAgo: number): string {
  return new Date(NOW - daysAgo * DAY).toISOString().slice(0, 10);
}

const SAMPLE_MESSAGES = [
  "CPI tháng 6 tăng nhẹ hơn dự báo, Fed có thể giữ nguyên lãi suất trong tháng 7.",
  "VN-Index đóng cửa tăng mạnh, thanh khoản vượt 20 nghìn tỷ.",
  "SBV tiếp tục hút tiền qua OMO, lãi suất liên ngân hàng nhích lên.",
  "Thị trường bất động sản gan Hyderabad sôi động, Vinomes ra hàng mới.",
  "Giá vàng SJC chạm đỉnh, gold futures tăng mạnh đêm qua.",
  "GDP quý II dự báo tăng trưởng 6.5%, vĩ mô tích cực.",
  "Cổ phiếu FPT chốt phiên tăng trần, margin giảm nhẹ.",
  "Yield trái phiếu chính phủ 10 năm nhích lên theo USD yield.",
  "Căn hộ chung cu trung bình Hà Nội tăng 12% so với cùng kỳ.",
  "XAUUSD rục rịch đỉnh lịch sử, paxg cũng theo sát.",
];

const SAMPLE_COMMENTS = [
  "Nguồn đâu bạn ơi?",
  "Có khuyến nghị mua không vậy?",
  "Inbox em nhé, kiếm tiền nhanh cam kết lợi nhuận 30%",
  "Bán chưa ae ơi",
  "Mua mã nào giờ",
  "Cho em vào room vip với",
  "Zalo em 0901xxx nhận phân tích",
  "Bài viết hay, cảm ơn ad",
  "Link đăng ký nhóm đâu vậy",
  "Học ở đâu để hiểu vĩ mô vậy ạ",
];

function makeReach() {
  return Math.floor(500 + Math.random() * 20000);
}

async function main() {
  console.log("→ Xoá dữ liệu cũ...");
  await prisma.comment.deleteMany();
  await prisma.post.deleteMany();
  await prisma.videoMetric.deleteMany();
  await prisma.pageSnapshot.deleteMany();
  await prisma.weeklyReport.deleteMany();
  await prisma.competitorMetricSnapshot.deleteMany();
  await prisma.competitorPage.deleteMany();
  await prisma.ownPagePublicComparableSnapshot.deleteMany();

  const pageId = process.env.FB_PAGE_ID || "demo_page_id";
  const pageName = "Demo Page";

  console.log("→ Tạo PageSnapshots (7 ngày gần nhất)...");
  let prevFollowers = 12000;
  for (let d = 6; d >= 0; d--) {
    const delta = Math.floor((Math.random() - 0.4) * 80);
    const followers = prevFollowers + delta;
    await prisma.pageSnapshot.create({
      data: {
        date: dateStr(d),
        pageId,
        pageName: "Demo Page",
        followersCount: followers,
        fanCount: followers + 350,
        followersDelta: delta,
      },
    });
    prevFollowers = followers;
  }

  console.log("→ Tạo 25 bài mẫu...");
  const posts = [];
  for (let i = 0; i < 25; i++) {
    const msg = SAMPLE_MESSAGES[i % SAMPLE_MESSAGES.length];
    const topic = detectTopic(msg);
    const reach = makeReach();
    const impressions = Math.floor(reach * (1.2 + Math.random() * 0.6));
    const reactions = Math.floor(reach * (0.02 + Math.random() * 0.06));
    const comments = Math.floor(reach * (0.005 + Math.random() * 0.03));
    const shares = Math.floor(reach * (0.001 + Math.random() * 0.01));
    const clicks = Math.floor(reach * (0.01 + Math.random() * 0.05));
    const engagementRate =
      reach > 0 ? (reactions + comments + shares + clicks) / reach : null;
    const isVideo = i % 5 === 0;
    const postType = isVideo ? "video_or_reel" : i % 3 === 0 ? "photo" : "text";

    const post = await prisma.post.create({
      data: {
        fbPostId: `demo_post_${i}_${Date.now()}`,
        pageId,
        message: msg,
        permalinkUrl: "https://www.facebook.com/demo/" + i,
        createdTime: iso(i * 0.7),
        postType,
        topic,
        reactionsCount: reactions,
        commentsCount: comments,
        sharesCount: shares,
        reach,
        impressions,
        engagedUsers: Math.floor(reach * (0.03 + Math.random() * 0.05)),
        clicks,
        engagementRate,
        score: null, // sẽ tính ở bước sync thực; demo để null
        rawJson: JSON.stringify({ seed: true }),
      },
    });
    posts.push(post);

    if (isVideo) {
      await prisma.videoMetric.create({
        data: {
          fbVideoId: `demo_video_${i}_${Date.now()}`,
          fbPostId: post.fbPostId,
          pageId,
          title: msg.slice(0, 60),
          createdTime: post.createdTime ?? iso(i * 0.7),
          views: Math.floor(reach * (1.5 + Math.random() * 3)),
          uniqueViews: Math.floor(reach * (1.1 + Math.random() * 0.8)),
          avgWatchTime: 8 + Math.random() * 30,
          reach,
          reactionsCount: reactions,
          commentsCount: comments,
          sharesCount: shares,
        },
      });
    }
  }

  console.log("→ Tạo comments mẫu cho 8 bài đầu...");
  for (let i = 0; i < 8 && i < posts.length; i++) {
    const post = posts[i];
    const n = 4 + Math.floor(Math.random() * 4);
    for (let j = 0; j < n; j++) {
      const msg = SAMPLE_COMMENTS[j % SAMPLE_COMMENTS.length];
      const mod = moderateComment(msg);
      await prisma.comment.create({
        data: {
          fbCommentId: `demo_cmt_${i}_${j}_${Date.now()}`,
          fbPostId: post.fbPostId,
          pageId,
          message: msg,
          createdTime: iso(i * 0.7),
          likeCount: Math.floor(Math.random() * 20),
          commentCount: Math.floor(Math.random() * 5),
          keywordFlag: mod.keywordFlag,
          sentiment: mod.sentiment,
          riskLevel: mod.riskLevel,
          status: mod.riskLevel === "high" ? "flagged" : "new",
          suggestedAction: mod.suggestedAction,
          suggestedReply: mod.suggestedReply,
        },
      });
    }
  }

  console.log("✅ Seed xong (FB page + posts + comments).");

  await seedBenchmark(pageId, pageName);
}

/**
 * Seed dữ liệu benchmark DEMO (fake). KHÔNG dùng số liệu thật.
 */
async function seedBenchmark(pageId: string, pageName: string) {
  console.log("→ Xoá benchmark cũ...");
  await prisma.competitorMetricSnapshot.deleteMany();
  await prisma.competitorPage.deleteMany();
  await prisma.ownPagePublicComparableSnapshot.deleteMany();

  const periodEnd = new Date().toISOString().slice(0, 10);
  // Khớp với /api/benchmark/compare?weeks=4 (4*7-1 = 27 ngày)
  const periodStartObj = new Date(Date.now() - 27 * 24 * 60 * 60 * 1000);
  const periodStart = periodStartObj.toISOString().slice(0, 10);

  // 8 competitor demo, đa dạng category & quy mô.
  // Dữ liệu giả lập để demo UI benchmark - không phải số liệu thật.
  const demoCompetitors = [
    { name: "CafeF", category: "chung_khoan", followers: 1_000_000, posts: 120, reactions: 50_000, comments: 7_000, shares: 3_000, videoViews: 2_000_000, topEng: 5_000, ads: true, topic: "chứng khoán" },
    { name: "Page Macro ABC", category: "vi_mo", followers: 200_000, posts: 40, reactions: 12_000, comments: 3_500, shares: 800, videoViews: 300_000, topEng: 1_800, ads: false, topic: "vĩ mô" },
    { name: "The Bonds Daily", category: "lai_suat", followers: 80_000, posts: 60, reactions: 6_000, comments: 1_200, shares: 600, videoViews: 90_000, topEng: 700, ads: false, topic: "lãi suất" },
    { name: "BĐS Watch", category: "bds", followers: 350_000, posts: 90, reactions: 22_000, comments: 9_000, shares: 4_500, videoViews: 600_000, topEng: 3_200, ads: true, topic: "BĐS" },
    { name: "Gold Tracker VN", category: "vang", followers: 150_000, posts: 70, reactions: 9_000, comments: 2_000, shares: 1_400, videoViews: 250_000, topEng: 1_100, ads: false, topic: "vàng" },
    { name: "Influencer Tài Chính X", category: "influencer_tai_chinh", followers: 500_000, posts: 30, reactions: 35_000, comments: 8_500, shares: 6_000, videoViews: 1_500_000, topEng: 9_000, ads: false, topic: "vĩ mô" },
    { name: "Stock Insights Y", category: "chung_khoan", followers: 90_000, posts: 100, reactions: 8_000, comments: 4_500, shares: 900, videoViews: 120_000, topEng: 1_200, ads: false, topic: "chứng khoán" },
    { name: "Macro Z (blog)", category: "vi_mo", followers: 30_000, posts: 25, reactions: 4_500, comments: 1_800, shares: 1_200, videoViews: 60_000, topEng: 900, ads: false, topic: "vĩ mô" },
  ];

  const competitors: Array<{ id: number; derived: any; raw: any }> = [];
  for (let i = 0; i < demoCompetitors.length; i++) {
    const d = demoCompetitors[i];
    const page = await prisma.competitorPage.create({
      data: {
        pageName: d.name,
        pageUrl: `https://facebook.com/demo-${d.category}-${i}-${Date.now()}`,
        category: d.category,
        description: `DEMO dữ liệu giả (${d.category})`,
        followersLatest: d.followers,
        isActive: true,
        notes: "DEMO/Fake data — không phải số liệu thật.",
      },
    });

    const derived = deriveSnapshot({
      followers: d.followers,
      postsCount: d.posts,
      reactionsCount: d.reactions,
      commentsCount: d.comments,
      sharesCount: d.shares,
      videoViews: d.videoViews,
      topPostEngagement: d.topEng,
      periodStart,
      periodEnd,
    });

    const snap = await prisma.competitorMetricSnapshot.create({
      data: {
        competitorPageId: page.id,
        periodStart,
        periodEnd,
        followers: d.followers,
        postsCount: d.posts,
        reactionsCount: d.reactions,
        commentsCount: d.comments,
        sharesCount: d.shares,
        videoViews: d.videoViews,
        topPostUrl: `https://facebook.com/demo-${d.category}-${i}-top`,
        topPostEngagement: d.topEng,
        activeAds: d.ads,
        dominantTopic: d.topic,
        publicEngagement: derived.publicEngagement,
        publicEngagementPerPost: derived.publicEngagementPerPost,
        engagementPer1kFollowers: derived.engagementPer1kFollowers,
        avgReactionsPerPost: derived.avgReactionsPerPost,
        avgCommentsPerPost: derived.avgCommentsPerPost,
        avgSharesPerPost: derived.avgSharesPerPost,
        videoViewsPerFollower: derived.videoViewsPerFollower,
        commentIntensity: derived.commentIntensity,
        shareIntensity: derived.shareIntensity,
        postingFrequencyPerDay: derived.postingFrequencyPerDay,
        rawJson: JSON.stringify({ demo: true }),
      },
    });

    competitors.push({ id: page.id, derived: snap, raw: d });
  }

  // Own page comparable snapshot — giả lập số liệu công khai tương đương.
  // Dùng dữ liệu INTERNAL đã sync (posts + pageSnapshot) để tính proxy.
  const ownPosts = await prisma.post.findMany({
    where: { pageId, createdTime: { gte: periodStartObj.toISOString() } },
  });
  const ownLatestSnapshot = await prisma.pageSnapshot.findFirst({
    where: { pageId },
    orderBy: { date: "desc" },
  });

  const ownFollowers = ownLatestSnapshot?.followersCount ?? 12_000;
  const ownReactions = ownPosts.reduce((s, p) => s + p.reactionsCount, 0) || 2_400;
  const ownComments = ownPosts.reduce((s, p) => s + p.commentsCount, 0) || 800;
  const ownShares = ownPosts.reduce((s, p) => s + p.sharesCount, 0) || 350;
  const ownVideoViews = (await prisma.videoMetric.aggregate({ _sum: { views: true } }))._sum.views ?? 80_000;
  const ownPostsCount = ownPosts.length || 22;

  const ownDerived = deriveSnapshot({
    followers: ownFollowers,
    postsCount: ownPostsCount,
    reactionsCount: ownReactions,
    commentsCount: ownComments,
    sharesCount: ownShares,
    videoViews: ownVideoViews ?? null,
    topPostEngagement: 650,
    periodStart,
    periodEnd,
  });

  await prisma.ownPagePublicComparableSnapshot.create({
    data: {
      pageId,
      periodStart,
      periodEnd,
      followers: ownFollowers,
      postsCount: ownPostsCount,
      reactionsCount: ownReactions,
      commentsCount: ownComments,
      sharesCount: ownShares,
      videoViews: ownVideoViews ?? null,
      publicEngagement: ownDerived.publicEngagement,
      publicEngagementPerPost: ownDerived.publicEngagementPerPost,
      engagementPer1kFollowers: ownDerived.engagementPer1kFollowers,
      avgReactionsPerPost: ownDerived.avgReactionsPerPost,
      avgCommentsPerPost: ownDerived.avgCommentsPerPost,
      avgSharesPerPost: ownDerived.avgSharesPerPost,
      videoViewsPerFollower: ownDerived.videoViewsPerFollower,
      commentIntensity: ownDerived.commentIntensity,
      shareIntensity: ownDerived.shareIntensity,
      postingFrequencyPerDay: ownDerived.postingFrequencyPerDay,
    },
  });

  console.log(`✅ Seed benchmark: ${competitors.length} competitor demo + own comparable snapshot.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
