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
        .select("cuil, nro_asociado, nombre_completo, sector")\
        .eq("activo", True)\
        .order("nombre_completo")\
        .execute()
    return res.data or []


def dar_baja_asociado(cuil):
    supabase.table("maestro_asociados")\
        .update({"activo": False})\
        .eq("cuil", cuil)\
        .execute()


def importar_asociados_desde_df(df, sobreescribir=False):
    """
    Carga masiva desde un DataFrame (Excel subido por el admin).
    Retorna (cantidad_ok, lista_errores).
    """
    df.columns = df.columns.str.strip()
    ok = 0
    errores = []

    # Mapa flexible de nombres de columna
    alias = {
        "cuil":            ["cuil", "CUIL"],
        "nro_asociado":    ["nro_asociado", "Nro", "NRO"],
        "nombre_completo": ["nombre_completo", "Nombre", "Apellido y Nombre"],
        "dni":             ["dni", "DNI"],
        "domicilio":       ["domicilio", "Domicilio"],
        "localidad":       ["localidad", "Localidad"],
        "provincia":       ["provincia", "Provincia"],
        "telefono":        ["telefono", "Teléfono", "Telefono"],
        "sector":          ["sector", "Sector"],
        "categoria":       ["categoria", "Categoría", "Categoria"],
        "fecha_ingreso":   ["fecha_ingreso", "Fecha Ingreso"],
    }

    def get(row, campo):
        for a in alias[campo]:
            if a in row.index:
                v = row[a]
                return "" if pd.isna(v) else str(v).strip()
        return ""

    for idx, row in df.iterrows():
        try:
            cuil = get(row, "cuil")
            nombre = get(row, "nombre_completo")
            if not cuil or not nombre:
                errores.append(f"Fila {idx+2}: falta CUIL o nombre")
                continue

            datos = {
                "cuil": cuil,
                "nro_asociado": get(row, "nro_asociado"),
                "nombre_completo": nombre,
                "dni": get(row, "dni"),
                "domicilio": get(row, "domicilio"),
                "localidad": get(row, "localidad"),
                "provincia": get(row, "provincia"),
                "telefono": get(row, "telefono"),
                "sector": get(row, "sector"),
                "categoria": get(row, "categoria"),
                "fecha_ingreso": get(row, "fecha_ingreso") or None,
                "activo": True
            }

            if sobreescribir:
                supabase.table("maestro_asociados").upsert(datos).execute()
            else:
                # Solo inserta si no existe
                existe = supabase.table("maestro_asociados")\
                    .select("cuil").eq("cuil", cuil).execute()
                if not existe.data:
                    supabase.table("maestro_asociados").insert(datos).execute()
            ok += 1
        except Exception as e:
            errores.append(f"Fila {idx+2}: {e}")

    return ok, errores


def obtener_reporte_asociados():
    res = supabase.table("maestro_asociados")\
        .select("cuil, nro_asociado, nombre_completo, dni, domicilio, localidad, provincia, telefono, sector, categoria, fecha_ingreso")\
        .eq("activo", True)\
        .order("nombre_completo")\
        .execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()


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

    for _, row in df.iterrows():
        try:
            cuil = str(row.get("CUIL", "")).strip()
            if not cuil:
                continue
            filas.append({
                "cuil": cuil,
                "periodo": periodo,
                "descripcion": str(row.get("Descripción Concepto", "")).strip(),
                "tipo_concepto": str(row.get("Tipo de Concepto", "")).strip(),
                "cantidad": float(str(row.get("Cantidad", 0)).replace(",", ".") or 0),
                "importe": float(str(row.get("Importe Calc", 0)).replace(",", ".") or 0),
                "sector": str(row.get("Sector", "")).strip(),
                "categoria": str(row.get("Categoría", "")).strip(),
                "neto": float(str(row.get("NETO", 0)).replace(",", ".") or 0),
                "haberes_rem": float(str(row.get("Haberes remunerativos", 0)).replace(",", ".") or 0),
                "haberes_no_rem": float(str(row.get("Haberes No remunerativos", 0)).replace(",", ".") or 0),
                "retenciones": float(str(row.get("Retenciones", 0)).replace(",", ".") or 0),
            })
        except:
            continue

    if filas:
        # Inserta en bloques de 500 para no saturar la API
        for i in range(0, len(filas), 500):
            supabase.table("liquidaciones").insert(filas[i:i+500]).execute()

    return len(filas)


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
