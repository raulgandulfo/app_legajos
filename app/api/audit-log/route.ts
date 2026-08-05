import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getSupabase } from "@/lib/supabase";

export async function GET() {
  // Solo admins pueden ver el log
  const cookieStore = await cookies();
  const raw = cookieStore.get("session")?.value;
  if (!raw) return NextResponse.json([], { status: 401 });
  const session = JSON.parse(raw);
  if (session.rol !== "admin") return NextResponse.json([], { status: 403 });

  const supabase = getSupabase();
  const { data } = await supabase
    .from("audit_log")
    .select("id, username, accion, detalle, fecha")
    .order("fecha", { ascending: false })
    .limit(1000);

  return NextResponse.json(data || []);
}
