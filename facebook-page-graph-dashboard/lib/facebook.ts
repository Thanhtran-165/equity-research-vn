/**
 * Server-side Facebook Graph API client.
 *
 * Bảo mật:
 * - Token CHỈ lấy từ process.env, KHÔNG bao giờ truyền từ client lên.
 * - KHÔNG log full token. Nếu cần log, dùng maskToken().
 * - Tất cả API call đều server-side.
 *
 * Lưu ý version: FB_API_VERSION lấy từ env (mặc định v25.0). Khi Meta bump
 * version, các field/metric có thể thay đổi → fbGet có fallback & warning.
 */

export type FbError =
  | "missing_token"
  | "missing_permission"
  | "invalid_token"
  | "rate_limit"
  | "unsupported_metric"
  | "unknown_error";

export class FacebookApiError extends Error {
  code: FbError;
  fbErrorType?: string;
  fbErrorCode?: number;
  fbSubcode?: number;
  status: number;
  constructor(
    code: FbError,
    message: string,
    opts?: {
      status?: number;
      fbErrorType?: string;
      fbErrorCode?: number;
      fbSubcode?: number;
    },
  ) {
    super(message);
    this.name = "FacebookApiError";
    this.code = code;
    this.status = opts?.status ?? 502;
    this.fbErrorType = opts?.fbErrorType;
    this.fbErrorCode = opts?.fbErrorCode;
    this.fbSubcode = opts?.fbSubcode;
  }
}

// ---------- env helpers ----------

export function getApiVersion(): string {
  // Luôn đọc từ env; fallback an toàn nếu người dùng quên set.
  return (process.env.FB_API_VERSION ?? "v25.0").replace(/^v/, "v");
}

export function getGraphBaseUrl(): string {
  const v = getApiVersion();
  return `https://graph.facebook.com/${v}`;
}

export function getPageAccessToken(): string {
  return process.env.FB_PAGE_ACCESS_TOKEN ?? "";
}

export function getUserAccessToken(): string {
  return process.env.FB_USER_ACCESS_TOKEN ?? "";
}

export function getPageId(): string {
  return process.env.FB_PAGE_ID ?? "";
}

/**
 * Mask token: chỉ hiện 6 ký tự đầu và 4 ký tự cuối.
 */
export function maskToken(token: string | null | undefined): string {
  if (!token) return "";
  const t = String(token);
  if (t.length <= 12) return "***";
  return `${t.slice(0, 6)}…${t.slice(-4)}`;
}

// ---------- core GET ----------

type FbGetParams = Record<string, string | number | boolean | undefined>;

function buildQuery(params: FbGetParams, accessToken: string): string {
  const url = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null) continue;
    url.set(k, String(v));
  }
  url.set("access_token", accessToken);
  return url.toString();
}

/**
 * Gọi GET tới Graph API.
 * @param path ví dụ: "/me/accounts" hoặc "<PAGE_ID>/posts"
 * @param params query params (KHÔNG bao gồm access_token)
 */
export async function fbGet<T = any>(
  path: string,
  params?: FbGetParams,
  opts?: { token?: string; raw?: boolean },
): Promise<T> {
  const token = opts?.token ?? getPageAccessToken();
  if (!token) {
    throw new FacebookApiError("missing_token", "Thiếu FB_PAGE_ACCESS_TOKEN trong .env.local", {
      status: 500,
    });
  }

  const base = getGraphBaseUrl();
  const cleanPath = path.startsWith("/") ? path.slice(1) : path;
  const url = `${base}/${cleanPath}?${buildQuery(params ?? {}, token)}`;

  let resp: Response;
  try {
    resp = await fetch(url, { method: "GET" });
  } catch (e: any) {
    throw new FacebookApiError("unknown_error", `Network error: ${e?.message ?? e}`, {
      status: 502,
    });
  }

  let body: any;
  try {
    body = await resp.json();
  } catch {
    body = null;
  }

  if (!resp.ok || body?.error) {
    throw mapFbError(resp.status, body?.error);
  }

  return body as T;
}

