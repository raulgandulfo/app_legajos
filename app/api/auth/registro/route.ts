import { NextRequest, NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  const { cuil, password } = await req.json();

  const { data: enMaestro } = await supabase
    .from("maestro_asociados")
    .select("cuil")
    .eq("cuil", cuil)
    .eq("activo", true)
    .single();

  if (!enMaestro) return NextResponse.json({ error: "El CUIL no figura en los registros de la empresa." }, { status: 400 });

  const { data: yaExiste } = await supabase
    .from("usuarios")
    .select("id")
    .eq("cuil_asociado", cuil)
    .single();

  if (yaExiste) return NextResponse.json({ error: "Este CUIL ya tiene usuario. Si olvidó la clave, contacte a RRHH." }, { status: 400 });

  await supabase.from("usuarios").insert({ username: cuil, password, rol: "asociado", cuil_asociado: cuil });
  return NextResponse.json({ ok: true });
}
