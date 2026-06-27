import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { cookies } from "next/headers";

export async function POST(req: NextRequest) {
  let supabase;
  try {
    supabase = getSupabase();
  } catch (e) {
    return NextResponse.json({ error: "Error de configuración del servidor: " + (e as Error).message }, { status: 500 });
  }
  const { username, password } = await req.json();
  const { data, error } = await supabase
    .from("usuarios")
    .select("*")
    .eq("username", username)
    .eq("password", password)
    .single();

  if (error && error.code !== "PGRST116") {
    return NextResponse.json({ error: "Error de base de datos: " + error.message }, { status: 500 });
  }
  if (!data) return NextResponse.json({ error: "Credenciales incorrectas" }, { status: 401 });

  const cookieStore = await cookies();
  cookieStore.set("session", JSON.stringify({ username: data.username, rol: data.rol, cuil: data.cuil_asociado }), {
    httpOnly: true, path: "/", maxAge: 60 * 60 * 8,
  });
  return NextResponse.json({ username: data.username, rol: data.rol, cuil: data.cuil_asociado });
}

export async function DELETE() {
  const cookieStore = await cookies();
  cookieStore.delete("session");
  return NextResponse.json({ ok: true });
}

export async function GET() {
  const cookieStore = await cookies();
  const raw = cookieStore.get("session")?.value;
  if (!raw) return NextResponse.json(null);
  try { return NextResponse.json(JSON.parse(raw)); }
  catch { return NextResponse.json(null); }
}
