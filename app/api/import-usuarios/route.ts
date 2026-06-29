import { NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function POST() {
  const supabase = getSupabase();

  const { data: asociados, error } = await supabase
    .from("maestro_asociados")
    .select("cuil, dni")
    .eq("activo", true);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  let ok = 0;
  let sinDni = 0;
  const errores: string[] = [];

  for (const aso of asociados || []) {
    const dni = String(aso.dni || "").replace(/\D/g, "").trim();
    if (!dni) { sinDni++; continue; }

    const { error: uError } = await supabase.from("usuarios").upsert(
      { username: aso.cuil, password: dni, rol: "asociado", cuil_asociado: aso.cuil },
      { onConflict: "username" }
    );
    if (uError) errores.push(`${aso.cuil}: ${uError.message}`);
    else ok++;
  }

  return NextResponse.json({ ok, sinDni, total: (asociados || []).length, errores });
}
