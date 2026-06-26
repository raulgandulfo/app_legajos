import os
from supabase import create_client
from dotenv import load_dotenv
import pandas as pd

# Carga las variables del archivo .env
load_dotenv()

# Crea la conexión a Supabase (se reutiliza en todas las funciones)
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

# ================================================================
# USUARIOS
# ================================================================

def login_usuario(username, password):
    """Busca un usuario por nombre y clave. Retorna sus datos o None."""
    res = supabase.table("usuarios")\
        .select("*")\
        .eq("username", username)\
        .eq("password", password)\
        .execute()
    return res.data[0] if res.data else None


def validar_registro_asociado(cuil, password):
    """
    Registra un asociado como usuario del portal.
    Primero verifica que el CUIL exista en el maestro (cargado por RRHH).
    """
    # ¿Existe en el maestro?
    en_maestro = supabase.table("maestro_asociados")\
        .select("cuil")\
        .eq("cuil", cuil)\
        .eq("activo", True)\
        .execute()
    if not en_maestro.data:
        return False, "El CUIL no figura en los registros de la empresa."

    # ¿Ya tiene usuario creado?
    ya_existe = supabase.table("usuarios")\
        .select("id")\
        .eq("cuil_asociado", cuil)\
        .execute()
    if ya_existe.data:
        return False, "Este CUIL ya tiene usuario. Si olvidó la clave, contacte a RRHH."

    # Crea el usuario
    supabase.table("usuarios").insert({
        "username": cuil,
        "password": password,
        "rol": "asociado",
        "cuil_asociado": cuil
    }).execute()
    return True, "Registro exitoso. Ya puede iniciar sesión."


def crear_usuario_sistema(username, password, rol):
    """Crea un usuario admin o auxiliar."""
    try:
        supabase.table("usuarios").insert({
            "username": username,
            "password": password,
            "rol": rol
        }).execute()
        return True
    except:
        return False


def blanquear_clave(username, nueva_clave):
    """Resetea la contraseña de cualquier usuario."""
    res = supabase.table("usuarios")\
        .update({"password": nueva_clave})\
        .eq("username", username)\
        .execute()
    return len(res.data) > 0


def cambiar_clave_asociado(cuil, nueva_clave):
    """El propio asociado cambia su clave."""
    supabase.table("usuarios")\
        .update({"password": nueva_clave})\
        .eq("cuil_asociado", cuil)\
        .execute()


def listar_usuarios_sistema():
    """Lista todos los usuarios admin y auxiliar (no asociados)."""
    res = supabase.table("usuarios")\
        .select("id, username, rol")\
        .neq("rol", "asociado")\
        .order("rol")\
        .execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()


# ================================================================
# SECTORES
# ================================================================

def listar_sectores():
    """Retorna la lista de sectores cargados por el admin."""
    res = supabase.table("sectores").select("*").order("nombre").execute()
    return res.data or []


def agregar_sector(nombre):
    try:
        supabase.table("sectores").insert({"nombre": nombre.strip()}).execute()
        return True
    except:
        return False


def eliminar_sector(sector_id):
    supabase.table("sectores").delete().eq("id", sector_id).execute()


# ================================================================
# MAESTRO DE ASOCIADOS
# ================================================================

def guardar_o_actualizar_asociado(datos: dict):
    """
    Inserta o actualiza un asociado en el maestro.
    Si el CUIL ya existe, pisa los datos. Si no existe, lo crea.
    'datos' es un diccionario con todos los campos.
    """
    supabase.table("maestro_asociados").upsert(datos).execute()


def buscar_asociado_por_cuil(cuil):
    res = supabase.table("maestro_asociados")\
        .select("*")\
        .eq("cuil", cuil)\
        .execute()
    return res.data[0] if res.data else None


def listar_asociados_activos():
    res = supabase.table("maestro_asociados")\
        .select("cuil, nro_asociado, nombre_completo, sector, categoria")\
        .eq("activo", True)\
        .order("nombre_completo")\
        .execute()
    return res.data or []


