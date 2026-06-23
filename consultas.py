import sqlite3
import datetime
import pandas as pd

DB_NAME = "sistema_rrhh.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# --- GESTIÓN DE ASOCIADOS ---
def guardar_o_actualizar_asociado(cuil, nombre, sector, categoria, fecha_ingreso):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO maestro_asociados (cuil, nombre_completo, sector, categoria, fecha_ingreso, activo)
        VALUES (?, ?, ?, ?, ?, 1)
        ON CONFLICT(cuil) DO UPDATE SET
            nombre_completo = excluded.nombre_completo,
            sector = excluded.sector,
            categoria = excluded.categoria,
            fecha_ingreso = excluded.fecha_ingreso
    """, (cuil, nombre, sector, categoria, fecha_ingreso))
    conn.commit()
    conn.close()

def listar_asociados_activos():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT cuil, nombre_completo, sector FROM maestro_asociados WHERE activo = 1 ORDER BY nombre_completo")
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- GESTIÓN DE PRÉSTAMOS Y SANCIONES ---
def registrar_prestamo_con_cuotas(cuil, monto_total, cant_cuotas, fecha_otorgamiento, fechas_vencimientos):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO prestamos (cuil_asociado, monto_total, cantidad_cuotas, fecha_otorgamiento) VALUES (?, ?, ?, ?)", (cuil, monto_total, cant_cuotas, fecha_otorgamiento))
    prestamo_id = cursor.lastrowid
    monto_cuota = round(monto_total / cant_cuotas, 2)
    
    for i, f_vto in enumerate(fechas_vencimientos):
        cursor.execute("INSERT INTO prestamos_cuotas (prestamo_id, numero_cuota, monto_cuota, fecha_vencimiento, estado) VALUES (?, ?, ?, ?, 'Pendiente')", (prestamo_id, i + 1, monto_cuota, f_vto))
    conn.commit()
    conn.close()

def obtener_prestamos_asociado(cuil):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pc.numero_cuota, pc.monto_cuota, pc.fecha_vencimiento, pc.estado, p.fecha_otorgamiento
        FROM prestamos_cuotas pc
        JOIN prestamos p ON pc.prestamo_id = p.id
        WHERE p.cuil_asociado = ? ORDER BY pc.fecha_vencimiento ASC
    """, (cuil,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def registrar_sancion(cuil, tipo, f_desde, f_hasta, motivo):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sanciones (cuil_asociado, tipo, fecha_desde, fecha_hasta, motivo) VALUES (?, ?, ?, ?, ?)", (cuil, tipo, f_desde, f_hasta, motivo))
    conn.commit()
    conn.close()

# --- ADMINISTRACIÓN DE USUARIOS Y REGISTRO ---
def validar_registro_asociado(cuil, password):
    """Verifica si el CUIL existe en el maestro y le crea el usuario si no lo tiene."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Verificar si existe en el padrón de RRHH
    cursor.execute("SELECT * FROM maestro_asociados WHERE cuil = ?", (cuil,))
    maestro = cursor.fetchone()
    if not maestro:
        conn.close()
        return False, "El CUIL ingresado no figura en los registros de la empresa."
        
    # 2. Verificar si ya tiene cuenta creada
    cursor.execute("SELECT * FROM usuarios WHERE cuil_asociado = ?", (cuil,))
    if cursor.fetchone():
        conn.close()
        return False, "Este CUIL ya tiene un usuario registrado. Si olvidó la clave, contacte a RRHH."
        
    # 3. Crear el usuario
    cursor.execute("INSERT INTO usuarios (username, password, rol, cuil_asociado) VALUES (?, ?, 'asociado', ?)", (cuil, password, cuil))
    conn.commit()
    conn.close()
    return True, "Registro exitoso. Ya puede iniciar sesión."

def crear_usuario_sistema(username, password, rol, cuil=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (username, password, rol, cuil_asociado) VALUES (?, ?, ?, ?)", (username, password, rol, cuil))
        conn.commit()
        exito = True
    except sqlite3.IntegrityError:
        exito = False
    conn.close()
    return exito

def blanquear_clave_usuario(username, nueva_clave):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET password = ? WHERE username = ?", (nueva_clave, username))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

# --- REPORTES Y EXPORTACIÓN ---
def obtener_reporte_asociados():
    conn = get_connection()
    df = pd.read_sql_query("SELECT cuil, nombre_completo, sector, categoria, fecha_ingreso FROM maestro_asociados", conn)
    conn.close()
    return df

def obtener_reporte_prestamos():
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT p.cuil_asociado, m.nombre_completo, p.monto_total, p.cantidad_cuotas, p.fecha_otorgamiento
        FROM prestamos p JOIN maestro_asociados m ON p.cuil_asociado = m.cuil
    """, conn)
    conn.close()
    return df