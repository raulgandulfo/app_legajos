import sqlite3

DB_NAME = "sistema_rrhh.db"

def inicializar_base():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS sectores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS maestro_asociados (
        cuil TEXT PRIMARY KEY,
        nro_asociado TEXT,
        nombre_completo TEXT NOT NULL,
        dni TEXT,
        domicilio TEXT,
        localidad TEXT,
        provincia TEXT,
        telefono TEXT,
        sector TEXT,
        categoria TEXT,
        fecha_ingreso DATE,
        activo INTEGER DEFAULT 1
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        rol TEXT NOT NULL CHECK(rol IN ('admin', 'auxiliar', 'asociado')),
        cuil_asociado TEXT,
        FOREIGN KEY (cuil_asociado) REFERENCES maestro_asociados(cuil)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS prestamos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuil_asociado TEXT NOT NULL,
        monto_total REAL NOT NULL,
        cantidad_cuotas INTEGER NOT NULL,
        fecha_otorgamiento DATE NOT NULL,
        FOREIGN KEY (cuil_asociado) REFERENCES maestro_asociados(cuil)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS prestamos_cuotas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prestamo_id INTEGER NOT NULL,
        numero_cuota INTEGER NOT NULL,
        monto_cuota REAL NOT NULL,
        fecha_vencimiento DATE NOT NULL,
        estado TEXT DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'Descontada', 'Pausada')),
        FOREIGN KEY (prestamo_id) REFERENCES prestamos(id) ON DELETE CASCADE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS sanciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuil_asociado TEXT NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('Apercibimiento', 'Suspensión')),
        fecha_desde DATE NOT NULL,
        fecha_hasta DATE NOT NULL,
        motivo TEXT,
        FOREIGN KEY (cuil_asociado) REFERENCES maestro_asociados(cuil)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS historial_medico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuil_asociado TEXT NOT NULL,
        fecha DATE NOT NULL,
        motivo TEXT,
        FOREIGN KEY (cuil_asociado) REFERENCES maestro_asociados(cuil)
    )""")

    c.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios (username, password, rol) VALUES ('admin', 'admin123', 'admin')")
        print("Usuario admin creado: admin / admin123")

    conn.commit()
    conn.close()


def migrar_base():
    """Agrega columnas nuevas a tablas existentes sin romper datos previos."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    columnas_nuevas = [
        ("maestro_asociados", "nro_asociado", "TEXT"),
        ("maestro_asociados", "dni", "TEXT"),
        ("maestro_asociados", "domicilio", "TEXT"),
        ("maestro_asociados", "localidad", "TEXT"),
        ("maestro_asociados", "provincia", "TEXT"),
        ("maestro_asociados", "telefono", "TEXT"),
    ]
    for tabla, col, tipo in columnas_nuevas:
        try:
            c.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


if __name__ == "__main__":
    inicializar_base()
