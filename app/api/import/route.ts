import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import * as XLSX from "xlsx";

const REPL = '�'; // U+FFFD: carácter de reemplazo que produce SheetJS para bytes no decodificables

// Normaliza sin quitar el carácter de reemplazo (se trata en keyMatchesAlias)
function normBase(s: string): string {
  return String(s || "")
    .normalize("NFD").replace(/[̀-ͯ]/g, "")
    .toLowerCase().trim();
}

// Compara clave de columna (puede tener � donde había vocales acentuadas)
// con alias. � en la clave actúa como wildcard de una letra.
function keyMatchesAlias(key: string, alias: string): boolean {
  const normKey = normBase(key);
  const normAlias = normBase(alias);
  if (normKey === normAlias) return true;
  if (!normKey.includes(REPL)) return false;
  const escaped = normKey.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const pattern = escaped.split(REPL).join('[a-z]');
  try { return new RegExp(`^${pattern}$`).test(normAlias); } catch { return false; }
}

function sanitize(s: string): string {
  return s.replace(/�/g, "?");
}

function getCell(row: Record<string, unknown>, aliases: string[]): string {
  for (const [key, v] of Object.entries(row)) {
    const matched = aliases.some(alias => keyMatchesAlias(key, alias));
    if (matched && v !== null && v !== undefined && String(v).trim() !== "" && String(v) !== "nan") {
      return sanitize(String(v).trim());
    }
  }
  return "";
}

function deduplicateCols(headers: string[]): string[] {
  const n = headers.length;
  const seen: Record<string, number> = {};
  const result: string[] = new Array(n);
  for (let i = n - 1; i >= 0; i--) {
    const c = (headers[i] || "").trim();
    if (seen[c] !== undefined) {
      result[i] = `${c}_dup${seen[c]}`;
      seen[c]++;
    } else {
      result[i] = c;
      seen[c] = 1;
    }
  }
  return result;
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const formData = await req.formData();
  const file = formData.get("file") as File;
  const sobreescribir = formData.get("sobreescribir") === "true";

  if (!file) return NextResponse.json({ error: "No se recibió archivo" }, { status: 400 });

  const bytes = await file.arrayBuffer();
  const workbook = XLSX.read(bytes, { type: "array", raw: true, codepage: 1252 });
  const sheet = workbook.Sheets[workbook.SheetNames[0]];
  const raw: Record<string, unknown>[] = XLSX.utils.sheet_to_json(sheet, { defval: null, raw: false });

  if (!raw.length) return NextResponse.json({ ok: 0, errores: [] });

  const rawHeaders = Object.keys(raw[0]);
  const cleanHeaders = deduplicateCols(rawHeaders);
  const remapped: Record<string, unknown>[] = raw.map((row) => {
    const newRow: Record<string, unknown> = {};
    rawHeaders.forEach((h, i) => { newRow[cleanHeaders[i]] = row[h]; });
    return newRow;
  });

  const ALIAS: Record<string, string[]> = {
    cuil:           ["CUIL", "cuil", "C.U.I.L.", "CUIT"],
    nro_asociado:   ["Nro. Asociado", "Numero Asociado", "Nro Asociado", "nro_asociado"],
    nro_legajo:     ["Número", "Numero", "Legajo", "Nro. de Legajo", "Nro.Legajo", "Numero de Legajo", "Nro", "NRO", "Número de Legajo", "Nro Legajo"],
    nombre_completo:["Apellido y Nombre", "Nombre y Apellido", "Nombre Completo", "Nombre", "nombre_completo", "Apellido"],
    dni:            ["Nro. de Documento", "Número de Documento", "Nro. Documento", "DNI", "dni", "Documento", "Nro Documento"],
    domicilio:      ["Calle", "Domicilio", "domicilio", "Dirección", "Direccion", "Domicilio Particular"],
    localidad:      ["Localidad", "localidad", "Ciudad"],
    provincia:      ["Provincia", "provincia"],
    telefono:       ["Teléfono móvil", "Telefono movil", "Teléfono Movil", "Telefono Movil", "Teléfono movil", "Tel. Movil", "Tel.Movil", "Teléfono Celular", "Celular", "Movil", "Móvil", "Teléfono fijo", "Telefono fijo", "Teléfono", "Telefono", "telefono", "Tel."],
    sector:         ["Sector", "sector", "Sección", "Seccion", "Area", "Área"],
    categoria:      ["Categoría funcional", "Categoria funcional", "Categoría", "Categoria", "categoria", "Categ.", "Cat."],
    fecha_ingreso:  ["Fecha de alta", "Fecha Alta", "Fecha Ingreso", "Fecha de Ingreso", "fecha_ingreso"],
    fecha_salida:   ["Fecha de baja", "Fecha Baja", "Fecha Salida", "fecha_salida", "Baja"],
    cod_area:       ["Cód. de Área", "Cod. de Area", "Código de área", "Código de Área", "Codigo de area", "Cod. Area", "Cód. Área", "Cod.Area", "CodArea"],
  };

  let ok = 0;
  const errores: string[] = [];

  for (const row of remapped) {
    try {
      const cuil = getCell(row, ALIAS.cuil).replace(/-/g, "").replace(/\s/g, "");
      const nombre = getCell(row, ALIAS.nombre_completo);
      if (!cuil || !nombre) continue;

      // Onvio: primero prueba móvil directo, luego construye con área+fijo
      let tel = getCell(row, ALIAS.telefono);
      if (!tel) {
        const area = getCell(row, ALIAS.cod_area);
        const fijo = getCell(row, ["Teléfono fijo", "Telefono fijo", "telefono"]);
        const movil = getCell(row, ["Teléfono móvil", "Telefono movil", "Movil"]);
        if (movil) tel = movil;
        else if (area && fijo) tel = `0${area}${fijo}`;
        else tel = fijo;
      }

      const fecha_salida = getCell(row, ALIAS.fecha_salida) || null;
      const datos = {
        cuil,
        nro_asociado: getCell(row, ALIAS.nro_asociado) || null,
        nro_legajo: getCell(row, ALIAS.nro_legajo) || null,
        nombre_completo: nombre,
        dni: getCell(row, ALIAS.dni) || null,
        domicilio: getCell(row, ALIAS.domicilio) || null,
        localidad: getCell(row, ALIAS.localidad) || null,
        provincia: getCell(row, ALIAS.provincia) || null,
        telefono: tel || null,
        sector: getCell(row, ALIAS.sector) || null,
        categoria: getCell(row, ALIAS.categoria) || null,
        fecha_ingreso: getCell(row, ALIAS.fecha_ingreso) || null,
        fecha_salida,
        activo: !fecha_salida,
      };

      if (sobreescribir) {
        await supabase.from("maestro_asociados").upsert(datos, { onConflict: "cuil" });
      } else {
        const { data: existe } = await supabase.from("maestro_asociados").select("cuil").eq("cuil", cuil).single();
        if (!existe) await supabase.from("maestro_asociados").insert(datos);
      }
      ok++;
    } catch (e) {
      errores.push(String(e));
    }
  }

  const columnas = Object.keys(raw[0] || {});
  return NextResponse.json({ ok, errores, columnas });
}
