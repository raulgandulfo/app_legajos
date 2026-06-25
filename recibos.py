import json
from fpdf import FPDF
import os
from collections import defaultdict
import pandas as pd

def fmt_moneda(valor):
    try:
        n = float(valor)
    except:
        n = 0.0
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def generar_pdf(df, datos_asociados, periodo, fecha_emision, db_map=None):
    # db_map: {cuil: nro_asociado} desde la DB. Si no viene, usa JSON legacy.
    if db_map is not None:
        db_asociados = db_map
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "asociados.json")
        try:
            with open(json_path, 'r') as f:
                db_asociados = json.load(f)
        except:
            db_asociados = {}

    df.columns = df.columns.str.strip()
    sectores = defaultdict(list)

    for cuil, grupo in df.groupby(['CUIL']):
        nombre = grupo['Apellido y Nombre'].iloc[0] if 'Apellido y Nombre' in grupo.columns else ""
        cat = grupo['Categoría'].iloc[0] if 'Categoría' in grupo.columns else ""
        sec = grupo['Sector'].iloc[0] if 'Sector' in grupo.columns else "General"

        cuil_val = cuil[0] if isinstance(cuil, (list, tuple)) else cuil
        cuil_limpio = str(cuil_val).replace('(', '').replace(')', '').replace(',', '').strip()
        nro_aso = db_asociados.get(cuil_limpio, "S/D")

        total_haberes = 0
        if 'Liquidación' in grupo.columns:
            resumen = grupo.drop_duplicates(subset='Liquidación')
            total_haberes = resumen['Haberes remunerativos'].sum() + resumen['Haberes No remunerativos'].sum()
        else:
            total_haberes = grupo['Haberes remunerativos'].iloc[0] + grupo['Haberes No remunerativos'].iloc[0]

        puntos = 0
        if 'Importe Calc' in grupo.columns and 'Descripción Concepto' in grupo.columns:
            mask = grupo['Descripción Concepto'].fillna('').astype(str).str.contains('PUNTOS', case=False)
            puntos = grupo.loc[mask, 'Importe Calc'].sum()

        total_desc = float(grupo['Retenciones'].sum() if 'Retenciones' in grupo.columns else 0)
        neto_final = total_haberes - total_desc
        v_punto = int(total_haberes / puntos) if puntos > 0 else 0

        sectores[sec].append({
            'cuil': cuil_limpio, 'nombre': nombre, 'cat': cat, 'sec': sec, 'nro_aso': nro_aso,
            'puntos': int(puntos), 'v_punto': v_punto, 'total': float(total_haberes),
            'neto': float(neto_final),
            'desc_det': grupo[grupo['Retenciones'] > 0][['Descripción Concepto', 'Retenciones']] if 'Retenciones' in grupo.columns else pd.DataFrame()
        })

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    logo_path = os.path.join(base_dir, "logo.png")
    archivos = []

    for sec, recibos in sectores.items():
        pdf = FPDF()
        pdf.set_auto_page_break(auto=False)
        for i, r in enumerate(sorted(recibos, key=lambda x: x['nombre'])):
            if i % 2 == 0:
                pdf.add_page()
                y = 10
            else:
                y = 150

            if os.path.exists(logo_path):
                try: pdf.image(logo_path, x=160, y=y, w=35)
                except: pass

            pdf.set_xy(10, y + 2)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(145, 6, "COOPERATIVA DE TRABAJO DE SERVICIOS AGROINDUSTRIALES LTDA.", ln=1)
            pdf.set_font("Arial", 'I', 9)
            pdf.cell(145, 5, "Mano de obra asociados (RT 24) / Retornos (Ley 20.337)", ln=1)
            pdf.ln(5)

            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 5, f"Asociado/a: {r['nombre']}", ln=1)
            pdf.cell(0, 5, f"Asociado n\xba: {r['nro_aso']}", ln=1)
            pdf.cell(0, 5, f"CUIL: {r['cuil']}", ln=1)
            pdf.cell(0, 5, f"Categor\xeda funcional: {r['cat']}", ln=1)
            pdf.cell(0, 5, f"Sector: {r['sec']} | Periodo: {periodo}", ln=1)
            pdf.ln(2)

            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 7, f"Puntos obtenidos: {r['puntos']} | Valor del punto: {r['v_punto']} | Total a cobrar: $ {fmt_moneda(r['total'])}", ln=1)

            if not r['desc_det'].empty:
                pdf.set_font("Arial", 'B', 9)
                pdf.cell(0, 5, "Descuentos aplicados:", ln=1)
                pdf.set_font("Arial", '', 9)
                for _, row in r['desc_det'].iterrows():
                    pdf.set_x(15)
                    pdf.cell(0, 5, f"- {row['Descripci\xf3n Concepto']}: $ {fmt_moneda(row['Retenciones'])}", ln=1)

            pdf.ln(3)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 5, f"Recib\xed conforme la suma de Pesos $ {fmt_moneda(r['neto'])} en concepto de Mano de obra asociados (RT 24) / Retornos (Ley 20.337).", align='L')

            pdf.set_y(y + 128)
            pdf.cell(0, 6, "Firma del Asociado/a: ____________________", ln=0)
            pdf.set_x(130)
            pdf.cell(0, 6, f"Fecha de emisi\xf3n: {fecha_emision}", ln=1)

        f_path = os.path.join(output_dir, f"Recibos_{sec.replace(' ','_')}.pdf")
        pdf.output(f_path)
        archivos.append(f_path)
    return archivos
