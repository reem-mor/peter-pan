import { NextRequest, NextResponse } from "next/server";
import { meshFetch } from "@/lib/backend";

export const runtime = "nodejs";

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(_req: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  const suffix = path.join("/");
  const upstream = await meshFetch("ppos", `/os/${suffix}`);
  const text = await upstream.text();
  return new NextResponse(text, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("Content-Type") ?? "application/json" },
  });
}
