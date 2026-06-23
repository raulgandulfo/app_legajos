import streamlit as st
import sqlite3
import pandas as pd
import datetime
import consultas

st.set_page_config(page_title="Portal RRHH", layout="centered", page_icon="🏢")

def get_db_connection():
    conn = sqlite3.connect("sistema_rrhh.db")
    conn.row_factory = sqlite3.Row
    return conn

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.rol = None
    st.session_state.username = None
    st.session_state.cuil = None

def login(username, password, es_asociado=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        if es_asociado and user['rol'] != 'asociado': return False, "Entrada exclusiva para asociados."
        if not es_asociado and user['rol'] == 'asociado': return False, "Asociados deben ingresar por autogestión."
        st.session_state.logged_in = True
        st.session_state.rol = user['rol']
        st.session_state.username = user['username']
        st.session_state.cuil = user['cuil_asociado']
        return True, "OK"
    return False, "Usuario o contraseña incorrectos."

def logout():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

# ==================================================================
# PANTALLA DE INGRESO 
# ==================================================================
if not st.session_state.logged_in:
    st.title("Sistema de Gestión de Personal")
    tab_aso, tab_adm = st.tabs(["👥 Ingreso ASOCIADO", "⚙️ Ingreso ADMINISTRACIÓN"])
    
    with tab_aso:
        st.subheader("Portal de Autogestión")
        with st.form("form_login_asociado"):
            cuil_input = st.text_input("Ingrese su CUIL (Sin guiones)")
            pass_aso_input = st.text_input("Contraseña", type="password")
            btn_ingresar_aso = st.form_submit_button("Ingresar", use_container_width=True)
            
        if btn_ingresar_aso:
            if cuil_input and pass_aso_input:
                exito, msj = login(cuil_input, pass_aso_input, es_asociado=True)
                if exito: st.rerun()
                else: st.error(msj)
            else: st.warning("Completá todos los campos.")
                
        # --- PROCESO DE REGISTRO ---
        st.markdown("---")
        with st.expander("No tengo clave. Registrarme por primera vez"):
            st.info("Para registrarte, tu CUIL ya debe haber sido cargado por RRHH.")
            with st.form("form_registro_nuevo"):
                reg_cuil = st.text_input("Ingrese su CUIL")
                reg_pass = st.text_input("Cree una Contraseña Nueva", type="password")
                btn_reg = st.form_submit_button("Crear mi cuenta")
                
            if btn_reg:
                if reg_cuil and reg_pass:
                    exito_reg, msj_reg = consultas.validar_registro_asociado(reg_cuil, reg_pass)
                    if exito_reg: st.success(msj_reg)
                    else: st.error(msj_reg)
                else:
                    st.warning("Debe ingresar CUIL y contraseña.")

    with tab_adm:
        st.subheader("Acceso a Gestión Operativa")
        with st.form("form_login_admin"):
            user_input = st.text_input("Usuario")
            pass_adm_input = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                exito, msj = login(user_input, pass_adm_input, es_asociado=False)
                if exito: st.rerun()
                else: st.error(msj)

# ==================================================================
# VISTAS DE USUARIOS LOGUEADOS
# ==================================================================
else:
    st.sidebar.title("Menú Principal")
    st.sidebar.write(f"Usuario: **{st.session_state.username}**")
    if st.sidebar.button("Cerrar Sesión", use_container_width=True): logout()
    st.sidebar.markdown("---")

    # 1. VISTA ASOCIADO
    if st.session_state.rol == "asociado":
        st.title("Mi Portal de Asociado")
        tab_rec, tab_pre = st.tabs(["📄 Mis Recibos", "💰 Préstamos"])
        with tab_rec: st.info("Historial de liquidaciones quincenal/mensual (Lógica de portal.py).")
        with tab_pre:
            mis_cuotas = consultas.obtener_prestamos_asociado(st.session_state.cuil)
            if mis_cuotas:
                df = pd.DataFrame([dict(r) for r in mis_cuotas])
                df.columns = ["Cuota N°", "Monto ($)", "Vencimiento", "Estado", "Fecha Otorgamiento"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else: st.write("No registrás préstamos activos.")

    # 2. VISTA AUXILIAR / ADMIN
    elif st.session_state.rol in ["auxiliar", "admin"]:
        st.title("Panel de Control Master" if st.session_state.rol == "admin" else "Panel de Operaciones")
        
        # Agregamos la pestaña de Consultas
        tab_ops, tab_reportes, tab_admin = st.tabs(["⚡ Operaciones", "📊 Consultas y Reportes", "🛠️ Herramientas Admin"])
        
        with tab_ops:
            menu_aux = st.radio("Acción a realizar:", ["Cargar / Modificar Asociado", "Otorgar Préstamo", "Registrar Sanción"], horizontal=True)
            
            if menu_aux == "Cargar / Modificar Asociado":
                with st.form("form_abm_maestro"):
                    cuil_m = st.text_input("CUIL del Asociado")
                    nombre_m = st.text_input("Nombre Completo")
                    sector_m = st.text_input("Sector")
                    cat_m = st.text_input("Categoría")
                    # CORRECCIÓN DE ERROR APLICADA (value= en vez de default=)
                    fecha_ing_m = st.date_input("Fecha de Ingreso", value=datetime.date.today())
                    if st.form_submit_button("Guardar en Maestro"):
                        consultas.guardar_o_actualizar_asociado(cuil_m, nombre_m, sector_m, cat_m, str(fecha_ing_m))
                        st.success("Guardado con éxito.")

            elif menu_aux == "Otorgar Préstamo":
                listado = consultas.listar_asociados_activos()
                if not listado: st.warning("Cargue un asociado en el Maestro primero.")
                else:
                    asoc_selec = st.selectbox("Asociado:", listado, format_func=lambda x: f"{x['nombre_completo']} ({x['cuil']})")
                    monto = st.number_input("Monto Total ($)", step=5000.0)
                    cuotas_cant = st.number_input("Cuotas", min_value=1, step=1)
                    f_otorgamiento = st.date_input("Fecha Otorgamiento", value=datetime.date.today())
                    
                    if monto > 0 and cuotas_cant > 0:
                        fechas_calc = []
                        st.write("Fechas de Vencimiento:")
                        for i in range(int(cuotas_cant)):
                            mes = (f_otorgamiento.month + i) % 12 + 1
                            año = f_otorgamiento.year + ((f_otorgamiento.month + i) // 12)
                            f_vto = st.date_input(f"Cuota {i+1}", value=datetime.date(año, mes, min(f_otorgamiento.day, 28)), key=f"v_{i}")
                            fechas_calc.append(str(f_vto))
                            
                        if st.button("Confirmar Préstamo"):
                            consultas.registrar_prestamo_con_cuotas(asoc_selec['cuil'], monto, int(cuotas_cant), str(f_otorgamiento), fechas_calc)
                            st.success("Préstamo guardado.")

            elif menu_aux == "Registrar Sanción":
                listado = consultas.listar_asociados_activos()
                if not listado: st.warning("Cargue un asociado en el Maestro primero.")
                else:
                    asoc_selec = st.selectbox("Sancionado:", listado, format_func=lambda x: x['nombre_completo'])
                    tipo_s = st.selectbox("Medida:", ["Apercibimiento", "Suspensión"])
                    f_desde = st.date_input("Desde", value=datetime.date.today())
                    f_hasta = st.date_input("Hasta", value=datetime.date.today())
                    motivo_s = st.text_area("Motivo")
                    if st.button("Registrar Sanción"):
                        consultas.registrar_sancion(asoc_selec['cuil'], tipo_s, str(f_desde), str(f_hasta), motivo_s)
                        st.success("Sanción registrada.")

        # --- PESTAÑA CONSULTAS Y EXPORTACIÓN ---
        with tab_reportes:
            st.subheader("Historiales y Bases")
            op_reporte = st.selectbox("Seleccione Base a consultar:", ["Padrón de Asociados", "Préstamos Otorgados"])
            
            if op_reporte == "Padrón de Asociados":
                df_rep = consultas.obtener_reporte_asociados()
            else:
                df_rep = consultas.obtener_reporte_prestamos()
                
            if not df_rep.empty:
                st.dataframe(df_rep, use_container_width=True)
                csv = df_rep.to_csv(index=False).encode('utf-8')
                st.download_button(label="📥 Descargar a Excel (CSV)", data=csv, file_name=f"{op_reporte}.csv", mime="text/csv")
            else:
                st.info("No hay datos cargados en esta tabla todavía.")

        with tab_admin:
            if st.session_state.rol != "admin": st.warning("Solo Administradores.")
            else:
                st.info("Opciones de Carga Masiva y Control de Usuarios (Como las definimos en la arquitectura).")