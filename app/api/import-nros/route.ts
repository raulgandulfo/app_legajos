import { NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { readFileSync } from "fs";
import { join } from "path";

export async function POST() {
  const supabase = getSupabase();
  const raw = readFileSync(join(process.cwd(), "asociados.json"), "utf-8");
  const mapa = JSON.parse(raw) as Record<string, string>;
  let ok = 0;
  let omitidos = 0;
  const errores: string[] = [];

  for (const [cuil, password] of Object.entries(mapa)) {
    const { data: enMaestro } = await supabase
      .from("maestro_asociados").select("cuil").eq("cuil", cuil).single();
    if (!enMaestro) { omitidos++; continue; }

    const { error } = await supabase.from("usuarios").upsert(
      { username: cuil, password, rol: "asociado", cuil_asociado: cuil },
      { onConflict: "username" }
    );
    if (error) errores.push(`${cuil}: ${error.message}`);
    else ok++;
  }

  return NextResponse.json({ ok, omitidos, total: Object.keys(mapa).length, errores });
}
