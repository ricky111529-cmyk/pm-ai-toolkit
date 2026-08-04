import { NextResponse } from "next/server";
import { getAuthenticatedUserId } from "@/lib/auth";
import { cleanName, hashSecret, normalizeShareCode } from "@/lib/pairing";
import { getSupabaseAdmin } from "@/lib/supabase";

export async function POST(request: Request) {
  try {
    const userId = await getAuthenticatedUserId(request); const { name, joinCode } = await request.json(); const displayName = cleanName(name); const code = typeof joinCode === "string" ? normalizeShareCode(joinCode) : "";
    if (!userId || !displayName || !code) return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
    const supabase = getSupabaseAdmin(); const { data: session, error } = await supabase.from("conversation_sessions").select("id, expires_at").eq("join_code_hash", hashSecret(code)).maybeSingle();
    if (error) throw error;
    if (!session || new Date(session.expires_at) < new Date()) return NextResponse.json({ error: "SESSION_NOT_AVAILABLE" }, { status: 404 });
    const { data: existing } = await supabase.from("session_members").select("id").eq("session_id", session.id).eq("user_id", userId).maybeSingle();
    if (existing) return NextResponse.json({ sessionId: session.id, existing: true });
    const { count, error: countError } = await supabase.from("session_members").select("id", { count: "exact", head: true }).eq("session_id", session.id); if (countError) throw countError;
    if ((count ?? 0) >= 2) return NextResponse.json({ error: "SESSION_FULL" }, { status: 409 });
    const { error: memberError } = await supabase.from("session_members").insert({ session_id: session.id, user_id: userId, display_name: displayName, access_token_hash: hashSecret(`${userId}:${session.id}`) }); if (memberError) throw memberError;
    return NextResponse.json({ sessionId: session.id });
  } catch (error) { console.error("Session join failed", error); return NextResponse.json({ error: "JOIN_FAILED" }, { status: 500 }); }
}
