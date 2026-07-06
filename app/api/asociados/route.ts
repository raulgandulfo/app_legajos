import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(req: NextRequest) {
  const supabase = getSupabase();
  const { searchParams } = new URL(req.url);
  const cuil = searchParams.get("cuil");
  const all = searchParams.get("all");
  const categorias = searchParams.get("categorias");
  const reporte = searchParams.get("reporte");

  if (categorias) {
    const { data } = await supabase.from("maestro_asociados").select("categoria").eq("activo", true);
    const cats = [...new Set((data || []).map((r: { categoria: string }) => r.categoria).filter(Boolean))].sort();
    return NextResponse.json(cats);
  }

  if (reporte) {
    const { data } = await supabase
      .from("maestro_asociados")
      .select("cuil,nro_asociado,nro_legajo,nombre_completo,dni,domicilio,localidad,provincia,telefono,sector,categoria,fecha_ingreso,fecha_salida,activo")
      .order("nombre_completo");
    return NextResponse.json(data || []);
  }

  if (cuil) {
    const { data } = await supabase.from("maestro_asociados").select("*").eq("cuil", cuil).single();
    return NextResponse.json(data);
  }

  if (all) {
    const incluirInactivos = searchParams.get("incluir_inactivos") === "1";
    let q = supabase.from("maestro_asociados").select("*").order("nombre_completo");
    if (!incluirInactivos) q = q.eq("activo", true);
    const { data, error } = await q;
    if (error) return NextResponse.json({ error: error.message }, { status: 500 });
    return NextResponse.json(data || []);
  }

  return NextResponse.json([]);
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const datos = await req.json();
  // Normalizar campos de fecha: string vacío → null
  if (!datos.fecha_salida) datos.fecha_salida = null;
  if (!datos.fecha_ingreso) datos.fecha_ingreso = null;
  datos.activo = !datos.fecha_salida;
  const { error } = await supabase.from("maestro_asociados").upsert(datos, { onConflict: "cuil" });
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: NextRequest) {
  const supabase = getSupabase();
  const { cuil } = await req.json();
  await supabase.from("maestro_asociados").update({ activo: false }).eq("cuil", cuil);
  return NextResponse.json({ ok: true });
}
