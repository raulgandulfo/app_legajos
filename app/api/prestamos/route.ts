import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(req: NextRequest) {
  const supabase = getSupabase();
  const { searchParams } = new URL(req.url);
  const cuil = searchParams.get("cuil");
  const reporte = searchParams.get("reporte");
  const fechaDesde = searchParams.get("fecha_desde");
  const fechaHasta = searchParams.get("fecha_hasta");
  const vtoDesde = searchParams.get("vto_desde");
  const vtoHasta = searchParams.get("vto_hasta");

  // Auto-marcar cuotas vencidas como Descontadas
  const hoy = new Date().toISOString().slice(0, 10);
  await supabase
    .from("prestamos_cuotas")
    .update({ estado: "Descontada" })
    .eq("estado", "Pendiente")
    .lt("fecha_vencimiento", hoy);

  if (reporte) {
    let query = supabase
      .from("prestamos")
      .select("*, maestro_asociados(cuil, nro_asociado, nro_legajo, nombre_completo), prestamos_cuotas(*)")
      .order("fecha_otorgamiento", { ascending: false });

    if (fechaDesde) query = query.gte("fecha_otorgamiento", fechaDesde);
    if (fechaHasta) query = query.lte("fecha_otorgamiento", fechaHasta);

    const { data } = await query;
    let result = data || [];

    // Filtro por fecha de vencimiento de cuotas
    if (vtoDesde || vtoHasta) {
      result = result.filter(p =>
        (p.prestamos_cuotas || []).some((c: { fecha_vencimiento: string }) => {
          if (vtoDesde && c.fecha_vencimiento < vtoDesde) return false;
          if (vtoHasta && c.fecha_vencimiento > vtoHasta) return false;
          return true;
        })
      ).map(p => ({
        ...p,
        prestamos_cuotas: (p.prestamos_cuotas || []).filter((c: { fecha_vencimiento: string }) => {
          if (vtoDesde && c.fecha_vencimiento < vtoDesde) return false;
          if (vtoHasta && c.fecha_vencimiento > vtoHasta) return false;
          return true;
        }),
      }));
    }

    return NextResponse.json(result);
  }

  if (cuil) {
    const { data } = await supabase
      .from("prestamos")
      .select("*, maestro_asociados(cuil, nro_asociado, nro_legajo, nombre_completo), prestamos_cuotas(*)")
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
