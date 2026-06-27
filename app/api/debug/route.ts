import { NextResponse } from "next/server";

export async function GET() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;

  if (!url || !key) {
    return NextResponse.json({
      ok: false,
      error: "Faltan env vars",
      SUPABASE_URL: url ? "SET" : "MISSING",
      SUPABASE_KEY: key ? "SET" : "MISSING",
    });
  }

  try {
    const { createClient } = await import("@supabase/supabase-js");
    const supabase = createClient(url, key);
    const { data, error } = await supabase.from("usuarios").select("username, rol, password").limit(5);
    const { data: loginTest, error: loginError } = await supabase
      .from("usuarios").select("*").eq("username", "admin").eq("password", "admin123").single();
    return NextResponse.json({
      ok: !error,
      SUPABASE_URL: "SET",
      SUPABASE_KEY: "SET",
      dbError: error?.message || null,
      usuarios: data || [],
      loginTest: loginTest || null,
      loginError: loginError?.message || null,
    });
  } catch (e) {
    return NextResponse.json({ ok: false, error: (e as Error).message });
  }
}
