import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(req: NextRequest) {
  const supabase = getSupabase();
  const { searchParams } = new URL(req.url);
  const cuil = searchParams.get("cuil");
  const periodo = searchParams.get("periodo");
  const periodos = searchParams.get("periodos");
  const listAll = searchParams.get("list");

  if (listAll) {
    // Paginar para superar el límite de 1000 filas de PostgREST
    const PAGE = 1000;
    let allPeriodos: string[] = [];
    let from = 0;
    while (true) {
      const { data } = await supabase.from("liquidaciones").select("periodo").range(from, from + PAGE - 1);
      if (!data?.length) break;
      allPeriodos.push(...data.map((r: { periodo: string }) => r.periodo));
      if (data.length < PAGE) break;
      from += PAGE;
    }
    const all = [...new Set(allPeriodos)].sort().reverse();
    return NextResponse.json(all);
  }

  if (cuil && !periodo) {
    const { data } = await supabase.from("liquidaciones").select("periodo").eq("cuil", cuil).limit(10000);
    const ps = [...new Set((data || []).map((r: { periodo: string }) => r.periodo))].sort().reverse();
    return NextResponse.json(ps);
  }

  if (cuil && periodo) {
    const { data } = await supabase.from("liquidaciones").select("*").eq("cuil", cuil).eq("periodo", periodo).limit(10000);
    return NextResponse.json(data || []);
  }

  if (periodos) {
    const arr = periodos.split(",");
    const { data } = await supabase.from("liquidaciones").select("*").in("periodo", arr).limit(100000);
    return NextResponse.json(data || []);
  }

  return NextResponse.json([]);
}

export async function DELETE(req: NextRequest) {
  const supabase = getSupabase();
  const { periodo } = await req.json();
  if (!periodo) return NextResponse.json({ error: "Falta periodo" }, { status: 400 });
  const { error } = await supabase.from("liquidaciones").delete().eq("periodo", periodo);
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });
  return NextResponse.json({ ok: true });
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const { filas, reemplazar } = await req.json();

  if (!filas?.length) return NextResponse.json({ count: 0, insertados: 0, errores: [] });

  // Si hay que reemplazar, borrar filas existentes del mismo período
  if (reemplazar) {
    const periodo = filas[0].periodo;
    await supabase.from("liquidaciones").delete().eq("periodo", periodo);
  }

  let insertados = 0;
  const errores: string[] = [];

  for (let i = 0; i < filas.length; i += 500) {
    const batch = filas.slice(i, i + 500);
    const { error } = await supabase.from("liquidaciones").insert(batch);
    if (error) {
      errores.push(`Batch ${Math.floor(i / 500) + 1}: ${error.message}`);
    } else {
      insertados += batch.length;
    }
  }

  return NextResponse.json({ count: filas.length, insertados, errores });
}
