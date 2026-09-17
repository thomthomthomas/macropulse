import { revalidatePath } from "next/cache";

// Called by the GitHub Action right after the daily update.
export async function POST(request: Request) {
  const secret = process.env.REVALIDATE_SECRET;
  if (!secret || request.headers.get("x-revalidate-secret") !== secret) {
    return Response.json({ ok: false }, { status: 401 });
  }
  revalidatePath("/");
  return Response.json({ ok: true, revalidated: "/", at: new Date().toISOString() });
}
