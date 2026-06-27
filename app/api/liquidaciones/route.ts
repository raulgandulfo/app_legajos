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
    const { data } = await supabase.from("liquidaciones").select("periodo");
    const all = [...new Set((data || []).map((r: { periodo: string }) => r.periodo))].sort().reverse();
    return NextResponse.json(all);
  }

  if (cuil && !periodo) {
    const { data } = await supabase.from("liquidaciones").select("periodo").eq("cuil", cuil);
    const ps = [...new Set((data || []).map((r: { periodo: string }) => r.periodo))].sort().reverse();
    return NextResponse.json(ps);
  }

  if (cuil && periodo) {
    const { data } = await supabase.from("liquidaciones").select("*").eq("cuil", cuil).eq("periodo", periodo);
    return NextResponse.json(data || []);
  }

  if (periodos) {
    const arr = periodos.split(",");
    const { data } = await supabase.from("liquidaciones").select("*").in("periodo", arr);
    return NextResponse.json(data || []);
  }

  return NextResponse.json([]);
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const { filas } = await req.json();
  for (let i = 0; i < filas.length; i += 500) {
    await supabase.from("liquidaciones").insert(filas.slice(i, i + 500));
  }
  return NextResponse.json({ count: filas.length });
}
