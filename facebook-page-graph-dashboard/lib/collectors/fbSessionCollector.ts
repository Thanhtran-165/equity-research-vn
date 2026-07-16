/**
 * Facebook Session-Based Collector
 *
 * Uses Playwright with the user's existing Chrome browser session to collect
 * public engagement data from Facebook Pages.
 *
 * Safety:
 * - No headless mode — browser is always visible
 * - No cookie/session storage — uses user's existing browser session
 * - No credential storage
 * - Human-like pacing: 30s delay between pages
 * - Max 5 posts per page per run
 *
 * Null ≠ zero contract: missing metrics → null + observed=false
 */

import { classifyContent, parseFollowerCount, parseMetricCount } from "./classifyContent";

export interface CollectedPost {
  postUrl: string;
  postedAt: string | null;
  textSnippet: string | null;
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  videoViews: number | null;
  contentType: string;
  topicTag: string;
  commercialSignal: boolean;
  rawReactions: string | null;
  rawComments: string | null;
  rawShares: string | null;
}

export interface CollectionResult {
  pageId: number;
  pageName: string;
  canonicalUrl: string;
  status: "success" | "partial" | "unavailable" | "blocked";
  followerCount: number | null;
  posts: CollectedPost[];
  errors: string[];
  collectedAt: Date;
}

export interface PeerTarget {
  id: number;
  name: string;
  canonicalUrl: string;
}

interface CollectOptions {
  maxPosts?: number;
  delayBetweenPagesMs?: number;
  pageTimeoutMs?: number;
}

/**
 * Extract posts from a Facebook Page using Playwright.
 * The browser must already be open and logged in to Facebook.
 *
 * Uses accessibility snapshot (browser_snapshot) to extract structured data.
 */