function mapFbError(status: number, error: any): FacebookApiError {
  const type: string = error?.type ?? "";
  const code: number | undefined = error?.code;
  const subcode: number | undefined = error?.error_subcode;
  const msg: string = error?.message ?? `HTTP ${status}`;

  // Các case phổ biến (có thể thay đổi theo version → để fallback an toàn)
  // OAuthException + code 190 => invalid/expired token
  if (code === 190) {
    return new FacebookApiError("invalid_token", msg, {
      status,
      fbErrorType: type,
      fbErrorCode: code,
      fbSubcode: subcode,
    });
  }
  // code 4, 17, 32, 613 => rate limit
  if (code === 4 || code === 17 || code === 32 || code === 613) {
    return new FacebookApiError("rate_limit", msg, {
      status: 429,
      fbErrorType: type,
      fbErrorCode: code,
      fbSubcode: subcode,
    });
  }
  // code 10, 200, 298 => permission
  if (code === 10 || code === 200 || code === 298) {
    return new FacebookApiError("missing_permission", msg, {
      status,
      fbErrorType: type,
      fbErrorCode: code,
      fbSubcode: subcode,
    });
  }
  // unsupported metric
  if (
    /does not support|unsupported|not supported/i.test(msg) ||
    code === 100 && /metric/i.test(msg)
  ) {
    return new FacebookApiError("unsupported_metric", msg, {
      status,
      fbErrorType: type,
      fbErrorCode: code,
      fbSubcode: subcode,
    });
  }

  return new FacebookApiError("unknown_error", msg, {
    status,
    fbErrorType: type,
    fbErrorCode: code,
    fbSubcode: subcode,
  });
}

// ---------- high-level helpers ----------

export interface PageInfo {
  pageId: string;
  name: string;
  followersCount: number;
  fanCount: number;
}

export async function getPageInfo(token?: string): Promise<PageInfo> {
  const pageId = getPageId();
  if (!pageId) {
    throw new FacebookApiError("missing_token", "Thiếu FB_PAGE_ID trong .env.local", {
      status: 500,
    });
  }
  const data = await fbGet<any>(`/${pageId}`, {
    fields: "id,name,followers_count,fan_count",
  }, token ? { token } : undefined);
  return {
    pageId: data.id,
    name: data.name ?? "",
    followersCount: data.followers_count ?? 0,
    fanCount: data.fan_count ?? 0,
  };
}

export interface FbAccount {
  id: string;
  name: string;
  hasAccessToken: boolean;
  tasks: string[];
}

export async function getAccountsFromUserToken(): Promise<FbAccount[]> {
  const userToken = getUserAccessToken();
  if (!userToken) {
    throw new FacebookApiError(
      "missing_token",
      "Thiếu FB_USER_ACCESS_TOKEN trong .env.local (cần cho helper /api/fb/accounts)",
      { status: 500 },
    );
  }
  const data = await fbGet<any>(
    "/me/accounts",
    {
      fields: "id,name,access_token,tasks",
      limit: 100,
    },
    { token: userToken },
  );
  const arr: any[] = data?.data ?? [];
  return arr.map((a) => ({
    id: a.id,
    name: a.name ?? "",
    hasAccessToken: Boolean(a.access_token),
    tasks: Array.isArray(a.tasks) ? a.tasks : [],
  }));
}

// ---------- Token exchange & refresh ----------

export interface ExchangedPageToken {
  pageId: string;
  pageName: string;
  pageAccessToken: string;
  tasks: string[];
}

/**
 * Đổi USER Access Token → PAGE Access Token qua /me/accounts.
 * Page token có quyền cao hơn cho Page-level endpoints và thường không expire
 * (khi App ở Live mode + User token còn hạn).
 *
 * @param userToken USER Access Token (lấy từ Graph API Explorer)
 * @param targetPageId Optional — nếu có nhiều Page, chọn Page này; nếu không, lấy Page đầu.
 */
export async function exchangeUserToPageToken(
  userToken: string,
  targetPageId?: string,
): Promise<ExchangedPageToken> {
  if (!userToken) {
    throw new FacebookApiError("missing_token", "Thiếu userToken tham số", { status: 400 });
  }
  const data = await fbGet<any>(
    "/me/accounts",
    { fields: "id,name,access_token,tasks", limit: 100 },
    { token: userToken },
  );
  const arr: any[] = data?.data ?? [];
  if (arr.length === 0) {
    throw new FacebookApiError(
      "missing_permission",
      "User token không quản lý Page nào, hoặc thiếu permission pages_show_list.",
      { status: 403 },
    );
  }
  const chosen = targetPageId
    ? arr.find((a) => a.id === targetPageId)
    : arr[0];
  if (!chosen) {
    throw new FacebookApiError(
      "unknown_error",
      `Không tìm thấy Page id=${targetPageId} trong danh sách user quản lý.`,
      { status: 404 },
    );
  }
  return {
    pageId: chosen.id,
    pageName: chosen.name ?? "",
    pageAccessToken: chosen.access_token,
    tasks: Array.isArray(chosen.tasks) ? chosen.tasks : [],
  };
}

