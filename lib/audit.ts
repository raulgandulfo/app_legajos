import { cookies } from "next/headers";
import { getSupabase } from "./supabase";

export async function auditLog(accion: string, detalle?: string) {
  try {
    const cookieStore = await cookies();
    const raw = cookieStore.get("session")?.value;
    if (!raw) return;
    const session = JSON.parse(raw);
    if (session.rol !== "auxiliar") return;

    const supabase = getSupabase();
    await supabase.from("audit_log").insert({
      username: session.username,
      accion,
      detalle: detalle || null,
    });
  } catch {
    // silencioso — el log no debe romper la operación principal
  }
}
