import sqlite3

DB_NAME = "sistema_rrhh.db"

def inicializar_base():
    """Crea la base de datos y todas las tablas del sistema si no existen."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. TABLA MAESTRO DE ASOCIADOS (La fuente de la verdad)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maestro_asociados (
            cuil TEXT PRIMARY KEY,
            nombre_completo TEXT NOT NULL,
            sector TEXT,
            categoria TEXT,
            fecha_ingreso DATE,
            activo INTEGER DEFAULT 1
        )
    """)

    # 2. TABLA DE USUARIOS (Reemplaza al asociados.json)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL, 
            password TEXT NOT NULL,
            rol TEXT NOT NULL CHECK(rol IN ('admin', 'auxiliar', 'asociado')),
            cuil_asociado TEXT,
            FOREIGN KEY (cuil_asociado) REFERENCES maestro_asociados (cuil)
        )
    """)

    # 3. TABLA DE PRÉSTAMOS (Cabecera)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prestamos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuil_asociado TEXT NOT NULL,
            monto_total REAL NOT NULL,
            cantidad_cuotas INTEGER NOT NULL,
            fecha_otorgamiento DATE NOT NULL,
            FOREIGN KEY (cuil_asociado) REFERENCES maestro_asociados (cuil)
        )
    """)

    # 4. TABLA DE CUOTAS (Detalle de cada préstamo, permite editar vencimientos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prestamos_cuotas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prestamo_id INTEGER NOT NULL,
            numero_cuota INTEGER NOT NULL,
            monto_cuota REAL NOT NULL,
            fecha_vencimiento DATE NOT NULL,
            estado TEXT DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'Descontada', 'Pausada')),
            FOREIGN KEY (prestamo_id) REFERENCES prestamos (id) ON DELETE CASCADE
        )
    """)

    # 5. TABLA DE SANCIONES
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sanciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuil_asociado TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('Apercibimiento', 'Suspensión')),
            fecha_desde DATE NOT NULL,
            fecha_hasta DATE NOT NULL,
            motivo TEXT,
            FOREIGN KEY (cuil_asociado) REFERENCES maestro_asociados (cuil)
        )
    """)

    # --- DATOS DE ARRANQUE (Usuario Admin por defecto) ---
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO usuarios (username, password, rol) 
            VALUES ('admin', 'admin123', 'admin')
        """)
        print("Usuario administrador creado por defecto (admin / admin123).")

    conn.commit()
    conn.close()
    print("Base de datos estructurada y lista para operar.")

if __name__ == "__main__":
    inicializar_base()