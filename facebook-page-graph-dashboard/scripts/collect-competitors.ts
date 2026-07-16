/**
 * Collect Competitor Data — CLI runner.
 *
 * Usage:
 *   npm run collect:competitors                     # all 10 core peers
 *   npm run collect:competitors -- --pilot          # 3 pilot peers
 *   npm run collect:competitors -- --peer-ids=1,2,3 # specific peers
 *
 * Launches Chrome with user's session, visits each peer's Facebook Page,
 * collects public engagement data, and writes to DB.
 */
import { PrismaClient } from "@prisma/client";
import { chromium } from "playwright";
import { collectFromPage, getCoverageScore, type PeerTarget } from "../lib/collectors/fbSessionCollector";
import { derivePostMetrics } from "../lib/benchmark/publicMetrics";

const prisma = new PrismaClient();

const DELAY_BETWEEN_PAGES_MS = 30_000; // 30 seconds
const MAX_POSTS_PER_PAGE = 5;
const PAGE_TIMEOUT_MS = 30_000;

async function main() {
  const args = process.argv.slice(2);
  const pilot = args.includes("--pilot");
  const peerIdsArg = args.find((a) => a.startsWith("--peer-ids="));

  let peerIds: number[] | undefined;
  if (peerIdsArg) {
    peerIds = peerIdsArg.split("=")[1].split(",").map(Number);
  }

  // Get core peers
  let peers = await prisma.benchmarkPage.findMany({
    where: { benchmarkRole: "core_peer", isOwnPage: false },
    select: { id: true, name: true, canonicalUrl: true },
    orderBy: { name: "asc" },
  });

  if (pilot) {
    // Pilot: first 3 peers
    peers = peers.slice(0, 3);
    console.log("PILOT MODE: collecting from 3 peers");
  } else if (peerIds) {
    peers = peers.filter((p) => peerIds!.includes(p.id));
  }

  if (peers.length === 0) {
    console.error("No core peers found. Run seed first.");
    process.exit(1);
  }

  console.log(`\n=== Competitor Collection ===`);
  console.log(`Peers: ${peers.length}`);
  console.log(`Max posts/page: ${MAX_POSTS_PER_PAGE}`);
  console.log(`Delay between pages: ${DELAY_BETWEEN_PAGES_MS / 1000}s\n`);

  // Launch Chrome with user's profile
  console.log("Launching Chrome with user session...");
  const browser = await chromium.launchPersistentContext(
    `${process.env.HOME}/Library/Application Support/Google/Chrome/Default`,
    {
      headless: false,
      channel: "chrome",
      viewport: { width: 1280, height: 800 },
      timeout: 60_000,
    },
  ).catch(async () => {
    // Fallback: try launching without persistent context (might need separate profile)
    console.log("⚠️  Could not use default Chrome profile. Launching with fresh profile...");
    console.log("   You may need to log in to Facebook manually in the opened browser.");
    return await chromium.launchPersistentContext(
      `${process.env.HOME}/.fb-collector-profile`,
      {
        headless: false,
        channel: "chrome",
        viewport: { width: 1280, height: 800 },
        timeout: 60_000,
      },
    );
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(PAGE_TIMEOUT_MS);

  const results: Array<{ peer: PeerTarget; status: string; posts: number; followerCount: number | null; errors: string[] }> = [];
  const collectedAt = new Date();

  for (let i = 0; i < peers.length; i++) {
    const peer = peers[i];
    console.log(`\n[${i + 1}/${peers.length}] ${peer.name}`);
    console.log(`  URL: ${peer.canonicalUrl}`);

    const peerTarget: PeerTarget = { id: peer.id, name: peer.name, canonicalUrl: peer.canonicalUrl };

    // Wrap browser page to match collector interface
    const browserAdapter = {
      async navigate(url: string) {
        await page.goto(url, { waitUntil: "domcontentloaded", timeout: PAGE_TIMEOUT_MS });
        // Wait for content
        await page.waitForTimeout(3000);
      },
      async snapshot() {
        return "";
      },
      async evaluate(fn: string | (() => unknown)) {
        if (typeof fn === "string") {
          return await page.evaluate(fn);
        }
        return await page.evaluate(fn);
      },
    };

    const result = await collectFromPage(browserAdapter, peerTarget, {
      maxPosts: MAX_POSTS_PER_PAGE,
      delayBetweenPagesMs: DELAY_BETWEEN_PAGES_MS,
      pageTimeoutMs: PAGE_TIMEOUT_MS,
    });

    console.log(`  Status: ${result.status}`);
    console.log(`  Posts: ${result.posts.length}`);
    console.log(`  Followers: ${result.followerCount ?? "—"}`);
    if (result.errors.length > 0) {
      console.log(`  Errors: ${result.errors.length}`);
      for (const e of result.errors.slice(0, 3)) console.log(`    - ${e.substring(0, 100)}`);
    }

    // Write to DB
    await writeToDB(result, collectedAt);

    results.push({
      peer: peerTarget,
      status: result.status,
      posts: result.posts.length,
      followerCount: result.followerCount,
      errors: result.errors,
    });

    // Delay before next page (except last)
    if (i < peers.length - 1) {
      console.log(`  Waiting ${DELAY_BETWEEN_PAGES_MS / 1000}s before next peer...`);
      await new Promise((r) => setTimeout(r, DELAY_BETWEEN_PAGES_MS));
    }
  }

  await browser.close();

  // Summary
  console.log("\n=== Collection Summary ===");
  const success = results.filter((r) => r.status === "success").length;
  const partial = results.filter((r) => r.status === "partial").length;
  const unavailable = results.filter((r) => r.status === "unavailable").length;
  const blocked = results.filter((r) => r.status === "blocked").length;
  console.log(`Success: ${success} | Partial: ${partial} | Unavailable: ${unavailable} | Blocked: ${blocked}`);
  console.log(`Total posts collected: ${results.reduce((s, r) => s + r.posts, 0)}`);

  await prisma.$disconnect();
}

async function writeToDB(result: { pageId: number; pageName: string; status: string; followerCount: number | null; posts: Array<{ postUrl: string; postedAt: string | null; textSnippet: string | null; reactions: number | null; comments: number | null; shares: number | null; videoViews: number | null; contentType: string; topicTag: string }>; errors: string[] }, collectedAt: Date) {
  const capturedAt = collectedAt;

  // Write BenchmarkPost records
  let postsWritten = 0;
  let postErrors = 0;

  for (const post of result.posts) {
    if (!post.postUrl) {
      postErrors++;
      continue;
    }

    const metrics = derivePostMetrics({
      reactions: post.reactions,
      comments: post.comments,
      shares: post.shares,
      publicVideoViews: post.videoViews,
    });

    try {
      await prisma.benchmarkPost.upsert({
        where: {
          benchmarkPageId_postUrl_capturedAt: {
            benchmarkPageId: result.pageId,
            postUrl: post.postUrl,
            capturedAt,
          },
        },
        create: {
          benchmarkPageId: result.pageId,
          postUrl: post.postUrl,
          postedAt: post.postedAt || null,
          textSnippet: post.textSnippet,
          contentType: post.contentType,
          topicTag: post.topicTag,
          reactions: metrics.reactions,
          comments: metrics.comments,
          shares: metrics.shares,
          publicVideoViews: metrics.publicVideoViews,
          reactionsObserved: metrics.reactionsObserved,
          commentsObserved: metrics.commentsObserved,
          sharesObserved: metrics.sharesObserved,
          publicVideoViewsObserved: metrics.publicVideoViewsObserved,
          comparableEngagement: metrics.comparableEngagement,
          observedPublicEngagement: metrics.observedPublicEngagement,
          metricCoverageScore: metrics.metricCoverageScore,
          source: "fb_session_collector",
          capturedAt,
        },
        update: {
          reactions: metrics.reactions,
          comments: metrics.comments,
          shares: metrics.shares,
          publicVideoViews: metrics.publicVideoViews,
          reactionsObserved: metrics.reactionsObserved,
          commentsObserved: metrics.commentsObserved,
          sharesObserved: metrics.sharesObserved,
          publicVideoViewsObserved: metrics.publicVideoViewsObserved,
          comparableEngagement: metrics.comparableEngagement,
          observedPublicEngagement: metrics.observedPublicEngagement,
          metricCoverageScore: metrics.metricCoverageScore,
        },
      });
      postsWritten++;
    } catch (e) {
      postErrors++;
    }
  }

  // Write audience snapshot if follower count found
  if (result.followerCount && result.followerCount > 0) {
    try {
      await prisma.benchmarkAudienceSnapshot.create({
        data: {
          benchmarkPageId: result.pageId,
          audienceCount: result.followerCount,
          audienceCountType: "followers",
          source: "fb_session_collector",
          verificationConfidence: "high",
          capturedAt,
        },
      });
    } catch {
      // P2002 or other — skip duplicate
    }
  }

  // Write CollectionLog
  await prisma.collectionLog.create({
    data: {
      benchmarkPageId: result.pageId,
      status: result.status,
      source: "fb_session_collector",
      postsCollected: postsWritten,
      postsWithError: postErrors,
      followerCount: result.followerCount,
      errors: JSON.stringify(result.errors.slice(0, 20)),
      collectedAt,
    },
  });

  // Update BenchmarkPage status
  await prisma.benchmarkPage.update({
    where: { id: result.pageId },
    data: {
      lastCollectedAt: collectedAt,
      collectionStatus: result.status,
      collectionErrors: JSON.stringify(result.errors.slice(0, 10)),
    },
  });

  console.log(`  DB: ${postsWritten} posts written, ${postErrors} errors`);
}

main().catch((e) => {
  console.error("Collection failed:", e);
  process.exit(1);
});