def dar_baja_asociado(cuil):
    supabase.table("maestro_asociados")\
        .update({"activo": False})\
        .eq("cuil", cuil)\
        .execute()


def _parsear_xls_onvio(contenido_bytes):
    """Parsea el formato XML de Onvio (.xls) y retorna un DataFrame."""
    from lxml import etree
    contenido = contenido_bytes.replace(b"version='1.0'encoding=", b"version='1.0' encoding=")
    ns = {'ss': 'urn:schemas-microsoft-com:office:spreadsheet'}
    tree = etree.fromstring(contenido)
    rows = tree.findall('.//ss:Row', ns)
    if not rows:
        return pd.DataFrame()
    headers = [c.findtext('ss:Data', namespaces=ns) for c in rows[0].findall('ss:Cell', ns)]
    data = []
    for row in rows[1:]:
        cells = row.findall('ss:Cell', ns)
        vals = [c.findtext('ss:Data', namespaces=ns) for c in cells]
        # Rellenar celdas faltantes
        while len(vals) < len(headers):
            vals.append(None)
        data.append(dict(zip(headers, vals)))
    return pd.DataFrame(data)


def importar_asociados_desde_df(df_o_bytes, sobreescribir=False):
    """
    Carga masiva desde un DataFrame o bytes de archivo XLS de Onvio.
    Retorna (cantidad_ok, lista_errores).
    """
    if isinstance(df_o_bytes, bytes):
        df = _parsear_xls_onvio(df_o_bytes)
    else:
        df = df_o_bytes.copy()

    # Deduplicar columnas: procesar en reversa para que la ÚLTIMA ocurrencia
    # de cada nombre quede limpia (sin sufijo). Así "Sector" (col 58) prevalece
    # sobre "Sector " (col 23) del XLS de Onvio.
    n = len(df.columns)
    seen = {}
    new_cols_rev = []
    for i in range(n - 1, -1, -1):
        c_strip = str(df.columns[i]).strip()
        if c_strip in seen:
            new_cols_rev.append(f"{c_strip}_dup{seen[c_strip]}")
            seen[c_strip] += 1
        else:
            new_cols_rev.append(c_strip)
            seen[c_strip] = 1
    df.columns = list(reversed(new_cols_rev))

    ok = 0
    errores = []

    alias = {
        "cuil":            ["CUIL", "cuil"],
        "nro_asociado":    ["Número", "Nro", "nro_asociado", "NRO"],
        "nombre_completo": ["Apellido y Nombre", "Nombre", "nombre_completo"],
        "dni":             ["Nro. de Documento", "DNI", "dni", "Documento"],
        "domicilio":       ["Calle", "Domicilio", "domicilio"],
        "localidad":       ["Localidad", "localidad"],
        "provincia":       ["Provincia", "provincia"],
        "telefono":        ["Teléfono móvil", "Teléfono fijo", "Teléfono", "Telefono", "telefono"],
        "sector":          ["Sector", "sector"],
        "categoria":       ["Categoría", "Categoria", "categoria"],
        "fecha_ingreso":   ["Fecha de alta", "Fecha Ingreso", "fecha_ingreso"],
        "cod_area":        ["Código de área", "Cod. Area"],
    }

    def get(row, campo):
        for a in alias.get(campo, []):
            if a in row.index:
                v = row[a]
                if isinstance(v, pd.Series):
                    v = v.iloc[0]
                if not pd.isna(v):
                    return str(v).strip()
        return ""

    for idx, row in df.iterrows():
        try:
            cuil = get(row, "cuil").replace("-", "").replace(" ", "")
            nombre = get(row, "nombre_completo")
            if not cuil or not nombre or cuil == "nan":
                continue

            # Teléfono: combinar área + fijo si no hay móvil
            tel = get(row, "telefono")
            if not tel:
                area = get(row, "cod_area")
                fijo = ""
                for col in ["Teléfono fijo", "telefono"]:
                    if col in row.index and not pd.isna(row.get(col)):
                        fijo = str(row[col]).strip()
                        break
                tel = f"0{area}{fijo}" if area and fijo else fijo

            datos = {
                "cuil": cuil,
                "nro_asociado": get(row, "nro_asociado") or None,
                "nombre_completo": nombre,
                "dni": get(row, "dni") or None,
                "domicilio": get(row, "domicilio") or None,
                "localidad": get(row, "localidad") or None,
                "provincia": get(row, "provincia") or None,
                "telefono": tel or None,
                "sector": get(row, "sector") or None,
                "categoria": get(row, "categoria") or None,
                "fecha_ingreso": get(row, "fecha_ingreso") or None,
                "activo": True
            }

            if sobreescribir:
                supabase.table("maestro_asociados").upsert(datos, on_conflict="cuil").execute()
            else:
                existe = supabase.table("maestro_asociados").select("cuil").eq("cuil", cuil).execute()
                if not existe.data:
                    supabase.table("maestro_asociados").insert(datos).execute()
            ok += 1
        except Exception as e:
            errores.append(f"Fila {idx+2} ({nombre}): {e}")

    return ok, errores


