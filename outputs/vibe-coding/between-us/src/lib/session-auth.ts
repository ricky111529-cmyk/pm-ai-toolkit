import { getAuthenticatedUserId } from "@/lib/auth";
import { getSupabaseAdmin } from "@/lib/supabase";

export async function getSessionMember(request: Request, sessionId: string) {
  const userId = await getAuthenticatedUserId(request);
  if (!userId) return null;
  const supabase = getSupabaseAdmin();
  const { data, error } = await supabase.from("session_members").select("id, session_id, user_id").eq("session_id", sessionId).eq("user_id", userId).maybeSingle();
  if (error) throw error;
  return data;
}
