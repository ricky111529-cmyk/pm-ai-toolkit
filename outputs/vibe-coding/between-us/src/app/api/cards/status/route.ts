import { NextResponse } from "next/server";
import { hashSecret } from "@/lib/pairing";
import { getSupabaseAdmin } from "@/lib/supabase";

export async function POST(request: Request) {
  try {
    const { roomId, accessToken } = await request.json();
    if (typeof roomId !== "string" || typeof accessToken !== "string") return NextResponse.json({ error: "INVALID_INPUT" }, { status: 400 });
    const tokenHash = hashSecret(accessToken);
    const supabase = getSupabaseAdmin();
    const { data: room, error } = await supabase
      .from("card_rooms")
      .select("id, card_id, creator_name, creator_response, partner_name, partner_response, status, expires_at")
      .eq("id", roomId)
      .or(`creator_token_hash.eq.${tokenHash},partner_token_hash.eq.${tokenHash}`)
      .maybeSingle();

    if (error || !room) return NextResponse.json({ error: "NOT_FOUND" }, { status: 404 });
    if (new Date(room.expires_at) < new Date()) return NextResponse.json({ status: "expired" });
    if (room.status !== "paired") return NextResponse.json({ status: "waiting" });
    return NextResponse.json({ status: "paired", room });
  } catch {
    return NextResponse.json({ error: "STATUS_FAILED" }, { status: 500 });
  }
}
