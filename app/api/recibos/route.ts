import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { PDFDocument, StandardFonts, rgb } from "pdf-lib";
import JSZip from "jszip";
import { readFileSync, existsSync } from "fs";
import { join } from "path";

function fmt(v: number) {
  return v.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

interface LiqRow {
  cuil: string;
  nombre_completo?: string;
  nro_legajo?: string;
  descripcion?: string;
  tipo_concepto?: string;
  importe?: number;
  sector?: string;
  categoria?: string;
  jornal_basico?: number;
  haberes_rem?: number;
  haberes_no_rem?: number;
  retenciones?: number;
  neto?: number;
  periodo?: string;
}

interface AsoMap {
  [cuil: string]: { nombre_completo?: string; nro_asociado?: string; sector?: string };
}

function safeMax(arr: number[]): number {
  const filtered = arr.filter(n => isFinite(n));
  return filtered.length ? Math.max(...filtered) : 0;
}

// Normaliza sector para agrupación (sin acentos, mayúsculas) — evita duplicados por variaciones
function normSec(s: string): string {
  return (s || "General").normalize("NFD").replace(/[̀-ͯ]/g, "").toUpperCase().trim();
}

// pdf-lib usa WinAnsi: elimina caracteres fuera de rango (0xFFFD, etc.)
function sp(s: string): string {
  return (s || "").replace(/[�Ā-￿]/g, c => {
    const map: Record<string, string> = {
      "’": "'", "‘": "'", "“": '"', "”": '"',
      "–": "-", "—": "-", "•": "*", "°": "o",
    };
    return map[c] ?? "?";
  });
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const { periodos, titulo, fecha } = await req.json();

  const { data: rows } = await supabase
    .from("liquidaciones").select("*").in("periodo", periodos).limit(100000);

  if (!rows?.length) return NextResponse.json({ error: "Sin datos" }, { status: 400 });

  try {

  const cuils = [...new Set(rows.map((r: LiqRow) => r.cuil))];
  const { data: asoData } = await supabase.from("maestro_asociados")
    .select("cuil, nombre_completo, nro_asociado, sector").in("cuil", cuils).limit(10000);
  const asoMap: AsoMap = {};
  (asoData || []).forEach((a: { cuil: string; nombre_completo?: string; nro_asociado?: string; sector?: string }) => { asoMap[a.cuil] = a; });

  // bySector key = sector normalizado; displaySec = nombre para mostrar en PDF
  const bySector: Record<string, {
    cuil: string; nombre: string; cat: string; sec: string; nro: string;
    puntos: number; vPunto: number; total: number; neto: number;
    descuentos: { desc: string; monto: number }[];
  }[]> = {};
  const sectorDisplay: Record<string, string> = {}; // normKey → nombre original para PDF

  // Normalizar CUILs al agrupar (por si algunos quedaron con guiones en la DB)
  const byCuil: Record<string, LiqRow[]> = {};
  for (const r of rows as LiqRow[]) {
    const cuil = String(r.cuil || "").replace(/-/g, "").replace(/\s/g, "").trim();
    if (!cuil) continue;
    if (!byCuil[cuil]) byCuil[cuil] = [];
    byCuil[cuil].push(r);
  }

  for (const [cuil, grupo] of Object.entries(byCuil)) {
    const first = grupo[0];
    const nombre = first.nombre_completo || asoMap[cuil]?.nombre_completo || cuil;
    const cat = first.categoria || grupo.find(r => r.categoria)?.categoria || "";
    const rawSec = first.sector || grupo.find(r => r.sector)?.sector || asoMap[cuil]?.sector || "General";
    const secKey = normSec(rawSec);
    const nro = asoMap[cuil]?.nro_asociado || first.nro_legajo || "S/D";
    // Guardar nombre de display del sector (primer valor encontrado)
    if (!sectorDisplay[secKey]) sectorDisplay[secKey] = rawSec;

    // Python: drop_duplicates(subset='Liquidación') para evitar duplicar haberes
    // Tomamos el max de haberes_rem+haberes_no_rem (repetido en cada fila, pero único por período)
    const totalHaberes = safeMax(grupo.map(r => (r.haberes_rem || 0) + (r.haberes_no_rem || 0)));
    const maxNeto = safeMax(grupo.map(r => r.neto || 0));

    // PUNTOS: fila con descripcion que contenga "PUNTOS" y tipo "Puente"
    const puntosRows = grupo.filter(r => (r.descripcion || "").toUpperCase().includes("PUNTO"));
    const puntos = puntosRows.reduce((s, r) => s + (r.importe || 0), 0);
    // Python: int(total_haberes / puntos)
    const vPunto = puntos > 0 && totalHaberes > 0 ? Math.floor(totalHaberes / puntos) : 0;

    // Retenciones: filas con tipo_concepto = "Retención" tienen el monto en 'retenciones'
    const descRows = grupo.filter(r =>
      (r.tipo_concepto || "").toLowerCase().includes("retenci") ||
      (r.retenciones || 0) > 0
    );
    const totalDesc = descRows.reduce((s, r) => s + (r.retenciones || 0), 0);
    const descuentos = descRows
      .filter(r => (r.retenciones || 0) > 0)
      .map(r => ({ desc: sp(r.descripcion || ""), monto: r.retenciones || 0 }));

    const netoFinal = maxNeto > 0 ? maxNeto : totalHaberes - totalDesc;

    if (!bySector[secKey]) bySector[secKey] = [];
    bySector[secKey].push({ cuil, nombre, cat, sec: rawSec, nro, puntos, vPunto, total: totalHaberes, neto: netoFinal, descuentos });
  }

  // Intentar cargar logo desde public/logo.png
  const logoPath = join(process.cwd(), "public", "logo.png");
  const logoBytes = existsSync(logoPath) ? readFileSync(logoPath) : null;

  const zip = new JSZip();

  for (const [secKey, recibos] of Object.entries(bySector)) {
    const sec = sectorDisplay[secKey] || secKey;
    const pdfDoc = await PDFDocument.create();
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const fontBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
    const logoImg = logoBytes ? await pdfDoc.embedPng(logoBytes).catch(() => null) : null;

    const sorted = [...recibos].sort((a, b) => a.nombre.localeCompare(b.nombre));

    for (let i = 0; i < sorted.length; i += 2) {
      const page = pdfDoc.addPage([595, 842]);
      const { height } = page.getSize();

      for (let j = 0; j < 2 && i + j < sorted.length; j++) {
        const r = sorted[i + j];
        const baseY = j === 0 ? height - 20 : height - 20 - 421;
        let y = baseY;

        const line = (text: string, size = 10, bold = false, indent = 10) => {
          page.drawText(text, { x: indent, y, font: bold ? fontBold : font, size, color: rgb(0.1, 0.1, 0.1) });
          y -= size + 3;
        };

        // Logo: lado derecho, no afecta el flujo de texto (igual que en Python: x=160, w=35 sobre A4 210mm)
        if (logoImg) {
          const logoDims = logoImg.scaleToFit(115, 55);
          page.drawImage(logoImg, {
            x: 585 - logoDims.width,
            y: baseY - logoDims.height,
            width: logoDims.width,
            height: logoDims.height,
          });
        }
        line("COOPERATIVA DE TRABAJO DE SERVICIOS AGROINDUSTRIALES LTDA.", 11, true);
        line("Mano de obra asociados (RT 24) / Retornos (Ley 20.337)", 9);
        y -= 6;
        line(`Asociado/a: ${sp(r.nombre)}`);
        line(`Asociado N: ${sp(r.nro)}`);
        line(`CUIL: ${sp(r.cuil)}`);
        line(`Categoria funcional: ${sp(r.cat)}`);
        line(`Sector: ${sp(r.sec)} | Periodo: ${sp(titulo)}`);
        y -= 4;
        line(`Puntos obtenidos: ${Math.round(r.puntos)} | Valor del punto: $${fmt(r.vPunto)} | Total a cobrar: $${fmt(r.total)}`, 10, true);
        y -= 2;

        if (r.descuentos.length > 0) {
          line("Descuentos:", 9, true);
          for (const d of r.descuentos) {
            line(`  - ${sp(d.desc)}: $${fmt(d.monto)}`, 9, false, 15);
          }
        }
        y -= 4;
        const txt = `Recibi conforme la suma de Pesos $${fmt(r.neto)} en concepto de Mano de obra asociados (RT 24) / Retornos (Ley 20.337).`;
        const words = txt.split(" ");
        let line2 = "";
        for (const w of words) {
          if ((line2 + w).length > 90) { line(line2.trim()); line2 = w + " "; }
          else line2 += w + " ";
        }
        if (line2.trim()) line(line2.trim());

        y = baseY - 390;
        page.drawText("Firma del Asociado/a: ____________________", { x: 10, y, font, size: 10, color: rgb(0.1, 0.1, 0.1) });
        page.drawText(`Fecha de emision: ${sp(fecha)}`, { x: 350, y, font, size: 10, color: rgb(0.1, 0.1, 0.1) });

        if (j === 0) {
          page.drawLine({ start: { x: 10, y: baseY - 405 }, end: { x: 585, y: baseY - 405 }, thickness: 0.5, color: rgb(0.6, 0.6, 0.6) });
        }
      }
    }

    const pdfBytes = await pdfDoc.save();
    zip.file(`Recibos_${sec.replace(/\s+/g, "_")}.pdf`, pdfBytes);
  }

  const zipBytes = await zip.generateAsync({ type: "uint8array" });
  return new NextResponse(zipBytes as unknown as BodyInit, {
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename="Recibos_${titulo.replace(/\s+/g, "_")}.zip"`,
    },
  });
  } catch (e) {
    console.error("Error generando recibos:", e);
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