/**
 * Đổi short-lived USER token → long-lived USER token (60 ngày) qua
 * oauth/access_token grant_type=fb_exchange_token.
 * Yêu cầu FB_APP_ID + FB_APP_SECRET trong env.
 *
 * @returns long-lived user token (60 ngày)
 */
export async function getLongLivedUserToken(shortLivedUserToken: string): Promise<{
  longLivedToken: string;
  expiresAt: number; // unix timestamp
  tokenType: string;
}> {
  const appId = process.env.FB_APP_ID;
  const appSecret = process.env.FB_APP_SECRET;
  if (!appId || !appSecret) {
    throw new FacebookApiError(
      "missing_token",
      "Thiếu FB_APP_ID hoặc FB_APP_SECRET trong env (cần cho exchange sang long-lived).",
      { status: 500 },
    );
  }
  const v = getApiVersion();
  const url = `https://graph.facebook.com/${v}/oauth/access_token?grant_type=fb_exchange_token&client_id=${appId}&client_secret=${appSecret}&fb_exchange_token=${shortLivedUserToken}`;
  let resp: Response;
  try {
    resp = await fetch(url, { method: "GET" });
  } catch (e: any) {
    throw new FacebookApiError("unknown_error", `Network error: ${e?.message ?? e}`, { status: 502 });
  }
  let body: any;
  try {
    body = await resp.json();
  } catch {
    body = null;
  }
  if (!resp.ok || body?.error) {
    throw mapFbError(resp.status, body?.error);
  }
  return {
    longLivedToken: body.access_token,
    expiresAt: body.expires_in ? Math.floor(Date.now() / 1000) + body.expires_in : 0,
    tokenType: body.token_type ?? "MAC",
  };
}

export interface FbPostRaw {
  id: string;
  message?: string;
  created_time?: string;
  permalink_url?: string;
  shares?: { count: number };
  comments?: { summary?: { total_count: number } };
  reactions?: { summary?: { total_count: number } };
  attachments?: { data?: any[] };
}

export async function getRecentPosts(limit = 25): Promise<FbPostRaw[]> {
  const pageId = getPageId();
  if (!pageId) {
    throw new FacebookApiError("missing_token", "Thiếu FB_PAGE_ID", { status: 500 });
  }
  const data = await fbGet<any>(`/${pageId}/posts`, {
    fields:
      "id,message,created_time,permalink_url,shares,comments.summary(true).limit(0),reactions.summary(true).limit(0),attachments{media_type,type,target,url}",
    limit,
  });
  return (data?.data ?? []) as FbPostRaw[];
}

export interface PostInsights {
  /** True reach từ post_impressions_unique. NULL nếu không có (App Dev mode). */
  reach?: number;
  impressions?: number;
  engagedUsers?: number;
  clicks?: number;
  /** Video views (metric thật cho video/reel, KHÔNG phải reach). */
  videoViews?: number;
  /** Public engagement = reactions + comments + shares (proxy, KHÔNG phải reach). */
  publicEngagement?: number;
  warnings: string[];
}

/**
 * Lấy insight cho post. Trả warning nếu metric không hỗ trợ thay vì throw.
 */
/**
 * Lấy insight cho post — trả 3 metric KHÔNG trộn:
 *  - reach (post_impressions_unique)      → true reach
 *  - videoViews (post_video_views)         → metric thật cho video, không phải reach
 *  - publicEngagement (reactions+cmt+share) → proxy, không phải reach
 *
 * KHÔNG tự fallback reach = proxy. Logic hiển thị do UI quyết định.
 */