export async function collectFromPage(
  browser: { snapshot: () => Promise<string>; evaluate: (fn: string | (() => unknown)) => Promise<unknown>; navigate: (url: string) => Promise<void> },
  peer: PeerTarget,
  options?: CollectOptions,
): Promise<CollectionResult> {
  const maxPosts = options?.maxPosts ?? 5;
  const errors: string[] = [];
  const posts: CollectedPost[] = [];
  let followerCount: number | null = null;

  try {
    // Navigate to the page
    await browser.navigate(peer.canonicalUrl);

    // Wait for page to load — look for follower count or posts
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // Try to get follower count from page text
    try {
      const pageText = await browser.evaluate(() => {
        return document.body?.innerText?.substring(0, 2000) || "";
      }) as string;

      // Look for "XX người theo dõi" pattern
      const followerMatch = pageText.match(/([\d.,KNTrn\s]+)\s*người theo dõi/i);
      if (followerMatch) {
        followerCount = parseFollowerCount(followerMatch[0]);
      }
    } catch (e) {
      errors.push(`Follower count extraction failed: ${e instanceof Error ? e.message : String(e)}`);
    }

    // Extract posts using evaluate — text-based approach (Facebook DOM is complex)
    try {
      const rawPosts = await browser.evaluate(() => {
        const results: Array<Record<string, string | null>> = [];

        // Facebook posts are in div[role="article"] containers
        const articles = document.querySelectorAll('div[role="article"]');

        let count = 0;
        for (const article of articles) {
          if (count >= 5) break;

          // Get all text content of the article
          const fullText = article.textContent || "";

          // Extract permalink — look for links to posts/permalink/photo/video/reel
          const links = article.querySelectorAll("a[href]");
          let permalink: string | null = null;
          for (const link of links) {
            const href = link.getAttribute("href") || "";
            if (href.includes("/posts/") || href.includes("/permalink/") || href.includes("/photos/") || href.includes("/videos/") || href.includes("/reel/")) {
              permalink = href.split("?")[0];
              break;
            }
          }

          // Extract post text — look for the main text container
          // Facebook uses [dir="auto"] for user-generated text
          const textEls = article.querySelectorAll('[dir="auto"]');
          let text = "";
          for (const el of textEls) {
            const t = el.textContent?.trim() || "";
            // Filter for substantial text (not navigation/labels)
            if (t.length > 30 && !t.includes("Thích") && !t.includes("Bình luận") && !t.includes("Chia sẻ")) {
              text = t.substring(0, 200);
              break;
            }
          }

          // Extract timestamp text (relative time like "2 giờ trước")
          let timestamp: string | null = null;
          for (const link of links) {
            const href = link.getAttribute("href") || "";
            if (href.includes("/posts/") || href.includes("/permalink/")) {
              timestamp = link.textContent?.trim() || null;
              break;
            }
          }

          // Extract reactions — look for aria-label containing reaction info
          let reactionsText: string | null = null;
          const reactionEls = article.querySelectorAll("[aria-label]");
          for (const el of reactionEls) {
            const label = el.getAttribute("aria-label") || "";
            if (label.includes("Thích") || label.includes("phản ứng") || label.includes("cảm xúc")) {
              const match = label.match(/([\d.,KNTntr\s]+)/i);
              if (match) reactionsText = match[0].trim();
              break;
            }
          }

          // Extract comments and shares from text
          // Facebook shows "N bình luận" and "N lượt chia sẻ" as text
          const commentsMatch = fullText.match(/([\d.,KNTntr\s]+)\s*bình luận/i);
          const sharesMatch = fullText.match(/([\d.,KNTntr\s]+)\s*(lượt\s*)?chia sẻ/i);
          const commentsText = commentsMatch ? commentsMatch[0] : null;
          const sharesText = sharesMatch ? sharesMatch[0] : null;

          // Check for video
          const hasVideo = !!article.querySelector("video, a[href*='/videos/'], a[href*='/reel/']");
          const hasPhoto = !!article.querySelector("img");

          // Only include if we have a permalink or substantial text
          if (permalink || text) {
            results.push({
              permalink,
              text: text || null,
              timestamp,
              reactionsText,
              commentsText,
              sharesText,
              hasVideo: hasVideo ? "true" : "false",
              hasPhoto: hasPhoto ? "true" : "false",
            });
            count++;
          }
        }
        return results;
      }) as Array<Record<string, string | null>>;

      // Transform raw posts to CollectedPost
      for (const raw of rawPosts.slice(0, maxPosts)) {
        const text = raw.text || null;
        const classification = classifyContent(text, {
          hasVideo: raw.hasVideo === "true",
          hasPhoto: raw.hasPhoto === "true",
        });

        const reactionsRaw = raw.reactionsText || null;
        const commentsRaw = raw.commentsText || null;
        const sharesRaw = raw.sharesText || null;

        posts.push({
          postUrl: raw.permalink || `fb-unknown-${Date.now()}-${posts.length}`,
          postedAt: raw.timestamp || null,
          textSnippet: text,
          reactions: parseMetricCount(reactionsRaw),
          comments: parseMetricCount(commentsRaw),
          shares: parseMetricCount(sharesRaw),
          videoViews: null,
          contentType: classification.contentType,
          topicTag: classification.topicTag,
          commercialSignal: classification.commercialSignal,
          rawReactions: reactionsRaw,
          rawComments: commentsRaw,
          rawShares: sharesRaw,
        });
      }
    } catch (e) {
      errors.push(`Post extraction failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  } catch (e) {
    errors.push(`Navigation failed: ${e instanceof Error ? e.message : String(e)}`);
  }

  // Determine status
  let status: CollectionResult["status"] = "unavailable";
  if (posts.length > 0) {
    const postsWithReactions = posts.filter((p) => p.reactions != null).length;
    if (postsWithReactions === posts.length) {
      status = "success";
    } else if (postsWithReactions > 0) {
      status = "partial";
    } else {
      status = "partial";
    }
  }
  if (posts.length === 0 && errors.length > 0) {
    status = errors.some((e) => e.includes("blocked") || e.includes("not found")) ? "blocked" : "unavailable";
  }

  return {
    pageId: peer.id,
    pageName: peer.name,
    canonicalUrl: peer.canonicalUrl,
    status,
    followerCount,
    posts,
    errors,
    collectedAt: new Date(),
  };
}

/**
 * Determine if a collection result has adequate coverage for benchmark use.
 */
export function getCoverageScore(result: CollectionResult): {
  reactions: number;
  comments: number;
  shares: number;
  overall: number;
} {
  const posts = result.posts;
  if (posts.length === 0) return { reactions: 0, comments: 0, shares: 0, overall: 0 };

  const reactionsCoverage = posts.filter((p) => p.reactions != null).length / posts.length;
  const commentsCoverage = posts.filter((p) => p.comments != null).length / posts.length;
  const sharesCoverage = posts.filter((p) => p.shares != null).length / posts.length;

  return {
    reactions: reactionsCoverage,
    comments: commentsCoverage,
    shares: sharesCoverage,
    overall: (reactionsCoverage + commentsCoverage + sharesCoverage) / 3,
  };
}