def obtener_reporte_asociados():
    res = supabase.table("maestro_asociados")\
        .select("cuil, nro_asociado, nombre_completo, dni, domicilio, localidad, provincia, telefono, sector, categoria, fecha_ingreso")\
        .eq("activo", True)\
        .order("nombre_completo")\
        .execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()


def listar_categorias():
    """Retorna la lista de categorías únicas ya cargadas en el maestro."""
    res = supabase.table("maestro_asociados").select("categoria").eq("activo", True).execute()
    cats = sorted(set(r["categoria"] for r in (res.data or []) if r.get("categoria")))
    return cats


def obtener_mapa_nro_asociado():
    """Para la generación de recibos PDF: {cuil: nro_asociado}."""
    res = supabase.table("maestro_asociados").select("cuil, nro_asociado").execute()
    return {r["cuil"]: r["nro_asociado"] or "S/D" for r in (res.data or [])}


# ================================================================
# LIQUIDACIONES (reemplaza el Excel en disco)
# ================================================================

def cargar_liquidacion_desde_df(df, periodo):
    """
    Procesa el Excel subido por el admin y guarda cada fila en Supabase.
    El período es un texto como 'QUINCENA 1 - JUNIO 2025'.
    Nunca pisa datos anteriores, siempre acumula.
    """
    df.columns = df.columns.str.strip()
    filas = []

    def _float(val):
        try:
            return float(str(val).replace(",", ".") or 0)
        except:
            return 0.0

    for _, row in df.iterrows():
        try:
            cuil = str(row.get("CUIL", "")).strip()
            if not cuil or cuil == "nan":
                continue
            filas.append({
                "cuil": cuil,
                "periodo": periodo,
                "nro_legajo": str(row.get("Nro. de Legajo", row.get("Nro. Legajo", ""))).strip() or None,
                "nombre_completo": str(row.get("Apellido y Nombre", "")).strip() or None,
                "descripcion": str(row.get("Descripción Concepto", "")).strip(),
                "tipo_concepto": str(row.get("Tipo de Concepto", "")).strip(),
                "cantidad": _float(row.get("Cantidad", 0)),
                "importe": _float(row.get("Importe Calc", row.get("Importe", 0))),
                "sector": str(row.get("Sector", "")).strip(),
                "categoria": str(row.get("Categoría", "")).strip(),
                "jornal_basico": _float(row.get("Jornal / Básico", row.get("Jornal/Básico", 0))),
                "neto": _float(row.get("NETO", row.get("Neto", 0))),
                "haberes_rem": _float(row.get("Haberes remunerativos", 0)),
                "haberes_no_rem": _float(row.get("Haberes No remunerativos", 0)),
                "retenciones": _float(row.get("Retenciones", row.get("Total Retenciones", 0))),
            })
        except:
            continue

    if filas:
        # Inserta en bloques de 500 para no saturar la API
        for i in range(0, len(filas), 500):
            supabase.table("liquidaciones").insert(filas[i:i+500]).execute()

    return len(filas)


