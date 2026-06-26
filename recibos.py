# -*- coding: utf-8 -*-
import io
import os
import zipfile
from collections import defaultdict
import pandas as pd
from fpdf import FPDF


def fmt_moneda(valor):
    try:
        n = float(valor)
    except:
        n = 0.0
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def generar_zip(df, periodo, fecha_emision, db_map=None):
    """
    Genera recibos PDF por sector, los empaqueta en un ZIP en memoria y lo devuelve como bytes.
    No guarda nada en disco.
    db_map: {cuil: nro_asociado} — fallback si no viene nro en el DataFrame.
    """
    db_map = db_map or {}
    df = df.copy()
    df.columns = df.columns.str.strip()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, "logo.png")

    sectores = defaultdict(list)

    for cuil, grupo in df.groupby("CUIL"):
        cuil_str = str(cuil).strip()
        nombre = grupo["Apellido y Nombre"].iloc[0] if "Apellido y Nombre" in grupo.columns else ""
        cat    = grupo["Categoría"].iloc[0] if "Categoría" in grupo.columns else ""
        sec    = grupo["Sector"].iloc[0] if "Sector" in grupo.columns else "General"
        nro_aso = (grupo["Nro. de Legajo"].iloc[0] if "Nro. de Legajo" in grupo.columns else "") \
                  or db_map.get(cuil_str, "S/D")

        # --- Cálculo del total ---
        haberes_rem    = grupo["Haberes remunerativos"].iloc[0]    if "Haberes remunerativos"    in grupo.columns else 0
        haberes_no_rem = grupo["Haberes No remunerativos"].iloc[0] if "Haberes No remunerativos" in grupo.columns else 0

        if "Liquidación" in grupo.columns:
            resumen = grupo.drop_duplicates(subset="Liquidación")
            total_haberes = resumen["Haberes remunerativos"].sum() + resumen["Haberes No remunerativos"].sum() \
                            if "Haberes remunerativos" in resumen.columns else 0
        else:
            total_haberes = float(haberes_rem) + float(haberes_no_rem)

        # Si no hay haberes guardados, usar Jornal/Básico como total base
        if total_haberes == 0 and "Jornal / Básico" in grupo.columns:
            total_haberes = float(grupo["Jornal / Básico"].iloc[0] or 0)

        # --- Puntos ---
        puntos = 0.0
        if "Importe Calc" in grupo.columns and "Descripción Concepto" in grupo.columns:
            mask = grupo["Descripción Concepto"].fillna("").str.contains("PUNTOS", case=False)
            puntos = float(grupo.loc[mask, "Importe Calc"].sum())

        v_punto = round(total_haberes / puntos, 2) if puntos > 0 else 0

        # --- Descuentos ---
        total_desc = 0.0
        desc_det = pd.DataFrame()
        if "Retenciones" in grupo.columns:
            total_desc = float(grupo["Retenciones"].sum())
            desc_det = grupo[grupo["Retenciones"] > 0][["Descripción Concepto", "Retenciones"]].copy()

        neto_final = total_haberes - total_desc

        sectores[sec].append({
            "cuil": cuil_str, "nombre": nombre, "cat": cat, "sec": sec,
            "nro_aso": nro_aso, "puntos": puntos, "v_punto": v_punto,
            "total": total_haberes, "neto": neto_final, "desc_det": desc_det,
        })

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for sec, recibos in sectores.items():
            pdf = FPDF()
            pdf.set_auto_page_break(auto=False)

            for i, r in enumerate(sorted(recibos, key=lambda x: x["nombre"])):
                if i % 2 == 0:
                    pdf.add_page()
                    y = 10
                else:
                    y = 150

                if os.path.exists(logo_path):
                    try:
                        pdf.image(logo_path, x=160, y=y, w=35)
                    except:
                        pass

                pdf.set_xy(10, y + 2)
                pdf.set_font("Arial", "B", 11)
                pdf.cell(145, 6, "COOPERATIVA DE TRABAJO DE SERVICIOS AGROINDUSTRIALES LTDA.", ln=1)
                pdf.set_font("Arial", "I", 9)
                pdf.cell(145, 5, "Mano de obra asociados (RT 24) / Retornos (Ley 20.337)", ln=1)
                pdf.ln(4)

                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 5, f"Asociado/a: {r['nombre']}", ln=1)
                pdf.cell(0, 5, f"Asociado n\xba: {r['nro_aso']}", ln=1)
                pdf.cell(0, 5, f"CUIL: {r['cuil']}", ln=1)
                pdf.cell(0, 5, f"Categor\xeda funcional: {r['cat']}", ln=1)
                pdf.cell(0, 5, f"Sector: {r['sec']} | Per\xedodo: {periodo}", ln=1)
                pdf.ln(3)

                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 7,
                    f"Puntos obtenidos: {r['puntos']:.2f} | Valor del punto: $ {fmt_moneda(r['v_punto'])} | Total a cobrar: $ {fmt_moneda(r['total'])}",
                    ln=1)

                if not r["desc_det"].empty:
                    pdf.set_font("Arial", "B", 9)
                    pdf.cell(0, 5, "Descuentos aplicados:", ln=1)
                    pdf.set_font("Arial", "", 9)
                    for _, row in r["desc_det"].iterrows():
                        pdf.set_x(15)
                        pdf.cell(0, 5, f"- {row['Descripci\xf3n Concepto']}: $ {fmt_moneda(row['Retenciones'])}", ln=1)

                pdf.ln(3)
                pdf.set_font("Arial", "", 10)
                pdf.multi_cell(0, 5,
                    f"Recib\xed conforme la suma de Pesos $ {fmt_moneda(r['neto'])} "
                    "en concepto de Mano de obra asociados (RT 24) / Retornos (Ley 20.337).",
                    align="L")

                pdf.set_y(y + 128)
                pdf.cell(0, 6, "Firma del Asociado/a: ____________________", ln=0)
                pdf.set_x(130)
                pdf.cell(0, 6, f"Fecha de emisi\xf3n: {fecha_emision}", ln=1)

            nombre_archivo = f"Recibos_{sec.replace(' ', '_')}.pdf"
            raw = pdf.output()
            if isinstance(raw, (bytes, bytearray)):
                pdf_bytes = bytes(raw)
            else:
                pdf_bytes = raw.encode("latin-1")
            zf.writestr(nombre_archivo, pdf_bytes)

    zip_buffer.seek(0)
    return zip_buffer.read()
