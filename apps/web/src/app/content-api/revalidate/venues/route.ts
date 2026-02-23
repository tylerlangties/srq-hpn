import { revalidatePath, revalidateTag } from "next/cache";
import { NextResponse } from "next/server";

type RevalidatePayload = {
  slug?: string;
};

export async function POST(request: Request) {
  const configuredToken = process.env.WEB_REVALIDATE_TOKEN;
  const providedToken = request.headers.get("x-revalidate-token");

  if (!configuredToken || providedToken !== configuredToken) {
    return NextResponse.json({ ok: false, error: "Unauthorized" }, { status: 401 });
  }

  let payload: RevalidatePayload = {};
  try {
    payload = (await request.json()) as RevalidatePayload;
  } catch {
    payload = {};
  }

  const slug = typeof payload.slug === "string" ? payload.slug.trim() : "";

  revalidatePath("/venues");
  revalidateTag("venues", "max");

  if (slug) {
    revalidatePath(`/venues/${slug}`);
    revalidateTag(`venue:${slug}`, "max");
    revalidateTag(`venue:${slug}:events`, "max");
  }

  revalidatePath("/sitemap.xml");

  return NextResponse.json({ ok: true, slug: slug || null });
}
