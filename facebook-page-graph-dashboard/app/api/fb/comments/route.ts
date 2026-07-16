import { getPostComments } from "@/lib/facebook";
import { moderateComment } from "@/lib/moderation";
import { err, ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const postId = url.searchParams.get("postId");
    if (!postId) {
      return err("unknown_error", "Thiếu query param postId", 400);
    }
    const limitRaw = url.searchParams.get("limit");
    const limit = Math.max(1, Math.min(100, Number(limitRaw) || 100));

    const raw = await getPostComments(postId, limit);
    const items = raw.map((c) => {
      const mod = moderateComment(c.message);
      return {
        fbCommentId: c.id,
        fbPostId: postId,
        message: c.message ?? null,
        createdTime: c.created_time ?? null,
        likeCount: c.like_count ?? 0,
        commentCount: c.comment_count ?? 0,
        keywordFlag: mod.keywordFlag,
        sentiment: mod.sentiment,
        riskLevel: mod.riskLevel,
        suggestedAction: mod.suggestedAction,
        suggestedReply: mod.suggestedReply,
      };
    });

    return ok({ comments: items });
  });
}
