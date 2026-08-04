import { NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabase";
import { getSessionMember } from "@/lib/session-auth";

function validId(value: unknown) {
  return typeof value === "string" && /^[0-9a-f-]{36}$/i.test(value);
}

export async function POST(request: Request) {
  try {
    const { sessionId } = await request.json();
    if (!validId(sessionId)) return NextResponse.json({ error: "INVALID_INPUT" }, { status: 400 });
    const supabase = getSupabaseAdmin();
    const authenticatedMember = await getSessionMember(request, sessionId);
    if (!authenticatedMember) return NextResponse.json({ error: "SESSION_NOT_AVAILABLE" }, { status: 404 });

    const [{ data: session, error: sessionError }, { data: members, error: membersError }, { data: answers, error: answersError }] = await Promise.all([
      supabase.from("conversation_sessions").select("id, expires_at").eq("id", sessionId).maybeSingle(),
      supabase.from("session_members").select("id, display_name").eq("session_id", sessionId).order("joined_at"),
      supabase.from("session_answers").select("card_id, member_id, response, status, published_at, updated_at").eq("session_id", sessionId)
    ]);
    if (sessionError || membersError || answersError) throw sessionError ?? membersError ?? answersError;
    if (!session || new Date(session.expires_at) < new Date()) return NextResponse.json({ error: "SESSION_NOT_AVAILABLE" }, { status: 404 });

    const visibleAnswers = (answers ?? []).map((answer) => ({
      cardId: answer.card_id,
      memberId: answer.member_id,
      status: answer.status,
      updatedAt: answer.updated_at,
      response: answer.member_id === authenticatedMember.id || answer.status === "published" ? answer.response : undefined
    }));
    return NextResponse.json({ session: { id: session.id, expiresAt: session.expires_at }, currentMemberId: authenticatedMember.id, members, answers: visibleAnswers });
  } catch (error) {
    const configured = !(error instanceof Error && error.message === "SUPABASE_NOT_CONFIGURED");
    return NextResponse.json({ error: configured ? "STATE_FAILED" : "SUPABASE_NOT_CONFIGURED" }, { status: configured ? 500 : 503 });
  }
}
