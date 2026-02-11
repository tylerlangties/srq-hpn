import { NextResponse } from "next/server";
import { getArticleSummaries } from "@/lib/articles";

export const dynamic = "force-static";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const limitParam = searchParams.get("limit");
  const limit = limitParam ? Number.parseInt(limitParam, 10) : undefined;
  const articles = await getArticleSummaries({ limit });

  return NextResponse.json({ articles });
}
