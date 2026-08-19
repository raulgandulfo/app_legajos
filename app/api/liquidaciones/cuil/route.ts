import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function DELETE(req: NextRequest) {
  const supabase = getSupabase();
  const { cuil, periodo } = await req.json();
  if (!cuil || !periodo) return NextResponse.json({ error: "Faltan parámetros" }, { status: 400 });
  const { error } = await supabase.from("liquidaciones").delete().eq("cuil", cuil).eq("periodo", periodo);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
