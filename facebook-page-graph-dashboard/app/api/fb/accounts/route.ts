import { getAccountsFromUserToken } from "@/lib/facebook";
import { err, ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * Helper lấy danh sách Page mà user quản lý.
 * Yêu cầu FB_USER_ACCESS_TOKEN.
 * KHÔNG trả access_token đầy đủ ra frontend (chỉ hasAccessToken: true/false).
 */
export async function GET() {
  return withFbErrors(async () => {
    const accounts = await getAccountsFromUserToken();
    return ok({ accounts });
  });
}
