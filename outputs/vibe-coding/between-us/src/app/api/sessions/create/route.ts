import { NextResponse } from "next/server";
import { getAuthenticatedUserId } from "@/lib/auth";
import { cleanName, hashSecret, makeSessionCode } from "@/lib/pairing";
import { getSupabaseAdmin } from "@/lib/supabase";

export async function POST(request: Request) {
  try {
    const userId = await getAuthenticatedUserId(request);
    const { name } = await request.json(); const displayName = cleanName(name);
    if (!userId || !displayName) return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
    const supabase = getSupabaseAdmin(); const joinCode = makeSessionCode(); const expiresAt = new Date(Date.now() + 21 * 86400000).toISOString();
    const { data: session, error } = await supabase.from("conversation_sessions").insert({ join_code_hash: hashSecret(joinCode), expires_at: expiresAt }).select("id").single();
    if (error || !session) throw error;
    const { error: memberError } = await supabase.from("session_members").insert({ session_id: session.id, user_id: userId, display_name: displayName, access_token_hash: hashSecret(`${userId}:${session.id}`) });
    if (memberError) throw memberError;
    return NextResponse.json({ sessionId: session.id, joinCode });
  } catch (error) { console.error("Session creation failed", error); return NextResponse.json({ error: "CREATE_FAILED" }, { status: 500 }); }
}
