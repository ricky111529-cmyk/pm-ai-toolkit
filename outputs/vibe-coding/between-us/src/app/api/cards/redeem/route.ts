import { NextResponse } from "next/server";
import { cleanCardId, cleanName, hashSecret, isResponse, makeAccessToken, normalizeShareCode } from "@/lib/pairing";
import { getSupabaseAdmin } from "@/lib/supabase";

export async function POST(request: Request) {
  try {
    const { cardId, name, response, shareCode } = await request.json();
    const validCardId = cleanCardId(cardId);
    const validName = cleanName(name);
    const normalizedCode = typeof shareCode === "string" ? normalizeShareCode(shareCode) : "";
    if (!validCardId || !validName || !normalizedCode || !isResponse(response)) {
      return NextResponse.json({ error: "INVALID_INPUT" }, { status: 400 });
    }

    const supabase = getSupabaseAdmin();
    const { data: room, error: lookupError } = await supabase
      .from("card_rooms")
      .select("id, card_id, creator_name, creator_response, status, expires_at")
      .eq("share_code_hash", hashSecret(normalizedCode))
      .maybeSingle();

    if (lookupError || !room || room.card_id !== validCardId || room.status !== "waiting" || new Date(room.expires_at) < new Date()) {
      return NextResponse.json({ error: "CODE_NOT_AVAILABLE" }, { status: 404 });
    }

    const accessToken = makeAccessToken();
    const { data: updatedRoom, error: updateError } = await supabase
      .from("card_rooms")
      .update({
        partner_name: validName,
        partner_response: response,
        partner_token_hash: hashSecret(accessToken),
        status: "paired",
        paired_at: new Date().toISOString()
      })
      .eq("id", room.id)
      .eq("status", "waiting")
      .select("id")
      .maybeSingle();

    if (updateError || !updatedRoom) return NextResponse.json({ error: "CODE_NOT_AVAILABLE" }, { status: 409 });
    return NextResponse.json({ roomId: room.id, accessToken, creatorName: room.creator_name, creatorResponse: room.creator_response, partnerName: validName, partnerResponse: response });
  } catch (error) {
    const configured = !(error instanceof Error && error.message === "SUPABASE_NOT_CONFIGURED");
    return NextResponse.json({ error: configured ? "REDEEM_FAILED" : "SUPABASE_NOT_CONFIGURED" }, { status: configured ? 500 : 503 });
  }
}
