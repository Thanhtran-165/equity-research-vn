import { getPostInsights } from "@/lib/facebook";
import { err, ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const postId = url.searchParams.get("postId");
    if (!postId) {
      return err("unknown_error", "Thiếu query param postId", 400);
    }
    const insights = await getPostInsights(postId);
    return ok(insights);
  });
}
