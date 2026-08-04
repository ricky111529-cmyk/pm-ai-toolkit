import { getSupabaseAdmin } from "@/lib/supabase";

export async function getAuthenticatedUserId(request: Request) {
  const token = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
  if (!token) return null;
  const { data, error } = await getSupabaseAdmin().auth.getUser(token);
  return error || !data.user ? null : data.user.id;
}
