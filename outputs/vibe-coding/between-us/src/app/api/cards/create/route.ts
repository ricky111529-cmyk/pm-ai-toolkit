import { NextResponse } from "next/server";
import { cleanCardId, cleanName, hashSecret, isResponse, makeAccessToken, makeShareCode } from "@/lib/pairing";
import { getSupabaseAdmin } from "@/lib/supabase";

export async function POST(request: Request) {
  try {
    const { cardId, name, response } = await request.json();
    const validCardId = cleanCardId(cardId);
    const validName = cleanName(name);
    if (!validCardId || !validName || !isResponse(response)) {
      return NextResponse.json({ error: "INVALID_INPUT" }, { status: 400 });
    }

    const shareCode = makeShareCode();
    const accessToken = makeAccessToken();
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();
    const supabase = getSupabaseAdmin();
    const { data, error } = await supabase
      .from("card_rooms")
      .insert({
        card_id: validCardId,
        creator_name: validName,
        creator_response: response,
        creator_token_hash: hashSecret(accessToken),
        share_code_hash: hashSecret(shareCode),
        expires_at: expiresAt
      })
      .select("id, card_id, expires_at")
      .single();

    if (error || !data) throw error ?? new Error("CREATE_FAILED");
    return NextResponse.json({ roomId: data.id, cardId: data.card_id, shareCode, accessToken, expiresAt: data.expires_at });
  } catch (error) {
    const configured = !(error instanceof Error && error.message === "SUPABASE_NOT_CONFIGURED");
    return NextResponse.json({ error: configured ? "CREATE_FAILED" : "SUPABASE_NOT_CONFIGURED" }, { status: configured ? 500 : 503 });
  }
}
