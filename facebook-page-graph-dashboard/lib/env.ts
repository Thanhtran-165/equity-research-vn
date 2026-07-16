/**
 * Helpers chia sẻ giữa các API route (server-only).
 */
import { NextResponse } from "next/server";
import { FacebookApiError, maskToken } from "./facebook";

export interface ApiOk<T> {
  ok: true;
  data: T;
}

export interface ApiErr {
  ok: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
}

export type ApiResponse<T> = ApiOk<T> | ApiErr;

export function ok<T>(data: T, status = 200): NextResponse {
  return NextResponse.json({ ok: true, data } as ApiOk<T>, { status });
}

export function err(code: string, message: string, status = 500, details?: any): NextResponse {
  return NextResponse.json(
    { ok: false, error: { code, message, details } } as ApiErr,
    { status },
  );
}

/**
 * Wrap một async handler, tự map FacebookApiError & unknown error sang JSON.
 */
export function withFbErrors<T>(
  fn: () => Promise<NextResponse>,
): Promise<NextResponse> {
  return fn().catch((e) => {
    if (e instanceof FacebookApiError) {
      return err(e.code, e.message, e.status, {
        fbErrorType: e.fbErrorType,
        fbErrorCode: e.fbErrorCode,
        fbSubcode: e.fbSubcode,
        tokenHint: "Kiểm tra FB_PAGE_ACCESS_TOKEN / FB_PAGE_ID trong .env.local",
      });
    }
    const msg = e?.message ?? String(e);
    return err("unknown_error", msg, 500);
  });
}

export function publicEnvInfo() {
  const hasPageId = Boolean(process.env.FB_PAGE_ID);
  const hasPageToken = Boolean(process.env.FB_PAGE_ACCESS_TOKEN);
  const hasUserToken = Boolean(process.env.FB_USER_ACCESS_TOKEN);
  return {
    apiVersion: process.env.FB_API_VERSION ?? "v25.0",
    hasPageId,
    pageId: process.env.FB_PAGE_ID ?? "",
    hasPageToken,
    pageTokenMasked: maskToken(process.env.FB_PAGE_ACCESS_TOKEN),
    hasUserToken,
    userTokenMasked: maskToken(process.env.FB_USER_ACCESS_TOKEN),
  };
}
