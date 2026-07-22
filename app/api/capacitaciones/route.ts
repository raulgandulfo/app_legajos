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
      .from("capacitaciones")
      .select("*, maestro_asociados!left(nombre_completo, nro_legajo)")
      .order("fecha", { ascending: false });

    if (filtroCuil) query = query.eq("cuil_asociado", filtroCuil);
    if (desde) query = query.gte("fecha", desde);
    if (hasta) query = query.lte("fecha", hasta);

    const { data } = await query;
    return NextResponse.json(data || []);
  }

  if (cuil) {
    const { data } = await supabase
      .from("capacitaciones").select("*").eq("cuil_asociado", cuil).order("fecha", { ascending: false });
    return NextResponse.json(data || []);
  }

  return NextResponse.json([]);
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const body = await req.json();
  await supabase.from("capacitaciones").insert({
    cuil_asociado: body.cuil,
    titulo: body.titulo,
    fecha: body.fecha,
    duracion_hs: body.duracion_hs || null,
    resultado: body.resultado || null,
    observaciones: body.observaciones || null,
  });
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: NextRequest) {
  const supabase = getSupabase();
  const { id } = await req.json();
  await supabase.from("capacitaciones").delete().eq("id", id);
  return NextResponse.json({ ok: true });
}
