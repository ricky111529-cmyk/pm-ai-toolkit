import { NextResponse } from "next/server";
import { cleanCardId, isDraftResponse, isResponse } from "@/lib/pairing";
import { getSupabaseAdmin } from "@/lib/supabase";
import { getSessionMember } from "@/lib/session-auth";

function validId(value: unknown) {
  return typeof value === "string" && /^[0-9a-f-]{36}$/i.test(value);
}

export async function POST(request: Request) {
  try {
    const { sessionId, cardId, response } = await request.json();
    const validCardId = cleanCardId(cardId);
    if (!validId(sessionId) || !validCardId || !isDraftResponse(response)) {
      return NextResponse.json({ error: "INVALID_INPUT" }, { status: 400 });
    }
    const supabase = getSupabaseAdmin();
    const member = await getSessionMember(request, sessionId);
    if (!member) return NextResponse.json({ error: "SESSION_NOT_AVAILABLE" }, { status: 404 });

    const { data: existing, error: existingError } = await supabase
      .from("session_answers")
      .select("status")
      .eq("session_id", sessionId)
      .eq("member_id", member.id)
      .eq("card_id", validCardId)
      .maybeSingle();
    if (existingError) throw existingError;
    if (existing?.status === "published") return NextResponse.json({ error: "ANSWER_PUBLISHED" }, { status: 409 });

    const status = isResponse(response) ? "ready" : "draft";
    const { error: saveError } = await supabase.from("session_answers").upsert({
      session_id: sessionId,
      member_id: member.id,
      card_id: validCardId,
      response,
      status,
      updated_at: new Date().toISOString()
    }, { onConflict: "session_id,member_id,card_id" });
    if (saveError) throw saveError;
    return NextResponse.json({ status });
  } catch (error) {
    const configured = !(error instanceof Error && error.message === "SUPABASE_NOT_CONFIGURED");
    return NextResponse.json({ error: configured ? "SAVE_FAILED" : "SUPABASE_NOT_CONFIGURED" }, { status: configured ? 500 : 503 });
  }
}