export async function getPostInsights(postId: string): Promise<PostInsights> {
  const warnings: string[] = [];
  const result: PostInsights = { warnings };

  // 1. Insights chính thức (reach, impressions, engaged_users, clicks)
  const primaryMetrics = [
    { metric: "post_impressions_unique", key: "reach" as const },
    { metric: "post_impressions", key: "impressions" as const },
    { metric: "post_engaged_users", key: "engagedUsers" as const },
    { metric: "post_clicks", key: "clicks" as const },
  ];

  await Promise.all(
    primaryMetrics.map(async ({ metric, key }) => {
      try {
        const data = await fbGet<any>(`/${postId}/insights`, {
          metric,
          period: "lifetime",
        });
        const val = data?.data?.[0]?.values?.[0]?.value;
        if (typeof val === "number") {
          (result as any)[key] = val;
        }
      } catch (e: any) {
        if (e instanceof FacebookApiError && e.code === "missing_permission") throw e;
        // Không push warning cho metric fail — tránh noise. UI tự xử lý null.
      }
    }),
  );

  // 2. Video views (metric riêng, không phải reach)
  try {
    const data = await fbGet<any>(`/${postId}/insights`, {
      metric: "post_video_views",
      period: "lifetime",
    });
    const val = data?.data?.[0]?.values?.[0]?.value;
    if (typeof val === "number") {
      result.videoViews = val;
    }
  } catch {
    // ignore — không phải video post
  }

  // 3. Public engagement proxy (reactions + comments + shares)
  try {
    const proxy = await getPostPublicProxy(postId);
    result.publicEngagement = proxy.publicEngagement;
  } catch (e: any) {
    warnings.push(`Không lấy được public engagement: ${e?.message ?? e}`);
  }

  return result;
}

/**
 * Lấy public proxy metrics cho 1 post: reactions + comments + shares.
 * Dùng làm fallback reach khi Graph API không trả post_impressions_unique.
 */
export async function getPostPublicProxy(postId: string): Promise<{
  reactions: number;
  comments: number;
  shares: number;
  publicEngagement: number;
}> {
  const data = await fbGet<any>(`/${postId}`, {
    fields: "reactions.summary(true).limit(0),comments.summary(true).limit(0),shares",
  });
  const reactions = data?.reactions?.summary?.total_count ?? 0;
  const comments = data?.comments?.summary?.total_count ?? 0;
  const shares = data?.shares?.count ?? 0;
  return { reactions, comments, shares, publicEngagement: reactions + comments + shares };
}

export interface FbCommentRaw {
  id: string;
  message?: string;
  created_time?: string;
  like_count?: number;
  comment_count?: number;
}

export async function getPostComments(postId: string, limit = 100): Promise<FbCommentRaw[]> {
  const data = await fbGet<any>(`/${postId}/comments`, {
    fields: "id,message,created_time,like_count,comment_count",
    limit,
    order: "reverse_chronological",
  });
  return (data?.data ?? []) as FbCommentRaw[];
}

export interface VideoInsights {
  views?: number;
  uniqueViews?: number;
  avgWatchTime?: number;
  reach?: number;
  warnings: string[];
}

/**
 * Lấy insight video. Graph API có thể yêu cầu quyền video hoặc metric
 * thay đổi theo version → dùng fallback, không crash.
 */
export async function getVideoInsights(videoId: string): Promise<VideoInsights> {
  const warnings: string[] = [];
  const result: VideoInsights = { warnings };

  const fields = [
    "total_video_views",
    "total_video_views_unique",
    "avg_video_view_time",
    "total_video_views_autoplayed",
  ];

  // Thử endpoint /video/insights (metric lifetime)
  try {
    const data = await fbGet<any>(`/${videoId}/video_insights`, {
      metric: fields.join(","),
    });
    const arr = data?.data ?? [];
    for (const row of arr) {
      const val = row?.values?.[0]?.value;
      if (typeof val !== "number") continue;
      switch (row.name) {
        case "total_video_views":
          result.views = (result.views ?? 0) + val;
          break;
        case "total_video_views_unique":
          result.uniqueViews = (result.uniqueViews ?? 0) + val;
          break;
        case "avg_video_view_time":
          result.avgWatchTime = val;
          break;
      }
    }
  } catch (e: any) {
    if (e instanceof FacebookApiError) {
      warnings.push(`video_insights lỗi (${e.code}): ${e.message}`);
    } else {
      warnings.push(`video_insights lỗi: ${e?.message ?? e}`);
    }
  }

  // Reach riêng (nếu được phép)
  try {
    const reachData = await fbGet<any>(`/${videoId}/insights`, {
      metric: "post_impressions_unique",
      period: "lifetime",
    });
    const v = reachData?.data?.[0]?.values?.[0]?.value;
    if (typeof v === "number") result.reach = v;
  } catch (e: any) {
    if (e instanceof FacebookApiError && e.code !== "unsupported_metric") {
      warnings.push(`video reach lỗi: ${e.message}`);
    }
  }

  return result;
}
