import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(req: NextRequest) {
  const supabase = getSupabase();
  const { searchParams } = new URL(req.url);
  const cuil = searchParams.get("cuil");
  const reporte = searchParams.get("reporte");
  const periodo = searchParams.get("periodo");

  if (reporte) {
    // Reporte admin: todos los períodos confirmados + quién no confirmó
    const { data } = await supabase
      .from("recibo_confirmaciones")
      .select("*, maestro_asociados!left(nombre_completo, nro_asociado, nro_legajo)")
      .order("fecha_confirmacion", { ascending: false });
    return NextResponse.json(data || []);
  }

  if (cuil && periodo) {
    const { data } = await supabase
      .from("recibo_confirmaciones")
      .select("id, fecha_confirmacion")
      .eq("cuil", cuil)
      .eq("periodo", periodo)
      .maybeSingle();
    return NextResponse.json(data || null);
  }

  if (cuil) {
    // Todos los períodos confirmados por este CUIL
    const { data } = await supabase
      .from("recibo_confirmaciones")
      .select("periodo, fecha_confirmacion")
      .eq("cuil", cuil);
    return NextResponse.json(data || []);
  }

  return NextResponse.json([]);
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const ip =
    req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ||
    req.headers.get("x-real-ip") ||
    "desconocida";

  const { cuil, periodo } = await req.json();
  if (!cuil || !periodo) return NextResponse.json({ error: "Faltan datos" }, { status: 400 });

  const { error } = await supabase.from("recibo_confirmaciones").upsert(
    { cuil, periodo, ip, fecha_confirmacion: new Date().toISOString() },
    { onConflict: "cuil,periodo" }
  );

  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}
