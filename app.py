# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import datetime
import consultas

st.set_page_config(
    page_title="Sistema RRHH",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="auto"
)

st.markdown("""
<style>
    /* ===== FONDO Y ESTRUCTURA ===== */
    .stApp { background-color: #eef2f7; }
    #MainMenu, footer, header { visibility: hidden; }

    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] { background-color: #1e293b !important; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    [data-testid="stSidebar"] .stButton button {
        background-color: #ef4444 !important;
        color: white !important;
        border: none !important;
    }
    [data-testid="stSidebar"] hr { border-color: #334155 !important; }

    /* ===== INPUTS (selectores específicos de Streamlit) ===== */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stDateInput"] input,
    [data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
    }
    /* Labels de inputs */
    [data-testid="stTextInput"] label,
    [data-testid="stNumberInput"] label,
    [data-testid="stDateInput"] label,
    [data-testid="stTextArea"] label,
    [data-testid="stSelectbox"] label,
    [data-testid="stCheckbox"] label,
    [data-testid="stFileUploader"] label {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
    }
    /* Selectbox */
    [data-testid="stSelectbox"] > div > div {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }

    /* ===== BOTONES PRINCIPALES ===== */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s !important;
    }
    .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(37,99,235,0.35) !important;
    }
    .stButton button[kind="secondary"] {
        background-color: #f1f5f9 !important;
        color: #374151 !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }

    /* ===== TARJETAS ===== */
    .card {
        background: white;
        border-radius: 14px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 1px 6px rgba(0,0,0,0.07), 0 4px 16px rgba(0,0,0,0.05);
        border: 1px solid #e8edf3;
    }
    .card-blue  { border-top: 4px solid #3b82f6; }
    .card-red   { border-top: 4px solid #ef4444; }
    .card-green { border-top: 4px solid #10b981; }

    /* ===== PORTAL HOME ===== */
    .portal-card {
        background: white;
        border-radius: 18px;
        padding: 2.5rem 2rem;
        text-align: center;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        border: 1px solid #e8edf3;
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
    }
    .portal-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.14);
    }
    .portal-icon { font-size: 3.5rem; margin-bottom: 1rem; }
    .portal-title { font-size: 1.1rem; font-weight: 700; color: #1e293b; letter-spacing: .5px; }
    .portal-desc { color: #64748b; font-size: 0.9rem; margin-top: 0.4rem; }

    /* ===== NETO ===== */
    .neto-box {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        color: white !important;
        border-radius: 14px;
        padding: 2rem;
        text-align: center;
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 1px;
        box-shadow: 0 8px 32px rgba(15,23,42,0.3);
        margin-top: 1.25rem;
    }
    .neto-label { font-size: 0.85rem; font-weight: 400; letter-spacing: 2px; opacity: 0.7; margin-bottom: 0.5rem; }

    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f1f5f9;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 7px;
        font-weight: 500;
        color: #64748b;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: white !important;
        color: #1e293b !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    }

    /* ===== FILE UPLOADER ===== */
    [data-testid="stFileUploader"] section {
        background-color: #f8fafc !important;
        border: 2px dashed #cbd5e1 !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: #3b82f6 !important;
        background-color: #eff6ff !important;
    }
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] small {
        color: #374151 !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #3b82f6 !important;
        color: white !important;
        border-radius: 6px !important;
        border: none !important;
    }

    /* ===== DATAFRAME ===== */
    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; box-shadow: 0 1px 6px rgba(0,0,0,0.06); }

    /* ===== TIPOGRAFÍA GENERAL ===== */
    h1, h2, h3 { color: #1e293b !important; }
    p, span, label { color: #374151; }

    /* ===== HEADER BAR ===== */
    .top-bar {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .top-bar .app-title { font-size: 1.4rem; font-weight: 700; }
    .top-bar .app-sub   { font-size: 0.85rem; opacity: 0.65; }
</style>
""", unsafe_allow_html=True)

