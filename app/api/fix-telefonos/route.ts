import { NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function POST() {
  const supabase = getSupabase();
  const { data, error } = await supabase
    .from("maestro_asociados")
    .select("cuil, telefono")
    .not("telefono", "is", null);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  const registros = (data || []).filter(a => {
    const t = String(a.telefono || "").trim();
    // Solo modifica si tiene teléfono y NO empieza con 381, 0381, +54381, 011, 02...
    return t && !t.startsWith("381") && !t.startsWith("0381") && !t.startsWith("+54381") && t.length >= 6;
  });

  let ok = 0;
  const errores: string[] = [];
  for (const a of registros) {
    const nuevo = "381" + String(a.telefono).trim();
    const { error: e } = await supabase
      .from("maestro_asociados")
      .update({ telefono: nuevo })
      .eq("cuil", a.cuil);
    if (e) errores.push(`${a.cuil}: ${e.message}`);
    else ok++;
  }

  return NextResponse.json({ ok, total: registros.length, errores });
}
