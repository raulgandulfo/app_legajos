import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";
import { PDFDocument, StandardFonts, rgb } from "pdf-lib";
import JSZip from "jszip";

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
}

interface AsoMap {
  [cuil: string]: { nombre_completo?: string; nro_asociado?: string };
}

function safeMax(arr: number[]): number {
  const filtered = arr.filter(n => isFinite(n));
  return filtered.length ? Math.max(...filtered) : 0;
}

export async function POST(req: NextRequest) {
  const supabase = getSupabase();
  const { periodos, titulo, fecha } = await req.json();

  const { data: rows } = await supabase
    .from("liquidaciones").select("*").in("periodo", periodos);

  if (!rows?.length) return NextResponse.json({ error: "Sin datos" }, { status: 400 });

  try {

  const cuils = [...new Set(rows.map((r: LiqRow) => r.cuil))];
  const { data: asoData } = await supabase.from("maestro_asociados")
    .select("cuil, nombre_completo, nro_asociado").in("cuil", cuils);
  const asoMap: AsoMap = {};
  (asoData || []).forEach((a: { cuil: string; nombre_completo?: string; nro_asociado?: string }) => { asoMap[a.cuil] = a; });

  const bySector: Record<string, {
    cuil: string; nombre: string; cat: string; sec: string; nro: string;
    puntos: number; vPunto: number; total: number; neto: number;
    descuentos: { desc: string; monto: number }[];
  }[]> = {};

  const byCuil: Record<string, LiqRow[]> = {};
  for (const r of rows as LiqRow[]) {
    if (!byCuil[r.cuil]) byCuil[r.cuil] = [];
    byCuil[r.cuil].push(r);
  }

  for (const [cuil, grupo] of Object.entries(byCuil)) {
    const first = grupo[0];
    const nombre = first.nombre_completo || asoMap[cuil]?.nombre_completo || cuil;
    const cat = first.categoria || grupo.find(r => r.categoria)?.categoria || "";
    const sec = first.sector || grupo.find(r => r.sector)?.sector || "General";
    const nro = first.nro_legajo || asoMap[cuil]?.nro_asociado || "S/D";

    // buscar el mayor valor de haberes entre todas las filas del empleado
    const maxHabRem = safeMax(grupo.map(r => (r.haberes_rem || 0) + (r.haberes_no_rem || 0)));
    const maxJornal = safeMax(grupo.map(r => r.jornal_basico || 0));
    const maxNeto = safeMax(grupo.map(r => r.neto || 0));
    const totalHaberes = maxHabRem > 0 ? maxHabRem : maxJornal > 0 ? maxJornal : maxNeto;

    const puntosRows = grupo.filter(r => (r.descripcion || "").toUpperCase().includes("PUNTO"));
    const puntos = puntosRows.reduce((s, r) => s + (r.importe || 0), 0);
    const vPunto = puntos > 0 && totalHaberes > 0 ? Math.round((totalHaberes / puntos) * 100) / 100 : 0;

    // retenciones: buscar filas con tipo_concepto de retención o importe negativo
    const descRows = grupo.filter(r =>
      (r.retenciones || 0) > 0 ||
      String(r.descripcion || "").toUpperCase().includes("DESCUENTO") ||
      String(r.descripcion || "").toUpperCase().includes("RETENCIÓN") ||
      String(r.descripcion || "").toUpperCase().includes("RETENCION")
    );
    const maxRet = safeMax(grupo.map(r => r.retenciones || 0));
    const totalDesc = maxRet > 0 ? maxRet : descRows.reduce((s, r) => s + (r.retenciones || 0), 0);
    const descuentos = descRows.filter(r => (r.retenciones || 0) > 0).map(r => ({ desc: r.descripcion || "", monto: r.retenciones || 0 }));

    const netoFinal = maxNeto > 0 ? maxNeto : totalHaberes - totalDesc;

    if (!bySector[sec]) bySector[sec] = [];
    bySector[sec].push({ cuil, nombre, cat, sec, nro, puntos, vPunto, total: totalHaberes, neto: netoFinal, descuentos });
  }

  const zip = new JSZip();

  for (const [sec, recibos] of Object.entries(bySector)) {
    const pdfDoc = await PDFDocument.create();
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const fontBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);

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

        line("COOPERATIVA DE TRABAJO DE SERVICIOS AGROINDUSTRIALES LTDA.", 11, true);
        line("Mano de obra asociados (RT 24) / Retornos (Ley 20.337)", 9);
        y -= 6;
        line(`Asociado/a: ${r.nombre}`);
        line(`Asociado N: ${r.nro}`);
        line(`CUIL: ${r.cuil}`);
        line(`Categoria funcional: ${r.cat}`);
        line(`Sector: ${r.sec} | Periodo: ${titulo}`);
        y -= 4;
        line(`Puntos: ${r.puntos.toFixed(2)} | Valor punto: $${fmt(r.vPunto)} | Total: $${fmt(r.total)}`, 10, true);
        y -= 2;

        if (r.descuentos.length > 0) {
          line("Descuentos:", 9, true);
          for (const d of r.descuentos) {
            line(`  - ${d.desc}: $${fmt(d.monto)}`, 9, false, 15);
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
        page.drawText(`Fecha de emision: ${fecha}`, { x: 350, y, font, size: 10, color: rgb(0.1, 0.1, 0.1) });

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
