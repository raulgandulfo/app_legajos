import { NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { readFileSync } from "fs";
import { join } from "path";

export async function POST() {
  const supabase = getSupabase();
  const raw = readFileSync(join(process.cwd(), "asociados.json"), "utf-8");
  const mapa = JSON.parse(raw) as Record<string, string>;
  let ok = 0;
  const errores: string[] = [];

  for (const [cuil, nro] of Object.entries(mapa)) {
    const { error } = await supabase
      .from("maestro_asociados")
      .update({ nro_asociado: nro })
      .eq("cuil", cuil);
    if (error) errores.push(`${cuil}: ${error.message}`);
    else ok++;
  }

  return NextResponse.json({ ok, total: Object.keys(mapa).length, errores });
}
