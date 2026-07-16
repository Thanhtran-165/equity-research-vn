import { getRecentPosts, type FbPostRaw } from "@/lib/facebook";
import { detectTopic, TOPIC_LABEL_VI, type Topic } from "@/lib/topics";
import { ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

export interface PostsItem {
  fbPostId: string;
  message: string | null;
  createdTime: string | null;
  permalinkUrl: string | null;
  postType: "text" | "photo" | "video_or_reel" | "link" | "unknown";
  topic: Topic;
  topicLabel: string;
  reactionsCount: number;
  commentsCount: number;
  sharesCount: number;
}

function detectPostType(raw: FbPostRaw): PostsItem["postType"] {
  const attachments = raw.attachments?.data ?? [];
  if (attachments.length === 0) {
    return raw.message ? "text" : "unknown";
  }
  const first = attachments[0];
  const mediaType: string | undefined = first?.media_type;
  const type: string | undefined = first?.type;
  // video / reel
  if (mediaType === "video" || type === "video_inline" || type === "video") {
    return "video_or_reel";
  }
  if (mediaType === "photo" || type === "photo") return "photo";
  if (type === "share" || type === "link") return "link";
  if (mediaType === "album") return "photo";
  return "unknown";
}

export async function GET(req: Request) {
  return withFbErrors(async () => {
    const url = new URL(req.url);
    const limitRaw = url.searchParams.get("limit");
    const limit = Math.max(1, Math.min(100, Number(limitRaw) || 25));

    const raw = await getRecentPosts(limit);
    const items: PostsItem[] = raw.map((r) => {
      const topic = detectTopic(r.message);
      return {
        fbPostId: r.id,
        message: r.message ?? null,
        createdTime: r.created_time ?? null,
        permalinkUrl: r.permalink_url ?? null,
        postType: detectPostType(r),
        topic,
        topicLabel: TOPIC_LABEL_VI[topic],
        reactionsCount: r.reactions?.summary?.total_count ?? 0,
        commentsCount: r.comments?.summary?.total_count ?? 0,
        sharesCount: r.shares?.count ?? 0,
      };
    });

    return ok({ posts: items });
  });
}
