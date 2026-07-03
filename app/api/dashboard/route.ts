import { NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET() {
  const supabase = getSupabase();
  const hoy = new Date().toISOString().slice(0, 10);
  const hace30 = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10);

  const [
    { count: totalActivos },
    { count: cuotasPendientes },
    { count: cuotasVencidas },
    { count: sancionesVigentes },
    { count: inasistencias30 },
  ] = await Promise.all([
    supabase.from("maestro_asociados").select("*", { count: "exact", head: true }).eq("activo", true),
    supabase.from("prestamos_cuotas").select("*", { count: "exact", head: true }).eq("estado", "Pendiente"),
    supabase.from("prestamos_cuotas").select("*", { count: "exact", head: true })
      .eq("estado", "Pendiente").lt("fecha_vencimiento", hoy),
    supabase.from("sanciones").select("*", { count: "exact", head: true }).gte("fecha_hasta", hace30),
    supabase.from("historial_medico").select("*", { count: "exact", head: true }).gte("fecha_desde", hace30),
  ]);

  return NextResponse.json({
    totalActivos: totalActivos ?? 0,
    cuotasPendientes: cuotasPendientes ?? 0,
    cuotasVencidas: cuotasVencidas ?? 0,
    sancionesVigentes: sancionesVigentes ?? 0,
    inasistencias30: inasistencias30 ?? 0,
  });
}
