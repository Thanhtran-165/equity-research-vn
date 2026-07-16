import { ok } from "@/lib/env";
import { publicEnvInfo } from "@/lib/env";

export const dynamic = "force-dynamic";

/**
 * GET /api/env
 * Trả thông tin cấu hình env (KHÔNG trả token đầy đủ).
 */
export async function GET() {
  return ok(publicEnvInfo());
}
