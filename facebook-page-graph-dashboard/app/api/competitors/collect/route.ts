import { prisma } from "@/lib/prisma";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * POST /api/competitors/collect
 *
 * This route does NOT run Playwright directly (it requires a browser process).
 * Instead, it signals the collection script to run, or returns instructions.
 *
 * The actual collection is done via CLI: `npm run collect:competitors`
 * or via the dashboard "Collect Now" button which triggers the CLI.
 *
 * This endpoint tracks the collection run state and provides the trigger info.
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    const body = await req.json().catch(() => ({}));
    const pilot = body.pilot === true;

    const peers = await prisma.benchmarkPage.findMany({
      where: { benchmarkRole: "core_peer", isOwnPage: false },
      select: { id: true, name: true, canonicalUrl: true },
      orderBy: { name: "asc" },
      ...(pilot ? { take: 3 } : {}),
    });

    return ok({
      message: pilot
        ? "Pilot collection: run `npm run collect:competitors -- --pilot` in terminal"
        : "Full collection: run `npm run collect:competitors` in terminal",
      command: pilot
        ? "npm run collect:competitors -- --pilot"
        : "npm run collect:competitors",
      peers: peers.map((p) => ({ id: p.id, name: p.name, url: p.canonicalUrl })),
      peerCount: peers.length,
      maxPosts: 5,
      delaySeconds: 30,
      estimatedTime: `${Math.ceil((peers.length * (30 + 10)) / 60)} minutes`,
      note: "Browser will open. Make sure you're logged into Facebook. Collection runs with visible browser.",
    });
  });
}
