import { createClient } from "@supabase/supabase-js";

export function getSupabase() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_KEY;
  if (!url || !key) throw new Error("Faltan variables de entorno SUPABASE_URL o SUPABASE_KEY");
  return createClient(url, key);
}
