import { NextResponse } from "next/server";
import { getPageInfo } from "@/lib/facebook";
import { err, ok, withFbErrors } from "@/lib/env";

export const dynamic = "force-dynamic";

export async function GET() {
  return withFbErrors(async () => {
    const info = await getPageInfo();
    return ok(info);
  });
}