def obtener_liquidacion_para_recibos(periodos: list):
    """
    Trae todos los registros de uno o más períodos y los devuelve con los
    nombres de columna que espera recibos.py (mayúsculas/español).
    """
    res = supabase.table("liquidaciones")\
        .select("*")\
        .in_("periodo", periodos)\
        .execute()
    if not res.data:
        return pd.DataFrame()
    df = pd.DataFrame(res.data)

    # Traer nombres de asociados para enriquecer el DataFrame
    cuils = df["cuil"].unique().tolist()
    aso_res = supabase.table("maestro_asociados")\
        .select("cuil, nombre_completo, nro_asociado")\
        .in_("cuil", cuils)\
        .execute()
    aso_map = {r["cuil"]: r for r in (aso_res.data or [])}

    # Nombre desde la propia liquidación (guardado al cargar) o desde maestro
    df["Apellido y Nombre"] = df.apply(
        lambda r: r.get("nombre_completo") or aso_map.get(r["cuil"], {}).get("nombre_completo", ""), axis=1)
    df["Nro. de Legajo"] = df.apply(
        lambda r: r.get("nro_legajo") or aso_map.get(r["cuil"], {}).get("nro_asociado", "S/D"), axis=1)

    df = df.rename(columns={
        "cuil":           "CUIL",
        "descripcion":    "Descripción Concepto",
        "tipo_concepto":  "Tipo de Concepto",
        "cantidad":       "Cantidad",
        "importe":        "Importe Calc",
        "sector":         "Sector",
        "categoria":      "Categoría",
        "jornal_basico":  "Jornal / Básico",
        "neto":           "NETO",
        "haberes_rem":    "Haberes remunerativos",
        "haberes_no_rem": "Haberes No remunerativos",
        "retenciones":    "Retenciones",
        "periodo":        "Liquidación",
    })
    return df


def obtener_periodos_asociado(cuil):
    """Lista todos los períodos disponibles para un CUIL."""
    res = supabase.table("liquidaciones")\
        .select("periodo")\
        .eq("cuil", cuil)\
        .execute()
    if not res.data:
        return []
    periodos = list(set(r["periodo"] for r in res.data))
    return sorted(periodos, reverse=True)


def obtener_liquidacion(cuil, periodo):
    """Trae todas las filas de un período para un asociado."""
    res = supabase.table("liquidaciones")\
        .select("*")\
        .eq("cuil", cuil)\
        .eq("periodo", periodo)\
        .execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()


def listar_periodos_disponibles():
    """Para el admin: todos los períodos cargados."""
    res = supabase.table("liquidaciones").select("periodo").execute()
    if not res.data:
        return []
    return sorted(list(set(r["periodo"] for r in res.data)), reverse=True)


# ================================================================
# PRÉSTAMOS
# ================================================================

def registrar_prestamo(cuil, monto_total, cant_cuotas, fecha_otorgamiento, fechas_vencimientos):
    """
    Crea un préstamo y sus cuotas en dos pasos:
    1. Inserta la cabecera del préstamo y obtiene el ID generado.
    2. Inserta cada cuota vinculada a ese ID.
    """
    # Paso 1: cabecera
    res = supabase.table("prestamos").insert({
        "cuil_asociado": cuil,
        "monto_total": monto_total,
        "cantidad_cuotas": cant_cuotas,
        "fecha_otorgamiento": fecha_otorgamiento
    }).execute()
    prestamo_id = res.data[0]["id"]

    # Paso 2: cuotas
    monto_cuota = round(monto_total / cant_cuotas, 2)
    cuotas = [
        {
            "prestamo_id": prestamo_id,
            "numero_cuota": i + 1,
            "monto_cuota": monto_cuota,
            "fecha_vencimiento": fechas_vencimientos[i],
            "estado": "Pendiente"
        }
        for i in range(cant_cuotas)
    ]
    supabase.table("prestamos_cuotas").insert(cuotas).execute()
    return prestamo_id


