import sqlite3
import pandas as pd
import datetime

DB_NAME = "sistema_rrhh.db"


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ================================================================
# USUARIOS
# ================================================================

def login_usuario(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (username, password))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def validar_registro_asociado(cuil, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT cuil FROM maestro_asociados WHERE cuil = ? AND activo = 1", (cuil,))
    if not c.fetchone():
        conn.close()
        return False, "El CUIL no figura en los registros de la empresa."
    c.execute("SELECT id FROM usuarios WHERE cuil_asociado = ?", (cuil,))
    if c.fetchone():
        conn.close()
        return False, "Este CUIL ya tiene usuario registrado. Si olvidó la clave, contacte a RRHH."
    c.execute(
        "INSERT INTO usuarios (username, password, rol, cuil_asociado) VALUES (?, ?, 'asociado', ?)",
        (cuil, password, cuil)
    )
    conn.commit()
    conn.close()
    return True, "Registro exitoso. Ya puede iniciar sesión."


def crear_usuario_sistema(username, password, rol):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)",
            (username, password, rol)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def blanquear_clave_usuario(username, nueva_clave):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET password = ? WHERE username = ?", (nueva_clave, username))
    conn.commit()
    ok = c.rowcount > 0
    conn.close()
    return ok


def cambiar_clave_asociado(cuil, nueva_clave):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET password = ? WHERE cuil_asociado = ?", (nueva_clave, cuil))
    conn.commit()
    ok = c.rowcount > 0
    conn.close()
    return ok


def listar_usuarios_sistema():
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT id, username, rol FROM usuarios WHERE rol != 'asociado' ORDER BY rol, username",
        conn
    )
    conn.close()
    return df


# ================================================================
# SECTORES
# ================================================================

def listar_sectores():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, nombre FROM sectores ORDER BY nombre")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def agregar_sector(nombre):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO sectores (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def eliminar_sector(sector_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM sectores WHERE id = ?", (sector_id,))
    conn.commit()
    conn.close()


# ================================================================
# MAESTRO DE ASOCIADOS
# ================================================================

def guardar_o_actualizar_asociado(cuil, nro_asociado, nombre, dni, domicilio,
                                   localidad, provincia, telefono, sector,
                                   categoria, fecha_ingreso):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO maestro_asociados
            (cuil, nro_asociado, nombre_completo, dni, domicilio, localidad,
             provincia, telefono, sector, categoria, fecha_ingreso, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(cuil) DO UPDATE SET
            nro_asociado    = excluded.nro_asociado,
            nombre_completo = excluded.nombre_completo,
            dni             = excluded.dni,
            domicilio       = excluded.domicilio,
            localidad       = excluded.localidad,
            provincia       = excluded.provincia,
            telefono        = excluded.telefono,
            sector          = excluded.sector,
            categoria       = excluded.categoria,
            fecha_ingreso   = excluded.fecha_ingreso
    """, (cuil, nro_asociado, nombre, dni, domicilio, localidad,
          provincia, telefono, sector, categoria, fecha_ingreso))
    conn.commit()
    conn.close()


def buscar_asociado_por_cuil(cuil):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM maestro_asociados WHERE cuil = ?", (cuil,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def listar_asociados_activos():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT cuil, nro_asociado, nombre_completo, sector
        FROM maestro_asociados WHERE activo = 1 ORDER BY nombre_completo
    """)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def dar_baja_asociado(cuil):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE maestro_asociados SET activo = 0 WHERE cuil = ?", (cuil,))
    conn.commit()
    conn.close()