for k, v in [("logged_in", False), ("rol", None), ("username", None), ("cuil", None), ("portal", None), ("aso_edit", {}), ("aso_edit_show", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

def logout():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()

def fmt_moneda(v):
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"

# ================================================================
# PANTALLA INICIO
# ================================================================
if st.session_state.portal is None:
    st.markdown("""
    <div class="top-bar">
        <div>
            <div class="app-title">🏢 Sistema de Gestión de Personal</div>
            <div class="app-sub">Cooperativa Agroindustrial · RRHH</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _, col1, col2, _ = st.columns([1, 2, 2, 1])
    with col1:
        st.markdown("""
        <div class="portal-card card-blue">
            <div class="portal-icon">👤</div>
            <div class="portal-title">SOY ASOCIADO</div>
            <div class="portal-desc">Consultá tus recibos, préstamos, sanciones e historial médico</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Ingresar como Asociado", use_container_width=True, type="primary"):
            st.session_state.portal = "asociado"
            st.rerun()
    with col2:
        st.markdown("""
        <div class="portal-card card-red">
            <div class="portal-icon">⚙️</div>
            <div class="portal-title">ADMINISTRACIÓN</div>
            <div class="portal-desc">Panel de gestión para el equipo de Recursos Humanos</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Ingresar como Administración", use_container_width=True):
            st.session_state.portal = "admin"
            st.rerun()

# ================================================================
# PORTAL ASOCIADO
# ================================================================
elif st.session_state.portal == "asociado":

    if not st.session_state.logged_in:
        st.markdown("""
        <div class="top-bar">
            <div>
                <div class="app-title">👤 Portal del Asociado</div>
                <div class="app-sub">Cooperativa Agroindustrial · RRHH</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        col_back, _ = st.columns([1, 8])
        with col_back:
            if st.button("← Volver al inicio"):
                st.session_state.portal = None
                st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        _, col_form, _ = st.columns([1, 2, 1])
        with col_form:
            st.markdown('<div class="card card-blue">', unsafe_allow_html=True)
            tab_login, tab_registro = st.tabs(["🔐 Ya tengo cuenta", "📝 Registrarme"])
            with tab_login:
                with st.form("form_login_aso"):
                    cuil_in = st.text_input("CUIL (sin guiones)", placeholder="20123456789")
                    pass_in = st.text_input("Contraseña", type="password")
                    if st.form_submit_button("Ingresar", use_container_width=True, type="primary"):
                        if cuil_in and pass_in:
                            user = consultas.login_usuario(cuil_in, pass_in)
                            if user and user["rol"] == "asociado":
                                st.session_state.logged_in = True
                                st.session_state.rol = "asociado"
                                st.session_state.username = user["username"]
                                st.session_state.cuil = user["cuil_asociado"]
                                st.rerun()
                            else:
                                st.error("CUIL o contraseña incorrectos.")
                        else:
                            st.warning("Completá todos los campos.")
            with tab_registro:
                st.info("Tu CUIL debe haber sido cargado previamente por RRHH.")
                with st.form("form_registro_aso"):
                    reg_cuil = st.text_input("Tu CUIL (sin guiones)", placeholder="20123456789")
                    reg_pass = st.text_input("Elegí una contraseña", type="password")
                    reg_pass2 = st.text_input("Confirmá la contraseña", type="password")
                    if st.form_submit_button("Crear mi cuenta", use_container_width=True):
                        if not reg_cuil or not reg_pass:
                            st.warning("Completá todos los campos.")
                        elif reg_pass != reg_pass2:
                            st.error("Las contraseñas no coinciden.")
                        else:
                            ok, msg = consultas.validar_registro_asociado(reg_cuil, reg_pass)
                            st.success(msg) if ok else st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        cuil = st.session_state.cuil
        asociado = consultas.buscar_asociado_por_cuil(cuil)
        nombre = asociado["nombre_completo"] if asociado else cuil
        with st.sidebar:
            st.markdown(f"### 👤 {nombre}")
            st.markdown(f"CUIL: `{cuil}`")
            st.divider()
            if st.button("Cerrar Sesión", use_container_width=True):
                logout()

        st.markdown(f"""
        <div class="top-bar">
            <div>
                <div class="app-title">Bienvenido/a, {nombre.split()[0]}</div>
                <div class="app-sub">Portal del Asociado · CUIL {cuil}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        tab_rec, tab_pre, tab_san, tab_med, tab_cuenta = st.tabs([
            "📄 Mis Recibos", "💰 Mis Préstamos", "⚠️ Sanciones", "🏥 Historial Médico", "🔐 Mi Cuenta"
        ])

        with tab_rec:
            periodos = consultas.obtener_periodos_asociado(cuil)
            if not periodos:
                st.info("Todavía no hay liquidaciones disponibles.")
            else:
                periodo_sel = st.selectbox("📅 Período:", periodos)
                df_liq = consultas.obtener_liquidacion(cuil, periodo_sel)
                if df_liq.empty:
                    st.warning("No se encontraron datos para este período.")
                else:
                    st.markdown(f'<div class="card"><b>Sector:</b> {df_liq["sector"].iloc[0]} &nbsp;|&nbsp; <b>Categoría:</b> {df_liq["categoria"].iloc[0]}</div>', unsafe_allow_html=True)
                    st.markdown("#### Detalle de la Liquidación")
                    tipos_validos = ["Remunerativo", "No Remunerativo", "Retención", "Redondeo"]
                    df_det = df_liq[df_liq["tipo_concepto"].isin(tipos_validos)].copy()
                    df_det["importe_real"] = df_det.apply(
                        lambda r: -abs(r["importe"]) if r["tipo_concepto"] == "Retención" else abs(r["importe"]), axis=1)
                    df_vista = df_det[["descripcion", "cantidad", "importe_real"]].copy()
                    df_vista.columns = ["Concepto", "Cantidad", "Importe ($)"]
                    df_vista["Importe ($)"] = df_vista["Importe ($)"].apply(fmt_moneda)
                    st.dataframe(df_vista.sort_values("Concepto"), use_container_width=True, hide_index=True)
                    neto = df_liq["neto"].iloc[0] if "neto" in df_liq.columns and df_liq["neto"].iloc[0] else df_det["importe_real"].sum()
                    st.markdown(f'<div class="neto-box"><div class="neto-label">NETO A COBRAR</div>$ {fmt_moneda(neto)}</div>', unsafe_allow_html=True)

        with tab_pre:
            prestamos = consultas.obtener_prestamos_asociado(cuil)
            if not prestamos:
                st.info("No registrás préstamos activos.")
            else:
                for p in prestamos:
                    st.markdown(f'<div class="card"><b>Préstamo otorgado el {p["fecha_otorgamiento"]}</b><br>Monto total: <b>$ {fmt_moneda(p["monto_total"])}</b> | Cuotas: <b>{p["cantidad_cuotas"]}</b></div>', unsafe_allow_html=True)
                    cuotas = p.get("prestamos_cuotas", [])
                    if cuotas:
                        df_c = pd.DataFrame(cuotas)[["numero_cuota", "monto_cuota", "fecha_vencimiento", "estado"]]
                        df_c.columns = ["Cuota N°", "Monto ($)", "Vencimiento", "Estado"]
                        df_c["Monto ($)"] = df_c["Monto ($)"].apply(fmt_moneda)
                        st.dataframe(df_c, use_container_width=True, hide_index=True)

        with tab_san:
            sanciones = consultas.obtener_sanciones_asociado(cuil)
            if not sanciones:
                st.info("No registrás sanciones.")
            else:
                for s in sanciones:
                    color = "#ef4444" if s["tipo"] == "Suspensión" else "#f59e0b"
                    st.markdown(f'<div class="card"><span style="color:{color};font-weight:700">⚠️ {s["tipo"]}</span><br><b>Período:</b> {s["fecha_desde"]} al {s["fecha_hasta"]}<br><b>Motivo:</b> {s["motivo"]}</div>', unsafe_allow_html=True)

        with tab_med:
            historial = consultas.obtener_historial_medico(cuil)
            if not historial:
                st.info("No registrás ausencias médicas.")
            else:
                df_h = pd.DataFrame(historial)[["fecha", "motivo"]]
                df_h.columns = ["Fecha", "Motivo"]
                st.dataframe(df_h, use_container_width=True, hide_index=True)

        with tab_cuenta:
            st.markdown("### Cambiar contraseña")
            with st.form("form_cambiar_pass"):
                nueva = st.text_input("Nueva contraseña", type="password")
                conf = st.text_input("Confirmá la contraseña", type="password")
                if st.form_submit_button("Actualizar contraseña", use_container_width=True):
                    if not nueva:
                        st.warning("La contraseña no puede estar vacía.")
                    elif nueva != conf:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        consultas.cambiar_clave_asociado(cuil, nueva)
                        st.success("Contraseña actualizada correctamente.")

# ================================================================
# PORTAL ADMIN
# ================================================================
elif st.session_state.portal == "admin":

    if not st.session_state.logged_in:
        st.markdown("""
        <div class="top-bar">
            <div>
                <div class="app-title">⚙️ Panel Administrativo</div>
                <div class="app-sub">Cooperativa Agroindustrial · RRHH</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        col_back, _ = st.columns([1, 8])
        with col_back:
            if st.button("← Volver al inicio"):
                st.session_state.portal = None
                st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        _, col_form, _ = st.columns([1, 2, 1])
        with col_form:
            st.markdown('<div class="card card-red">', unsafe_allow_html=True)
            st.markdown("### 🔐 Acceso Administrativo")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            with st.form("form_login_admin"):
                user_in = st.text_input("Usuario")
                pass_in = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Ingresar", use_container_width=True, type="primary"):
                    if user_in and pass_in:
                        user = consultas.login_usuario(user_in, pass_in)
                        if user and user["rol"] in ("admin", "auxiliar"):
                            st.session_state.logged_in = True
                            st.session_state.rol = user["rol"]
                            st.session_state.username = user["username"]
                            st.rerun()
                        else:
                            st.error("Credenciales incorrectas o sin permiso.")
                    else:
                        st.warning("Completá todos los campos.")
            st.markdown('</div>', unsafe_allow_html=True)

    else:
        rol = st.session_state.rol
        with st.sidebar:
            st.markdown("### ⚙️ Panel de Control")
            st.markdown(f"**{st.session_state.username}** · {rol.upper()}")
            st.divider()
            opciones = ["👤 Asociados", "💰 Préstamos", "⚠️ Sanciones", "🏥 Inasistencias", "📊 Reportes"]
            if rol == "admin":
                opciones += ["👥 Usuarios", "📁 Cargar Excel", "🖨️ Emitir Recibos", "🔧 Configuración"]
            seccion = st.radio("Navegación:", opciones, label_visibility="collapsed")
            st.divider()
            if st.button("Cerrar Sesión", use_container_width=True):
                logout()

        # ---- ASOCIADOS ----
        if seccion == "👤 Asociados":
            st.markdown("# 👤 Gestión de Asociados")
            tab_nuevo, tab_buscar, tab_lista, tab_import = st.tabs(["➕ Nuevo Asociado", "🔍 Buscar / Modificar", "📋 Listado", "📥 Importar Maestro"])

            def _form_asociado(edit, form_key):
                """Renderiza el formulario de asociado. edit={} para nuevo, dict con datos para edición."""
                sectores = consultas.listar_sectores()
                nombres_sectores = [s["nombre"] for s in sectores]
                categorias = consultas.listar_categorias()
                with st.form(form_key):
                    col1, col2 = st.columns(2)
                    with col1:
                        cuil_m     = st.text_input("CUIL *", value=edit.get("cuil", ""))
                        nro_m      = st.text_input("Nro Asociado", value=edit.get("nro_asociado") or "")
                        nombre_m   = st.text_input("Nombre Completo *", value=edit.get("nombre_completo", ""))
                        dni_m      = st.text_input("DNI", value=edit.get("dni") or "")
                        telefono_m = st.text_input("Teléfono", value=edit.get("telefono") or "")
                    with col2:
                        domicilio_m = st.text_input("Domicilio", value=edit.get("domicilio") or "")
                        localidad_m = st.text_input("Localidad", value=edit.get("localidad") or "")
                        provincia_m = st.text_input("Provincia", value=edit.get("provincia") or "")
                        if nombres_sectores:
                            idx_s = nombres_sectores.index(edit["sector"]) if edit.get("sector") in nombres_sectores else 0
                            sector_m = st.selectbox("Sector *", nombres_sectores, index=idx_s)
                        else:
                            sector_m = st.text_input("Sector *", value=edit.get("sector") or "")
                            st.caption("⚠️ No hay sectores cargados. Ingresá en Configuración.")
                        if categorias:
                            cat_actual = edit.get("categoria") or ""
                            opciones_cat = categorias if cat_actual in categorias else ([cat_actual] + categorias if cat_actual else categorias)
                            idx_c = opciones_cat.index(cat_actual) if cat_actual in opciones_cat else 0
                            cat_m = st.selectbox("Categoría", opciones_cat, index=idx_c)
                        else:
                            cat_m = st.text_input("Categoría", value=edit.get("categoria") or "")
                        try:
                            fi_val = datetime.date.fromisoformat(edit["fecha_ingreso"]) if edit.get("fecha_ingreso") else datetime.date.today()
                        except:
                            fi_val = datetime.date.today()
                        fecha_ing_m = st.date_input("Fecha de Ingreso", value=fi_val)
                    saved = st.form_submit_button("💾 Guardar Asociado", use_container_width=True, type="primary")
                if saved:
                    if not cuil_m or not nombre_m:
                        st.error("CUIL y Nombre son obligatorios.")
                    else:
                        consultas.guardar_o_actualizar_asociado({
                            "cuil": cuil_m, "nro_asociado": nro_m or None,
                            "nombre_completo": nombre_m, "dni": dni_m or None,
                            "domicilio": domicilio_m or None, "localidad": localidad_m or None,
                            "provincia": provincia_m or None, "telefono": telefono_m or None,
                            "sector": sector_m or None, "categoria": cat_m or None,
                            "fecha_ingreso": str(fecha_ing_m), "activo": True
                        })
                        st.success(f"✅ Asociado {nombre_m} guardado correctamente.")
                        return True
                return False

            with tab_nuevo:
                if _form_asociado({}, "form_nuevo_asociado"):
                    st.rerun()

            with tab_buscar:
                st.markdown("### 🔍 Buscar por nombre o CUIL")
                filtro = st.text_input("Escribí para filtrar:", placeholder="Nombre o CUIL...", key="buscar_filtro")
                todos_aso = consultas.listar_asociados_activos()
                if filtro:
                    fl = filtro.lower()
                    resultados = [a for a in todos_aso
                                  if fl in (a.get("nombre_completo") or "").lower()
                                  or fl in str(a.get("cuil") or "")]
                else:
                    resultados = todos_aso

                if resultados:
                    st.caption(f"{len(resultados)} asociado(s) encontrado(s){' — mostrando primeros 25' if len(resultados) > 25 else ''}.")
                    for a in resultados[:25]:
                        with st.container():
                            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                            c1.write(f"**{a['nombre_completo']}**")
                            c2.write(a.get("cuil") or "-")
                            c3.write(a.get("sector") or "-")
                            with c4:
                                if st.button("✏️ Editar", key=f"edit_btn_{a['cuil']}"):
                                    aso_full = consultas.buscar_asociado_por_cuil(a["cuil"])
                                    st.session_state.aso_edit = aso_full or a
                                    st.session_state.aso_edit_show = True
                                    st.rerun()
                elif filtro:
                    st.warning("No se encontraron asociados que coincidan.")

                # Formulario de edición inline (aparece abajo al hacer clic en Editar)
                if st.session_state.get("aso_edit_show") and st.session_state.get("aso_edit"):
                    aso_e = st.session_state.aso_edit
                    st.divider()
                    st.markdown(f"### ✏️ Editando: {aso_e.get('nombre_completo', '')}")
                    col_cancel, _ = st.columns([2, 8])
                    with col_cancel:
                        if st.button("✖ Cancelar"):
                            st.session_state.aso_edit = {}
                            st.session_state.aso_edit_show = False
                            st.rerun()
                    if _form_asociado(aso_e, "form_edit_asociado"):
                        st.session_state.aso_edit = {}
                        st.session_state.aso_edit_show = False
                        st.rerun()

            with tab_lista:
                df_aso = consultas.obtener_reporte_asociados()
                if not df_aso.empty:
                    st.dataframe(df_aso, use_container_width=True, hide_index=True)
                    st.download_button("📥 Descargar CSV", df_aso.to_csv(index=False).encode("utf-8"), "asociados.csv", "text/csv")
                else:
                    st.info("No hay asociados cargados todavía.")

            with tab_import:
                st.markdown("### 📥 Importar Maestro de Asociados")
                st.info("Soporta el archivo XLS exportado desde **Onvio** (Legajos) o cualquier Excel/CSV con columnas CUIL y Apellido y Nombre.")
                archivo_m = st.file_uploader("Seleccioná el archivo", type=["xlsx", "xls", "csv"], key="up_maestro")
                sobreescribir = st.checkbox("Sobreescribir datos existentes", value=False, help="Si está tildado, actualiza asociados que ya existen. Si no, solo agrega los nuevos.")
                if archivo_m:
                    if st.button("📤 Importar ahora", type="primary"):
                        import io as _io
                        try:
                            with st.spinner("Importando..."):
                                ext = archivo_m.name.split(".")[-1].lower()
                                contenido = archivo_m.getvalue()
                                if ext == "csv":
                                    df_m = pd.read_csv(_io.BytesIO(contenido), encoding="latin-1")
                                    ok_count, errores = consultas.importar_asociados_desde_df(df_m, sobreescribir)
                                elif ext == "xls":
                                    ok_count, errores = consultas.importar_asociados_desde_df(contenido, sobreescribir)
                                else:
                                    df_m = pd.read_excel(_io.BytesIO(contenido))
                                    ok_count, errores = consultas.importar_asociados_desde_df(df_m, sobreescribir)
                            st.success(f"✅ {ok_count} asociados importados correctamente.")
                            if errores:
                                st.warning(f"⚠️ {len(errores)} filas con error:")
                                for e in errores[:5]:
                                    st.write(f"  - {e}")
                        except Exception as e:
                            st.error(f"Error al procesar el archivo: {e}")
                else:
                    st.caption("Seleccioná un archivo para habilitar el botón de importación.")

        # ---- PRESTAMOS ----
        elif seccion == "💰 Préstamos":
            st.markdown("# 💰 Gestión de Préstamos")
            tab_nuevo, tab_editar, tab_reporte = st.tabs(["➕ Otorgar Préstamo", "✏️ Editar Cuotas", "📋 Reporte"])

            with tab_nuevo:
                listado = consultas.listar_asociados_activos()
                if not listado:
                    st.warning("No hay asociados cargados.")
                else:
                    opts = {f"{a['nombre_completo']} — {a['cuil']}": a["cuil"] for a in listado}
                    cuil_sel = opts[st.selectbox("Asociado:", list(opts.keys()))]
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        monto = st.number_input("Monto Total ($)", min_value=0.0, step=1000.0, format="%.2f")
                    with col2:
                        cant_cuotas = st.number_input("Cantidad de Cuotas", min_value=1, max_value=60, value=6, step=1)
                    with col3:
                        f_otorg = st.date_input("Fecha de Otorgamiento", value=datetime.date.today())
                    if monto > 0 and cant_cuotas > 0:
                        st.info(f"💡 Monto por cuota: **$ {fmt_moneda(round(monto / cant_cuotas, 2))}**")
                        st.markdown("**Fechas de vencimiento:**")
                        fechas = []
                        cols = st.columns(min(int(cant_cuotas), 4))
                        for i in range(int(cant_cuotas)):
                            mes_offset = f_otorg.month + i
                            anio = f_otorg.year + (mes_offset - 1) // 12
                            mes = ((mes_offset - 1) % 12) + 1
                            with cols[i % min(int(cant_cuotas), 4)]:
                                f = st.date_input(f"Cuota {i+1}", value=datetime.date(anio, mes, min(f_otorg.day, 28)), key=f"vto_{i}")
                            fechas.append(str(f))
                        if st.button("✅ Confirmar Préstamo", type="primary"):
                            consultas.registrar_prestamo(cuil_sel, monto, int(cant_cuotas), str(f_otorg), fechas)
                            st.success("Préstamo registrado correctamente.")
                    st.markdown('</div>', unsafe_allow_html=True)

            with tab_editar:
                listado2 = consultas.listar_asociados_activos()
                if listado2:
                    opts2 = {f"{a['nombre_completo']} — {a['cuil']}": a["cuil"] for a in listado2}
                    prestamos = consultas.obtener_prestamos_asociado(opts2[st.selectbox("Asociado:", list(opts2.keys()), key="sel_edit_pre")])
                    if not prestamos:
                        st.info("Este asociado no tiene préstamos.")
                    else:
                        for p in prestamos:
                            st.markdown(f'<div class="card"><b>Préstamo #{p["id"]}</b> — {p["fecha_otorgamiento"]} | $ {fmt_moneda(p["monto_total"])}</div>', unsafe_allow_html=True)
                            for c in p.get("prestamos_cuotas", []):
                                col_n, col_f, col_e, col_b = st.columns([1, 2, 2, 1])
                                with col_n: st.write(f"Cuota {c['numero_cuota']}")
                                with col_f:
                                    try: vto = datetime.date.fromisoformat(c["fecha_vencimiento"])
                                    except: vto = datetime.date.today()
                                    nueva_f = st.date_input("Vto.", value=vto, key=f"f_{c['id']}", label_visibility="collapsed")
                                with col_e:
                                    estados = ["Pendiente", "Descontada", "Pausada"]
                                    nuevo_e = st.selectbox("Estado", estados, index=estados.index(c["estado"]) if c["estado"] in estados else 0, key=f"e_{c['id']}", label_visibility="collapsed")
                                with col_b:
                                    if st.button("💾", key=f"b_{c['id']}"):
                                        consultas.actualizar_cuota(c["id"], str(nueva_f), nuevo_e)
                                        st.success(f"Cuota {c['numero_cuota']} actualizada.")
                                        st.rerun()

            with tab_reporte:
                df_p = consultas.obtener_reporte_prestamos()
                if not df_p.empty:
                    st.dataframe(df_p, use_container_width=True, hide_index=True)
                    st.download_button("📥 CSV", df_p.to_csv(index=False).encode("utf-8"), "prestamos.csv", "text/csv")
                else:
                    st.info("No hay préstamos registrados.")

        # ---- SANCIONES ----
        elif seccion == "⚠️ Sanciones":
            st.markdown("# ⚠️ Gestión de Sanciones")
            tab_nueva, tab_rep = st.tabs(["➕ Registrar Sanción", "📋 Reporte"])
            with tab_nueva:
                listado = consultas.listar_asociados_activos()
                if not listado:
                    st.warning("No hay asociados cargados.")
                else:
                    opts = {f"{a['nombre_completo']} — {a['cuil']}": a["cuil"] for a in listado}
                    cuil_san = opts[st.selectbox("Asociado sancionado:", list(opts.keys()))]
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    tipo = st.selectbox("Tipo de medida:", ["Apercibimiento", "Suspensión"])
                    col1, col2 = st.columns(2)
                    with col1: f_desde = st.date_input("Fecha Desde", value=datetime.date.today())
                    with col2: f_hasta = st.date_input("Fecha Hasta", value=datetime.date.today())
                    motivo = st.text_area("Motivo:", max_chars=300, height=100)
                    if st.button("📝 Registrar Sanción", type="primary"):
                        if not motivo: st.warning("Ingresá el motivo.")
                        else:
                            consultas.registrar_sancion(cuil_san, tipo, str(f_desde), str(f_hasta), motivo)
                            st.success("Sanción registrada correctamente.")
                    st.markdown('</div>', unsafe_allow_html=True)
            with tab_rep:
                df_s = consultas.obtener_reporte_sanciones()
                if not df_s.empty:
                    st.dataframe(df_s, use_container_width=True, hide_index=True)
                    st.download_button("📥 CSV", df_s.to_csv(index=False).encode("utf-8"), "sanciones.csv", "text/csv")
                else:
                    st.info("No hay sanciones registradas.")

        # ---- INASISTENCIAS ----
        elif seccion == "🏥 Inasistencias":
            st.markdown("# 🏥 Inasistencias Médicas")
            tab_nueva, tab_hist = st.tabs(["➕ Registrar Ausencia", "📋 Historial"])
            with tab_nueva:
                listado = consultas.listar_asociados_activos()
                if not listado:
                    st.warning("No hay asociados cargados.")
                else:
                    opts = {f"{a['nombre_completo']} — {a['cuil']}": a["cuil"] for a in listado}
                    cuil_med = opts[st.selectbox("Asociado:", list(opts.keys()))]
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    fecha_m = st.date_input("Fecha de ausencia", value=datetime.date.today())
                    motivo_m = st.text_area("Motivo / Diagnóstico:", max_chars=300, height=100)
                    if st.button("💾 Registrar Ausencia", type="primary"):
                        if not motivo_m: st.warning("Ingresá el motivo.")
                        else:
                            consultas.registrar_ausencia_medica(cuil_med, str(fecha_m), motivo_m)
                            st.success("Ausencia médica registrada.")
                    st.markdown('</div>', unsafe_allow_html=True)
            with tab_hist:
                listado2 = consultas.listar_asociados_activos()
                if listado2:
                    opts2 = {f"{a['nombre_completo']} — {a['cuil']}": a["cuil"] for a in listado2}
                    hist = consultas.obtener_historial_medico(opts2[st.selectbox("Ver historial de:", list(opts2.keys()), key="sel_hist")])
                    if hist:
                        df_h = pd.DataFrame(hist)[["fecha", "motivo"]]
                        df_h.columns = ["Fecha", "Motivo"]
                        st.dataframe(df_h, use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay ausencias registradas para este asociado.")

        # ---- REPORTES ----
        elif seccion == "📊 Reportes":
            st.markdown("# 📊 Reportes")
            op = st.selectbox("Seleccioná el reporte:", ["Padrón de Asociados", "Préstamos y Cuotas", "Sanciones", "Historial Médico"])
            df_rep = {"Padrón de Asociados": consultas.obtener_reporte_asociados, "Préstamos y Cuotas": consultas.obtener_reporte_prestamos, "Sanciones": consultas.obtener_reporte_sanciones, "Historial Médico": consultas.obtener_reporte_historial_medico}[op]()
            if not df_rep.empty:
                st.dataframe(df_rep, use_container_width=True, hide_index=True)
                st.download_button("📥 Descargar CSV", df_rep.to_csv(index=False).encode("utf-8"), f"{op}.csv", "text/csv")
            else:
                st.info("No hay datos todavía.")

        # ---- USUARIOS ----
        elif seccion == "👥 Usuarios" and rol == "admin":
            st.markdown("# 👥 Gestión de Usuarios")
            tab_nuevo, tab_lista, tab_blanqueo = st.tabs(["➕ Crear Usuario", "📋 Usuarios Activos", "🔑 Blanquear Clave"])
            with tab_nuevo:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                with st.form("form_nuevo_user"):
                    nu_user = st.text_input("Nombre de usuario")
                    nu_pass = st.text_input("Contraseña", type="password")
                    nu_rol  = st.selectbox("Rol", ["auxiliar", "admin"])
                    if st.form_submit_button("Crear Usuario", use_container_width=True, type="primary"):
                        if nu_user and nu_pass:
                            ok = consultas.crear_usuario_sistema(nu_user, nu_pass, nu_rol)
                            st.success(f"Usuario '{nu_user}' creado.") if ok else st.error("Ya existe un usuario con ese nombre.")
                        else:
                            st.warning("Completá todos los campos.")
                st.markdown('</div>', unsafe_allow_html=True)
            with tab_lista:
                df_u = consultas.listar_usuarios_sistema()
                st.dataframe(df_u, use_container_width=True, hide_index=True) if not df_u.empty else st.info("No hay usuarios.")
            with tab_blanqueo:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                with st.form("form_blanqueo"):
                    usr_reset = st.text_input("Usuario a resetear")
                    nueva_clave = st.text_input("Nueva clave", type="password")
                    if st.form_submit_button("🔑 Blanquear Clave", use_container_width=True):
                        if usr_reset and nueva_clave:
                            ok = consultas.blanquear_clave(usr_reset, nueva_clave)
                            st.success(f"Clave de '{usr_reset}' actualizada.") if ok else st.error("No se encontró ese usuario.")
                        else:
                            st.warning("Completá todos los campos.")
                st.markdown('</div>', unsafe_allow_html=True)

        # ---- CARGAR EXCEL LIQUIDACIONES ----
        elif seccion == "📁 Cargar Excel" and rol == "admin":
            st.markdown("# 📁 Cargar Liquidaciones")
            st.info("💡 Cada Excel que subás se **acumula** como historial. Nunca se pisa información anterior.")
            archivo = st.file_uploader("Seleccioná el Excel de liquidaciones (exportado de Onvio)", type=["xlsx", "xls"], key="up_liq")
            if archivo:
                try:
                    df_liq = pd.read_excel(archivo)
                    # Detectar período automáticamente desde columna "Liquidación"
                    periodo_auto = ""
                    if "Liquidación" in df_liq.columns:
                        vals = df_liq["Liquidación"].dropna()
                        if not vals.empty:
                            periodo_auto = str(vals.iloc[0]).strip()
                    periodo_txt = st.text_input("Nombre del período", value=periodo_auto,
                        help="Se detectó automáticamente desde el archivo. Podés editarlo si querés.")
                    col_a, col_b = st.columns(2)
                    empleados = df_liq["Apellido y Nombre"].nunique() if "Apellido y Nombre" in df_liq.columns else "?"
                    col_a.metric("Empleados en el archivo", empleados)
                    col_b.metric("Registros (conceptos)", len(df_liq))
                    if periodo_txt:
                        if periodo_txt in consultas.listar_periodos_disponibles():
                            st.warning(f"⚠️ El período **{periodo_txt}** ya fue cargado. Si cargás de nuevo se duplicarán los registros.")
                        if st.button("📤 Cargar Liquidación", type="primary"):
                            cant = consultas.cargar_liquidacion_desde_df(df_liq, periodo_txt)
                            st.success(f"✅ Se cargaron {cant} registros para **{periodo_txt}**.")
                    else:
                        st.warning("Ingresá el nombre del período antes de cargar.")
                except Exception as e:
                    st.error(f"Error al leer el archivo: {e}")
            periodos = consultas.listar_periodos_disponibles()
            if periodos:
                st.markdown("---")
                st.markdown("**Períodos ya cargados:**")
                for p in periodos:
                    st.write(f"• {p}")

        # ---- EMITIR RECIBOS ----
        elif seccion == "🖨️ Emitir Recibos" and rol == "admin":
            st.markdown("# 🖨️ Emisión de Recibos en PDF")
            periodos_disponibles = consultas.listar_periodos_disponibles()
            if not periodos_disponibles:
                st.warning("No hay liquidaciones cargadas todavía. Primero cargá al menos un Excel en 'Cargar Excel'.")
            else:
                st.info("Seleccioná una o más liquidaciones cargadas. Los conceptos se agruparán por empleado en un solo recibo.")
                periodos_sel = st.multiselect(
                    "📋 Liquidaciones a incluir en el recibo:",
                    options=periodos_disponibles,
                    help="Podés seleccionar 1ª y 2ª quincena juntas para el recibo mensual, por ejemplo."
                )
                col1, col2 = st.columns(2)
                with col1: titulo_recibo = st.text_input("Título del recibo", placeholder="JUNIO 2026", help="Nombre que aparecerá en el encabezado del PDF")
                with col2: fecha_em = st.date_input("Fecha de emisión", value=datetime.date.today())
                if periodos_sel and titulo_recibo:
                    if st.button("🖨️ Generar Recibos PDF", type="primary"):
                        try:
                            import recibos as mod_recibos
                            df_r = consultas.obtener_liquidacion_para_recibos(periodos_sel)
                            if df_r.empty:
                                st.error("No se encontraron datos para los períodos seleccionados.")
                            else:
                                with st.spinner("Generando recibos..."):
                                    zip_bytes = mod_recibos.generar_zip(
                                        df_r, titulo_recibo, str(fecha_em),
                                        db_map=consultas.obtener_mapa_nro_asociado()
                                    )
                                nombre_zip = f"Recibos_{titulo_recibo.replace(' ','_')}.zip"
                                st.success(f"✅ Recibos generados correctamente.")
                                st.download_button(
                                    f"📦 Descargar {nombre_zip}",
                                    zip_bytes, nombre_zip, "application/zip",
                                    type="primary"
                                )
                        except Exception as e:
                            st.error(f"Error al generar recibos: {e}")
                elif periodos_sel and not titulo_recibo:
                    st.warning("Ingresá el título del recibo.")

        # ---- CONFIGURACION ----
        elif seccion == "🔧 Configuración" and rol == "admin":
            st.markdown("# 🔧 Configuración")
            st.markdown("### Gestión de Sectores")
            st.info("Los sectores que cargues acá van a aparecer como opciones al crear o modificar un asociado.")
            col1, col2 = st.columns([2, 1])
            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                with st.form("form_sector"):
                    nuevo_sec = st.text_input("Nombre del sector")
                    if st.form_submit_button("➕ Agregar", use_container_width=True):
                        if nuevo_sec:
                            ok = consultas.agregar_sector(nuevo_sec)
                            st.success(f"Sector '{nuevo_sec}' agregado.") if ok else st.error("Ya existe ese sector.")
                            if ok: st.rerun()
                        else:
                            st.warning("Ingresá un nombre.")
                st.markdown('</div>', unsafe_allow_html=True)
            with col1:
                sectores = consultas.listar_sectores()
                if sectores:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    for s in sectores:
                        col_n, col_b = st.columns([4, 1])
                        with col_n: st.write(f"• {s['nombre']}")
                        with col_b:
                            if st.button("🗑️", key=f"del_{s['id']}"):
                                consultas.eliminar_sector(s["id"])
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No hay sectores cargados todavía.")
