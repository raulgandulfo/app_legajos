import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const { cuil, dni, password } = await req.json();

  if (!cuil || !dni || !password) {
    return NextResponse.json({ error: "Datos incompletos." }, { status: 400 });
  }

  // Verificar que el CUIL + DNI coincidan en el maestro
  const { data: aso } = await supabase
    .from("maestro_asociados")
    .select("cuil, dni")
    .eq("cuil", cuil)
    .eq("activo", true)
    .single();

  if (!aso) {
    return NextResponse.json({ error: "CUIL no encontrado." }, { status: 400 });
  }

  const dniLimpio = String(aso.dni || "").replace(/\D/g, "");
  const dniIngresado = String(dni).replace(/\D/g, "");

  if (!dniLimpio || dniLimpio !== dniIngresado) {
    return NextResponse.json({ error: "El DNI no coincide con el registrado." }, { status: 400 });
  }

  // Verificar que tiene usuario registrado
  const { data: usuario } = await supabase
    .from("usuarios").select("id").eq("username", cuil).single();

  if (!usuario) {
    return NextResponse.json({ error: "No tenés cuenta creada. Usá la opción Registrarme." }, { status: 400 });
  }

  const { error } = await supabase
    .from("usuarios").update({ password }).eq("username", cuil);

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({ ok: true });
}