def importar_asociados_desde_df(df, sobreescribir=False):
    """Importación masiva desde DataFrame. Retorna (ok_count, lista_errores)."""
    conn = get_conn()
    c = conn.cursor()
    ok = 0
    errores = []
    df.columns = df.columns.str.strip()

    col_map = {
        'cuil':           ['cuil', 'CUIL'],
        'nro_asociado':   ['nro_asociado', 'Nro', 'nro', 'NRO'],
        'nombre_completo':['nombre_completo', 'Nombre', 'NOMBRE', 'Apellido y Nombre'],
        'dni':            ['dni', 'DNI'],
        'domicilio':      ['domicilio', 'Domicilio'],
        'localidad':      ['localidad', 'Localidad'],
        'provincia':      ['provincia', 'Provincia'],
        'telefono':       ['telefono', 'Teléfono', 'Telefono'],
        'sector':         ['sector', 'Sector'],
        'categoria':      ['categoria', 'Categoría', 'Categoria'],
        'fecha_ingreso':  ['fecha_ingreso', 'Fecha Ingreso', 'Fecha de Ingreso'],
    }

    def get_val(row, campo):
        for alias in col_map[campo]:
            if alias in row.index:
                v = row[alias]
                return '' if pd.isna(v) else str(v).strip()
        return ''

    for idx, row in df.iterrows():
        try:
            cuil = get_val(row, 'cuil')
            if not cuil:
                continue
            nombre = get_val(row, 'nombre_completo')
            if not nombre:
                errores.append(f"Fila {idx + 2}: falta nombre")
                continue
            if sobreescribir:
                c.execute("""
                    INSERT INTO maestro_asociados
                        (cuil, nro_asociado, nombre_completo, dni, domicilio, localidad,
                         provincia, telefono, sector, categoria, fecha_ingreso, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    ON CONFLICT(cuil) DO UPDATE SET
                        nro_asociado=excluded.nro_asociado, nombre_completo=excluded.nombre_completo,
                        dni=excluded.dni, domicilio=excluded.domicilio, localidad=excluded.localidad,
                        provincia=excluded.provincia, telefono=excluded.telefono, sector=excluded.sector,
                        categoria=excluded.categoria, fecha_ingreso=excluded.fecha_ingreso
                """, (cuil, get_val(row,'nro_asociado'), nombre, get_val(row,'dni'),
                      get_val(row,'domicilio'), get_val(row,'localidad'), get_val(row,'provincia'),
                      get_val(row,'telefono'), get_val(row,'sector'), get_val(row,'categoria'),
                      get_val(row,'fecha_ingreso')))
            else:
                c.execute("""
                    INSERT OR IGNORE INTO maestro_asociados
                        (cuil, nro_asociado, nombre_completo, dni, domicilio, localidad,
                         provincia, telefono, sector, categoria, fecha_ingreso, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (cuil, get_val(row,'nro_asociado'), nombre, get_val(row,'dni'),
                      get_val(row,'domicilio'), get_val(row,'localidad'), get_val(row,'provincia'),
                      get_val(row,'telefono'), get_val(row,'sector'), get_val(row,'categoria'),
                      get_val(row,'fecha_ingreso')))
            ok += 1
        except Exception as e:
            errores.append(f"Fila {idx + 2}: {e}")

    conn.commit()
    conn.close()
    return ok, errores


def obtener_mapa_nro_asociado():
    """Retorna {cuil: nro_asociado} para generación de recibos."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT cuil, nro_asociado FROM maestro_asociados")
    rows = c.fetchall()
    conn.close()
    return {r['cuil']: r['nro_asociado'] or 'S/D' for r in rows}


