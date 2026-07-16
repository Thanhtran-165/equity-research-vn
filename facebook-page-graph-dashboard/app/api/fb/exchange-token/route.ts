import { NextResponse } from "next/server";
import { exchangeUserToPageToken, getLongLivedUserToken } from "@/lib/facebook";
import { ok, err, withFbErrors } from "@/lib/env";
import * as fs from "fs";
import * as path from "path";

export const dynamic = "force-dynamic";

interface RequestBody {
  /** Short-lived hoặc long-lived USER access token. */
  userToken: string;
  /** Optional Page ID nếu user quản lý nhiều Page. */
  pageId?: string;
  /** Optional: exchange sang long-lived user token (60 ngày) trước khi lấy page token. */
  longLived?: boolean;
  /** Optional: ghi đè token vào .env.local + .env ngay (default true). */
  updateEnv?: boolean;
}

/**
 * POST /api/fb/exchange-token
 * Body: { userToken, pageId?, longLived?, updateEnv? }
 *
 * Flow:
 * 1. (optional) short-lived → long-lived user token (60 ngày).
 * 2. user token → page token qua /me/accounts.
 * 3. (optional) ghi page token vào .env.local + .env.
 *
 * Trả: { pageId, pageName, pageAccessToken (masked), expiresAt }
 */
export async function POST(req: Request) {
  return withFbErrors(async () => {
    let body: RequestBody;
    try {
      body = await req.json();
    } catch {
      return err("unknown_error", "Body không phải JSON hợp lệ", 400);
    }

    const userToken = (body.userToken ?? "").toString().trim();
    if (!userToken) {
      return err("unknown_error", "Thiếu body.userToken", 400);
    }

    let workingUserToken = userToken;
    let longLivedExpiresAt: number | null = null;

    if (body.longLived) {
      const ll = await getLongLivedUserToken(userToken);
      workingUserToken = ll.longLivedToken;
      longLivedExpiresAt = ll.expiresAt;
    }

    const page = await exchangeUserToPageToken(workingUserToken, body.pageId);

    const updateEnv = body.updateEnv !== false;
    if (updateEnv) {
      const updated = updateEnvFiles({
        pageId: page.pageId,
        pageAccessToken: page.pageAccessToken,
        userToken: body.longLived ? workingUserToken : undefined,
      });
      if (!updated) {
        return ok({
          ...serializeExchangedToken(page, longLivedExpiresAt),
          envUpdated: false,
          warning: "Không đọc/ghi được .env.local — token trả về trong response, bạn tự cập nhật.",
        });
      }
    }

    return ok({
      ...serializeExchangedToken(page, longLivedExpiresAt),
      envUpdated: updateEnv,
    });
  });
}

function serializeExchangedToken(
  page: { pageId: string; pageName: string; pageAccessToken: string; tasks: string[] },
  longLivedExpiresAt: number | null,
) {
  const t = page.pageAccessToken;
  const masked = t.length > 12 ? `${t.slice(0, 6)}…${t.slice(-4)}` : "***";
  return {
    pageId: page.pageId,
    pageName: page.pageName,
    pageAccessTokenMasked: masked,
    pageAccessTokenLength: t.length,
    tasks: page.tasks,
    longLivedExpiresAt,
  };
}

/**
 * Update .env.local + .env với page ID + page token (optional: user token).
 * Trả true nếu update thành công cả 2, false nếu fail.
 */
function updateEnvFiles(args: {
  pageId: string;
  pageAccessToken: string;
  userToken?: string;
}): boolean {
  const projectRoot = process.cwd();
  const files = [".env.local", ".env"];
  let allOk = true;

  for (const fname of files) {
    const fpath = path.join(projectRoot, fname);
    try {
      if (!fs.existsSync(fpath)) {
        // Tạo file .env.local/.env nếu chưa có
        fs.writeFileSync(fpath, "", { mode: 0o600 });
      }
      let content = fs.readFileSync(fpath, "utf8");

      // Update FB_PAGE_ID
      content = upsertEnvLine(content, "FB_PAGE_ID", args.pageId);
      // Update FB_PAGE_ACCESS_TOKEN
      content = upsertEnvLine(content, "FB_PAGE_ACCESS_TOKEN", args.pageAccessToken);
      // Optional: update FB_USER_ACCESS_TOKEN
      if (args.userToken) {
        content = upsertEnvLine(content, "FB_USER_ACCESS_TOKEN", args.userToken);
      }

      fs.writeFileSync(fpath, content, { mode: 0o600 });
    } catch (e) {
      console.error(`[exchange-token] Lỗi update ${fname}:`, e);
      allOk = false;
    }
  }
  return allOk;
}

function upsertEnvLine(content: string, key: string, value: string): string {
  const lines = content.split(/\r?\n/);
  const regex = new RegExp(`^${key}=.*$`);
  let found = false;
  const out = lines.map((line) => {
    if (regex.test(line)) {
      found = true;
      return `${key}=${value}`;
    }
    return line;
  });
  if (!found) {
    out.push(`${key}=${value}`);
  }
  return out.join("\n");
}
