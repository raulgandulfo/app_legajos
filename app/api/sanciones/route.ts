import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(req: NextRequest) {
  const supabase = getSupabase();
  const { searchParams } = new URL(req.url);
  const cuil = searchParams.get("cuil");
  const reporte = searchParams.get("reporte");

  if (reporte) {
    const desde = searchParams.get("desde");
    const hasta = searchParams.get("hasta");
    const filtroCuil = searchParams.get("cuil_filtro");

    let query = supabase
      .from("sanciones")
      .select("*, maestro_asociados!left(nombre_completo, nro_legajo)")
      .order("fecha_desde", { ascending: false });

    if (filtroCuil) query = query.eq("cuil_asociado", filtroCuil);
    if (desde) query = query.gte("fecha_desde", desde);
    if (hasta) query = query.lte("fecha_desde", hasta);

    const { data } = await query;
    return NextResponse.json(data || []);
  }

  if (cuil) {
    const { data } = await supabase
      .from("sanciones").select("*").eq("cuil_asociado", cuil).order("fecha_desde", { ascending: false });
    return NextResponse.json(data || []);
  }

  return NextResponse.json([]);
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const body = await req.json();
  const fecha_desde = body.tipo === "Suspensión" ? body.fecha_desde : body.fecha_sancion;
  const fecha_hasta = body.tipo === "Suspensión" ? body.fecha_hasta : body.fecha_sancion;
  await supabase.from("sanciones").insert({
    cuil_asociado: body.cuil, tipo: body.tipo,
    fecha_desde, fecha_hasta, motivo: body.motivo,
  });
  return NextResponse.json({ ok: true });
}