def obtener_reporte_asociados():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT cuil, nro_asociado, nombre_completo, dni, domicilio, localidad,
               provincia, telefono, sector, categoria, fecha_ingreso
        FROM maestro_asociados WHERE activo = 1 ORDER BY nombre_completo
    """, conn)
    conn.close()
    return df


# ================================================================
# PRÉSTAMOS
# ================================================================

def registrar_prestamo_con_cuotas(cuil, monto_total, cant_cuotas, fecha_otorgamiento, fechas_vencimientos):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO prestamos (cuil_asociado, monto_total, cantidad_cuotas, fecha_otorgamiento) VALUES (?, ?, ?, ?)",
        (cuil, monto_total, cant_cuotas, fecha_otorgamiento)
    )
    prestamo_id = c.lastrowid
    monto_cuota = round(monto_total / cant_cuotas, 2)
    for i, f_vto in enumerate(fechas_vencimientos):
        c.execute(
            "INSERT INTO prestamos_cuotas (prestamo_id, numero_cuota, monto_cuota, fecha_vencimiento) VALUES (?, ?, ?, ?)",
            (prestamo_id, i + 1, monto_cuota, f_vto)
        )
    conn.commit()
    conn.close()
    return prestamo_id


def obtener_prestamos_asociado(cuil):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT p.id AS prestamo_id, p.monto_total, p.cantidad_cuotas, p.fecha_otorgamiento,
               pc.id AS cuota_id, pc.numero_cuota, pc.monto_cuota, pc.fecha_vencimiento, pc.estado
        FROM prestamos p
        JOIN prestamos_cuotas pc ON pc.prestamo_id = p.id
        WHERE p.cuil_asociado = ?
        ORDER BY p.fecha_otorgamiento DESC, pc.numero_cuota ASC
    """, (cuil,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def actualizar_cuota(cuota_id, nueva_fecha, nuevo_estado):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE prestamos_cuotas SET fecha_vencimiento = ?, estado = ? WHERE id = ?",
        (nueva_fecha, nuevo_estado, cuota_id)
    )
    conn.commit()
    conn.close()


def obtener_reporte_prestamos():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT p.id AS prestamo_id, m.cuil, m.nombre_completo,
               p.monto_total, p.cantidad_cuotas, p.fecha_otorgamiento,
               pc.numero_cuota, pc.monto_cuota, pc.fecha_vencimiento, pc.estado
        FROM prestamos p
        JOIN maestro_asociados m ON p.cuil_asociado = m.cuil
        JOIN prestamos_cuotas pc ON pc.prestamo_id = p.id
        ORDER BY p.fecha_otorgamiento DESC, pc.numero_cuota ASC
    """, conn)
    conn.close()
    return df


# ================================================================
# SANCIONES
# ================================================================

def registrar_sancion(cuil, tipo, f_desde, f_hasta, motivo):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO sanciones (cuil_asociado, tipo, fecha_desde, fecha_hasta, motivo) VALUES (?, ?, ?, ?, ?)",
        (cuil, tipo, f_desde, f_hasta, motivo)
    )
    conn.commit()
    conn.close()


def obtener_sanciones_asociado(cuil):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, tipo, fecha_desde, fecha_hasta, motivo
        FROM sanciones WHERE cuil_asociado = ? ORDER BY fecha_desde DESC
    """, (cuil,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obtener_reporte_sanciones():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT s.id, m.cuil, m.nombre_completo, s.tipo, s.fecha_desde, s.fecha_hasta, s.motivo
        FROM sanciones s
        JOIN maestro_asociados m ON s.cuil_asociado = m.cuil
        ORDER BY s.fecha_desde DESC
    """, conn)
    conn.close()
    return df


# ================================================================
# HISTORIAL MÉDICO
# ================================================================

def registrar_ausencia_medica(cuil, fecha, motivo):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO historial_medico (cuil_asociado, fecha, motivo) VALUES (?, ?, ?)",
        (cuil, fecha, motivo)
    )
    conn.commit()
    conn.close()


def obtener_historial_medico_asociado(cuil):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id, fecha, motivo FROM historial_medico WHERE cuil_asociado = ? ORDER BY fecha DESC",
        (cuil,)
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obtener_reporte_historial_medico():
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT h.id, m.cuil, m.nombre_completo, h.fecha, h.motivo
        FROM historial_medico h
        JOIN maestro_asociados m ON h.cuil_asociado = m.cuil
        ORDER BY h.fecha DESC
    """, conn)
    conn.close()
    return df
