import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { auditLog } from "@/lib/audit";

export async function GET(req: NextRequest) {
  const supabase = getSupabase();
  const { searchParams } = new URL(req.url);
  const cuil = searchParams.get("cuil");
  const reporte = searchParams.get("reporte");
  const fechaDesde = searchParams.get("fecha_desde");
  const fechaHasta = searchParams.get("fecha_hasta");

  if (reporte) {
    await auditLog("consulta", "Consultó reporte de anticipos");
    let query = supabase
      .from("anticipos")
      .select("*, maestro_asociados(cuil, nro_asociado, nro_legajo, nombre_completo)")
      .order("fecha_solicitud", { ascending: false });
    if (fechaDesde) query = query.gte("fecha_solicitud", fechaDesde);
    if (fechaHasta) query = query.lte("fecha_solicitud", fechaHasta);
    const { data } = await query;
    return NextResponse.json(data || []);
  }

  if (cuil) {
    const { data } = await supabase
      .from("anticipos")
      .select("*, maestro_asociados(cuil, nro_asociado, nro_legajo, nombre_completo)")
      .eq("cuil_asociado", cuil)
      .order("fecha_solicitud", { ascending: false });
    return NextResponse.json(data || []);
  }

  return NextResponse.json([]);
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const { cuil, monto, fecha_solicitud, observaciones } = await req.json();
  const { error } = await supabase.from("anticipos").insert({
    cuil_asociado: cuil, monto, fecha_solicitud, estado: "Pendiente", observaciones: observaciones || null,
  });
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });
  await auditLog("alta", `Registró anticipo $${monto} para CUIL ${cuil}`);
  return NextResponse.json({ ok: true });
}

export async function PATCH(req: NextRequest) {
  const supabase = getSupabase();
  const { id, monto, fecha_solicitud, estado, observaciones } = await req.json();
  await supabase.from("anticipos").update({ monto, fecha_solicitud, estado, observaciones }).eq("id", id);
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: NextRequest) {
  const supabase = getSupabase();
  const { id } = await req.json();
  await supabase.from("anticipos").delete().eq("id", id);
  await auditLog("baja", `Eliminó anticipo id ${id}`);
  return NextResponse.json({ ok: true });
}
