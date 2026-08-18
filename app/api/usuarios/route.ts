import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import bcrypt from "bcryptjs";

export async function GET() {
  const supabase = getSupabase();
  const { data } = await supabase
    .from("usuarios").select("id,username,rol").neq("rol", "asociado").order("rol");
  return NextResponse.json(data || []);
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const { username, password, rol } = await req.json();
  const password_hash = await bcrypt.hash(password, 12);
  const { error } = await supabase.from("usuarios").insert({ username, password, password_hash, rol });
  if (error) return NextResponse.json({ error: "Ya existe un usuario con ese nombre." }, { status: 400 });
  return NextResponse.json({ ok: true });
}

export async function PATCH(req: NextRequest) {
  const supabase = getSupabase();
  const { username, password } = await req.json();
  const password_hash = await bcrypt.hash(password, 12);
  const { data } = await supabase.from("usuarios").update({ password, password_hash }).eq("username", username).select();
  if (!data?.length) return NextResponse.json({ error: "No se encontró ese usuario." }, { status: 404 });
  return NextResponse.json({ ok: true });
}
