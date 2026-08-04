import { NextResponse } from "next/server";
import { cleanCardId } from "@/lib/pairing";
import { getSupabaseAdmin } from "@/lib/supabase";
import { getSessionMember } from "@/lib/session-auth";

function validId(value: unknown) {
  return typeof value === "string" && /^[0-9a-f-]{36}$/i.test(value);
}

export async function POST(request: Request) {
  try {
    const { sessionId, cardId } = await request.json();
    const validCardId = cleanCardId(cardId);
    if (!validId(sessionId) || !validCardId) return NextResponse.json({ error: "INVALID_INPUT" }, { status: 400 });
    const supabase = getSupabaseAdmin();
    const member = await getSessionMember(request, sessionId);
    if (!member) return NextResponse.json({ error: "SESSION_NOT_AVAILABLE" }, { status: 404 });

    const { data: answer, error: answerError } = await supabase
      .from("session_answers")
      .select("id, status")
      .eq("session_id", sessionId)
      .eq("member_id", member.id)
      .eq("card_id", validCardId)
      .maybeSingle();
    if (answerError) throw answerError;
    if (!answer || answer.status !== "ready") return NextResponse.json({ error: "ANSWER_NOT_READY" }, { status: 409 });

    const { error: publishError } = await supabase
      .from("session_answers")
      .update({ status: "published", published_at: new Date().toISOString(), updated_at: new Date().toISOString() })
      .eq("id", answer.id)
      .eq("status", "ready");
    if (publishError) throw publishError;
    return NextResponse.json({ status: "published" });
  } catch (error) {
    const configured = !(error instanceof Error && error.message === "SUPABASE_NOT_CONFIGURED");
    return NextResponse.json({ error: configured ? "PUBLISH_FAILED" : "SUPABASE_NOT_CONFIGURED" }, { status: configured ? 500 : 503 });
  }
}