def obtener_prestamos_asociado(cuil):
    """Trae todos los préstamos y cuotas de un asociado."""
    res = supabase.table("prestamos")\
        .select("*, prestamos_cuotas(*)")\
        .eq("cuil_asociado", cuil)\
        .order("fecha_otorgamiento", desc=True)\
        .execute()
    return res.data or []


def actualizar_cuota(cuota_id, nueva_fecha, nuevo_estado):
    supabase.table("prestamos_cuotas")\
        .update({"fecha_vencimiento": nueva_fecha, "estado": nuevo_estado})\
        .eq("id", cuota_id)\
        .execute()


def obtener_reporte_prestamos():
    res = supabase.table("prestamos")\
        .select("*, maestro_asociados(cuil, nombre_completo), prestamos_cuotas(*)")\
        .order("fecha_otorgamiento", desc=True)\
        .execute()
    if not res.data:
        return pd.DataFrame()
    filas = []
    for p in res.data:
        for c in p.get("prestamos_cuotas", []):
            filas.append({
                "CUIL": p["cuil_asociado"],
                "Nombre": p["maestro_asociados"]["nombre_completo"] if p.get("maestro_asociados") else "",
                "Monto Total": p["monto_total"],
                "Cuota N°": c["numero_cuota"],
                "Monto Cuota": c["monto_cuota"],
                "Vencimiento": c["fecha_vencimiento"],
                "Estado": c["estado"],
                "Otorgamiento": p["fecha_otorgamiento"],
            })
    return pd.DataFrame(filas)


# ================================================================
# SANCIONES
# ================================================================

def registrar_sancion(cuil, tipo, f_desde, f_hasta, motivo):
    supabase.table("sanciones").insert({
        "cuil_asociado": cuil,
        "tipo": tipo,
        "fecha_desde": f_desde,
        "fecha_hasta": f_hasta,
        "motivo": motivo
    }).execute()


def obtener_sanciones_asociado(cuil):
    res = supabase.table("sanciones")\
        .select("*")\
        .eq("cuil_asociado", cuil)\
        .order("fecha_desde", desc=True)\
        .execute()
    return res.data or []


def obtener_reporte_sanciones():
    res = supabase.table("sanciones")\
        .select("*, maestro_asociados(nombre_completo)")\
        .order("fecha_desde", desc=True)\
        .execute()
    if not res.data:
        return pd.DataFrame()
    filas = [{
        "CUIL": s["cuil_asociado"],
        "Nombre": s["maestro_asociados"]["nombre_completo"] if s.get("maestro_asociados") else "",
        "Tipo": s["tipo"],
        "Desde": s["fecha_desde"],
        "Hasta": s["fecha_hasta"],
        "Motivo": s["motivo"],
    } for s in res.data]
    return pd.DataFrame(filas)


# ================================================================
# HISTORIAL MÉDICO
# ================================================================

def registrar_ausencia_medica(cuil, fecha, motivo):
    supabase.table("historial_medico").insert({
        "cuil_asociado": cuil,
        "fecha": fecha,
        "motivo": motivo
    }).execute()


def obtener_historial_medico(cuil):
    res = supabase.table("historial_medico")\
        .select("*")\
        .eq("cuil_asociado", cuil)\
        .order("fecha", desc=True)\
        .execute()
    return res.data or []


def obtener_reporte_historial_medico():
    res = supabase.table("historial_medico")\
        .select("*, maestro_asociados(nombre_completo)")\
        .order("fecha", desc=True)\
        .execute()
    if not res.data:
        return pd.DataFrame()
    filas = [{
        "CUIL": h["cuil_asociado"],
        "Nombre": h["maestro_asociados"]["nombre_completo"] if h.get("maestro_asociados") else "",
        "Fecha": h["fecha"],
        "Motivo": h["motivo"],
    } for h in res.data]
    return pd.DataFrame(filas)
