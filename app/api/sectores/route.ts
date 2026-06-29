import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET() {
  const supabase = getSupabase();
  const { data } = await supabase.from("sectores").select("*").order("nombre");
  return NextResponse.json(data || []);
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const { nombre } = await req.json();
  // Ignorar si ya existe (upsert por nombre, o insert silencioso)
  const { data: existe } = await supabase.from("sectores").select("id").eq("nombre", nombre.trim()).single();
  if (existe) return NextResponse.json({ ok: true });
  const { error } = await supabase.from("sectores").insert({ nombre: nombre.trim() });
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: NextRequest) {
  const supabase = getSupabase();
  const { id } = await req.json();
  await supabase.from("sectores").delete().eq("id", id);
  return NextResponse.json({ ok: true });
}
