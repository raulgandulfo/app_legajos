import { NextRequest, NextResponse } from "next/server";
import { supabase } from "@/lib/supabase";

export async function GET(req: NextRequest) {
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
      .select("cuil,nro_asociado,nombre_completo,dni,domicilio,localidad,provincia,telefono,sector,categoria,fecha_ingreso")
      .eq("activo", true)
      .order("nombre_completo");
    return NextResponse.json(data || []);
  }

  if (cuil) {
    const { data } = await supabase.from("maestro_asociados").select("*").eq("cuil", cuil).single();
    return NextResponse.json(data);
  }

  if (all) {
    const { data } = await supabase
      .from("maestro_asociados")
      .select("cuil,nro_asociado,nombre_completo,sector,categoria")
      .eq("activo", true)
      .order("nombre_completo");
    return NextResponse.json(data || []);
  }

  return NextResponse.json([]);
}

export async function POST(req: NextRequest) {
  const datos = await req.json();
  const { error } = await supabase.from("maestro_asociados").upsert(datos, { onConflict: "cuil" });
  if (error) return NextResponse.json({ error: error.message }, { status: 400 });
  return NextResponse.json({ ok: true });
}

export async function DELETE(req: NextRequest) {
  const { cuil } = await req.json();
  await supabase.from("maestro_asociados").update({ activo: false }).eq("cuil", cuil);
  return NextResponse.json({ ok: true });
}
