import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(req: NextRequest) {
  const supabase = getSupabase();
  const { searchParams } = new URL(req.url);
  const cuil = searchParams.get("cuil");
  const reporte = searchParams.get("reporte");

  if (reporte) {
    const { data } = await supabase
      .from("prestamos")
      .select("*, maestro_asociados(cuil, nombre_completo), prestamos_cuotas(*)")
      .order("fecha_otorgamiento", { ascending: false });
    return NextResponse.json(data || []);
  }

  if (cuil) {
    const { data } = await supabase
      .from("prestamos")
      .select("*, prestamos_cuotas(*)")
      .eq("cuil_asociado", cuil)
      .order("fecha_otorgamiento", { ascending: false });
    return NextResponse.json(data || []);
  }

  return NextResponse.json([]);
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const { cuil, monto_total, cantidad_cuotas, fecha_otorgamiento, fechas_vencimientos } = await req.json();

  const { data: p } = await supabase.from("prestamos").insert({
    cuil_asociado: cuil, monto_total, cantidad_cuotas, fecha_otorgamiento,
  }).select().single();

  if (!p) return NextResponse.json({ error: "Error al crear préstamo" }, { status: 400 });

  const monto_cuota = Math.round((monto_total / cantidad_cuotas) * 100) / 100;
  const cuotas = fechas_vencimientos.map((f: string, i: number) => ({
    prestamo_id: p.id,
    numero_cuota: i + 1,
    monto_cuota,
    fecha_vencimiento: f,
    estado: "Pendiente",
  }));
  await supabase.from("prestamos_cuotas").insert(cuotas);
  return NextResponse.json({ ok: true, id: p.id });
}

export async function PATCH(req: NextRequest) {
  const supabase = getSupabase();
  const { id, fecha_vencimiento, estado } = await req.json();
  await supabase.from("prestamos_cuotas").update({ fecha_vencimiento, estado }).eq("id", id);
  return NextResponse.json({ ok: true });
}
