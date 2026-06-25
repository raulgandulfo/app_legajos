# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import datetime
import consultas

# ================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS
# ================================================================
st.set_page_config(
    page_title="Sistema RRHH",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Fondo general */
    .stApp { background-color: #f5f7fa; }

    /* Oculta el menú de hamburguesa y footer de Streamlit */
    #MainMenu, footer { visibility: hidden; }

    /* Botones principales grandes */
    .btn-portal {
        background-color: #1a1a2e;
        color: white;
        padding: 2rem;
        border-radius: 12px;
        text-align: center;
        cursor: pointer;
        transition: background 0.2s;
        margin: 0.5rem;
    }
    .btn-portal:hover { background-color: #16213e; }

    /* Tarjetas de información */
    .card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    /* Encabezado de sección */
    .seccion-titulo {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 1rem;
    }

    /* Badge de estado de cuota */
    .badge-pendiente { color: #f59e0b; font-weight: 600; }
    .badge-descontada { color: #10b981; font-weight: 600; }
    .badge-pausada { color: #ef4444; font-weight: 600; }

    /* Métrica neto */
    .neto-box {
        background: #1a1a2e;
        color: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        font-size: 1.8rem;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ================================================================
# ESTADO DE SESIÓN
# Streamlit recarga la página con cada interacción, así que
# usamos st.session_state para "recordar" quién está logueado.
# ================================================================
for k, v in [
    ("logged_in", False),
    ("rol", None),
    ("username", None),
    ("cuil", None),
    ("portal", None),   # 'asociado' o 'admin'
]:
    if k not in st.session_state:
        st.session_state[k] = v


def logout():
    """Limpia toda la sesión y vuelve al inicio."""
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()


def fmt_moneda(v):
    """Formatea un número como moneda argentina: 1234567.8 → 1.234.567,80"""
    try:
        return f"{float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00"


# ================================================================
# PANTALLA 0 — SELECCIÓN DE PORTAL
# ================================================================
if st.session_state.portal is None:

    st.markdown("<br><br>", unsafe_allow_html=True)
    col_logo, col_titulo = st.columns([1, 4])
    with col_titulo:
        st.markdown("# 🏢 Sistema de Gestión de Personal")
        st.markdown("#### Seleccioná tu acceso para continuar")
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.markdown("""
        <div class="card" style="text-align:center; padding:2rem;">
            <div style="font-size:3rem;">👤</div>
            <div style="font-size:1.2rem; font-weight:700; margin-top:0.5rem;">SOY ASOCIADO</div>
            <div style="color:#666; margin-top:0.5rem;">Consultá tus recibos, préstamos y más</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ingresar como Asociado", use_container_width=True, type="primary"):
            st.session_state.portal = "asociado"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="card" style="text-align:center; padding:2rem;">
            <div style="font-size:3rem;">⚙️</div>
            <div style="font-size:1.2rem; font-weight:700; margin-top:0.5rem;">ADMINISTRACIÓN</div>
            <div style="color:#666; margin-top:0.5rem;">Panel de gestión para RRHH</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Ingresar como Administración", use_container_width=True):
            st.session_state.portal = "admin"
            st.rerun()


# ================================================================
# PORTAL ASOCIADO
# ================================================================
elif st.session_state.portal == "asociado":

    # --- LOGIN ---
    if not st.session_state.logged_in:
        col_back, _ = st.columns([1, 8])
        with col_back:
            if st.button("← Volver"):
                st.session_state.portal = None
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_form, _ = st.columns([1, 2, 1])

        with col_form:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("## 👤 Portal del Asociado")
            tab_login, tab_registro = st.tabs(["🔐 Ya tengo cuenta", "📝 Registrarme por primera vez"])

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
                            if ok:
                                st.success(msg)
                            else:
                                st.error(msg)
            st.markdown('</div>', unsafe_allow_html=True)

    # --- ASOCIADO LOGUEADO ---
    else:
        cuil = st.session_state.cuil
        asociado = consultas.buscar_asociado_por_cuil(cuil)
        nombre = asociado["nombre_completo"] if asociado else cuil

        # Sidebar
        with st.sidebar:
            st.markdown(f"### 👤 {nombre}")
            st.markdown(f"CUIL: `{cuil}`")
            st.divider()
            if st.button("Cerrar Sesión", use_container_width=True):
                logout()

        st.markdown(f"# Bienvenido/a, {nombre.split()[0]}")
        st.markdown("<br>", unsafe_allow_html=True)

        tab_rec, tab_pre, tab_san, tab_med, tab_cuenta = st.tabs([
            "📄 Mis Recibos",
            "💰 Mis Préstamos",
            "⚠️ Sanciones",
            "🏥 Historial Médico",
            "🔐 Mi Cuenta"
        ])

        # ---- TAB: MIS RECIBOS ----
        with tab_rec:
            periodos = consultas.obtener_periodos_asociado(cuil)

            if not periodos:
                st.info("Todavía no hay liquidaciones disponibles. El administrador debe cargarlas.")
            else:
                periodo_sel = st.selectbox("📅 Seleccioná el período:", periodos)
                df_liq = consultas.obtener_liquidacion(cuil, periodo_sel)

                if df_liq.empty:
                    st.warning("No se encontraron datos para este período.")
                else:
                    # Info de sector y categoría
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.write(f"**Sector:** {df_liq['sector'].iloc[0]}")
                        st.write(f"**Categoría:** {df_liq['categoria'].iloc[0]}")
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Detalle de conceptos
                    st.markdown("#### Detalle de la Liquidación")
                    tipos_validos = ["Remunerativo", "No Remunerativo", "Retención", "Redondeo"]
                    df_detalle = df_liq[df_liq["tipo_concepto"].isin(tipos_validos)].copy()

                    # Retenciones en negativo para que se vea claro
                    df_detalle["importe_real"] = df_detalle.apply(
                        lambda r: -abs(r["importe"]) if r["tipo_concepto"] == "Retención" else abs(r["importe"]),
                        axis=1
                    )
                    df_detalle = df_detalle.sort_values("descripcion")
                    df_vista = df_detalle[["descripcion", "cantidad", "importe_real"]].copy()
                    df_vista.columns = ["Concepto", "Cantidad", "Importe ($)"]
                    df_vista["Importe ($)"] = df_vista["Importe ($)"].apply(fmt_moneda)
                    st.dataframe(df_vista, use_container_width=True, hide_index=True)

                    # Neto
                    st.markdown("<br>", unsafe_allow_html=True)
                    neto = df_liq["neto"].iloc[0] if "neto" in df_liq.columns and df_liq["neto"].iloc[0] else df_detalle["importe_real"].sum()
                    st.markdown(f'<div class="neto-box">NETO A COBRAR<br>$ {fmt_moneda(neto)}</div>', unsafe_allow_html=True)

        # ---- TAB: PRÉSTAMOS ----
        with tab_pre:
            prestamos = consultas.obtener_prestamos_asociado(cuil)
            if not prestamos:
                st.info("No registrás préstamos activos.")
            else:
                for p in prestamos:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown(f"**Préstamo otorgado el {p['fecha_otorgamiento']}**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Monto total: **$ {fmt_moneda(p['monto_total'])}**")
                    with col2:
                        st.write(f"Cuotas: **{p['cantidad_cuotas']}**")

                    cuotas = p.get("prestamos_cuotas", [])
                    if cuotas:
                        df_c = pd.DataFrame(cuotas)[["numero_cuota", "monto_cuota", "fecha_vencimiento", "estado"]]
                        df_c.columns = ["Cuota N°", "Monto ($)", "Vencimiento", "Estado"]
                        df_c["Monto ($)"] = df_c["Monto ($)"].apply(fmt_moneda)
                        st.dataframe(df_c, use_container_width=True, hide_index=True)
                    st.markdown('</div>', unsafe_allow_html=True)

        # ---- TAB: SANCIONES ----
        with tab_san:
            sanciones = consultas.obtener_sanciones_asociado(cuil)
            if not sanciones:
                st.info("No registrás sanciones.")
            else:
                for s in sanciones:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    color = "#ef4444" if s["tipo"] == "Suspensión" else "#f59e0b"
                    st.markdown(f"<span style='color:{color}; font-weight:700'>⚠️ {s['tipo']}</span>", unsafe_allow_html=True)
                    st.write(f"**Período:** {s['fecha_desde']} al {s['fecha_hasta']}")
                    st.write(f"**Motivo:** {s['motivo']}")
                    st.markdown('</div>', unsafe_allow_html=True)

        # ---- TAB: HISTORIAL MÉDICO ----
        with tab_med:
            historial = consultas.obtener_historial_medico(cuil)
            if not historial:
                st.info("No registrás ausencias médicas.")
            else:
                df_h = pd.DataFrame(historial)[["fecha", "motivo"]]
                df_h.columns = ["Fecha", "Motivo"]
                st.dataframe(df_h, use_container_width=True, hide_index=True)

        # ---- TAB: MI CUENTA ----
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
# PORTAL ADMINISTRACIÓN
# ================================================================
elif st.session_state.portal == "admin":

    # --- LOGIN ADMIN ---
    if not st.session_state.logged_in:
        col_back, _ = st.columns([1, 8])
        with col_back:
            if st.button("← Volver"):
                st.session_state.portal = None
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        _, col_form, _ = st.columns([1, 2, 1])

        with col_form:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("## ⚙️ Acceso Administrativo")
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

    # --- ADMIN/AUXILIAR LOGUEADO ---
    else:
        rol = st.session_state.rol

        with st.sidebar:
            st.markdown(f"### ⚙️ Panel de Control")
            st.markdown(f"**{st.session_state.username}** · {rol.upper()}")
            st.divider()

            # Opciones según rol
            opciones = ["👤 Asociados", "💰 Préstamos", "⚠️ Sanciones", "🏥 Inasistencias", "📊 Reportes"]
            if rol == "admin":
                opciones += ["👥 Usuarios", "📁 Cargar Excel", "🖨️ Emitir Recibos", "🔧 Configuración"]

            seccion = st.radio("Navegación:", opciones, label_visibility="collapsed")
            st.divider()
            if st.button("Cerrar Sesión", use_container_width=True):
                logout()

        # ============================================================
        # SECCIÓN: ASOCIADOS
        # ============================================================
        if seccion == "👤 Asociados":
            st.markdown("# 👤 Gestión de Asociados")

            tab_form, tab_buscar, tab_lista = st.tabs(["➕ Nuevo / Modificar", "🔍 Buscar", "📋 Listado completo"])

            with tab_form:
                # Si venimos de "buscar y editar", pre-cargamos los datos
                edit = st.session_state.get("aso_edit", {})
                sectores = consultas.listar_sectores()
                nombres_sectores = [s["nombre"] for s in sectores]

                st.markdown('<div class="card">', unsafe_allow_html=True)
                with st.form("form_asociado"):
                    col1, col2 = st.columns(2)
                    with col1:
                        cuil_m      = st.text_input("CUIL *", value=edit.get("cuil", ""))
                        nro_m       = st.text_input("Nro Asociado", value=edit.get("nro_asociado") or "")
                        nombre_m    = st.text_input("Nombre Completo *", value=edit.get("nombre_completo", ""))
                        dni_m       = st.text_input("DNI", value=edit.get("dni") or "")
                        telefono_m  = st.text_input("Teléfono", value=edit.get("telefono") or "")
                    with col2:
                        domicilio_m = st.text_input("Domicilio", value=edit.get("domicilio") or "")
                        localidad_m = st.text_input("Localidad", value=edit.get("localidad") or "")
                        provincia_m = st.text_input("Provincia", value=edit.get("provincia") or "")

                        if nombres_sectores:
                            idx = nombres_sectores.index(edit["sector"]) if edit.get("sector") in nombres_sectores else 0
                            sector_m = st.selectbox("Sector *", nombres_sectores, index=idx)
                        else:
                            sector_m = st.text_input("Sector *", value=edit.get("sector") or "")
                            st.caption("⚠️ No hay sectores cargados. Cargalos en Configuración.")

                        cat_m = st.text_input("Categoría", value=edit.get("categoria") or "")
                        try:
                            fi_val = datetime.date.fromisoformat(edit["fecha_ingreso"]) if edit.get("fecha_ingreso") else datetime.date.today()
                        except:
                            fi_val = datetime.date.today()
                        fecha_ing_m = st.date_input("Fecha de Ingreso", value=fi_val)

                    if st.form_submit_button("💾 Guardar Asociado", use_container_width=True, type="primary"):
                        if not cuil_m or not nombre_m:
                            st.error("CUIL y Nombre son obligatorios.")
                        else:
                            consultas.guardar_o_actualizar_asociado({
                                "cuil": cuil_m,
                                "nro_asociado": nro_m or None,
                                "nombre_completo": nombre_m,
                                "dni": dni_m or None,
                                "domicilio": domicilio_m or None,
                                "localidad": localidad_m or None,
                                "provincia": provincia_m or None,
                                "telefono": telefono_m or None,
                                "sector": sector_m or None,
                                "categoria": cat_m or None,
                                "fecha_ingreso": str(fecha_ing_m),
                                "activo": True
                            })
                            st.success(f"✅ Asociado {nombre_m} guardado correctamente.")
                            st.session_state.aso_edit = {}
                st.markdown('</div>', unsafe_allow_html=True)

                if edit:
                    if st.button("✖ Cancelar edición"):
                        st.session_state.aso_edit = {}
                        st.rerun()

            with tab_buscar:
                cuil_b = st.text_input("Ingresá el CUIL a buscar:")
                if cuil_b:
                    aso = consultas.buscar_asociado_por_cuil(cuil_b)
                    if aso:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown(f"### {aso['nombre_completo']}")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**CUIL:** {aso['cuil']}")
                            st.write(f"**DNI:** {aso.get('dni') or '-'}")
                            st.write(f"**Nro Asociado:** {aso.get('nro_asociado') or '-'}")
                        with col2:
                            st.write(f"**Sector:** {aso.get('sector') or '-'}")
                            st.write(f"**Categoría:** {aso.get('categoria') or '-'}")
                            st.write(f"**Ingreso:** {aso.get('fecha_ingreso') or '-'}")
                        with col3:
                            st.write(f"**Domicilio:** {aso.get('domicilio') or '-'}")
                            st.write(f"**Localidad:** {aso.get('localidad') or '-'}")
                            st.write(f"**Teléfono:** {aso.get('telefono') or '-'}")
                        st.markdown('</div>', unsafe_allow_html=True)
                        if st.button("✏️ Editar este asociado"):
                            st.session_state.aso_edit = aso
                            st.rerun()
                    else:
                        st.warning("No se encontró ningún asociado con ese CUIL.")

            with tab_lista:
                df_aso = consultas.obtener_reporte_asociados()
                if not df_aso.empty:
                    st.dataframe(df_aso, use_container_width=True, hide_index=True)
                    csv = df_aso.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Descargar CSV", csv, "asociados.csv", "text/csv")
                else:
                    st.info("No hay asociados cargados todavía.")

        # ============================================================
        # SECCIÓN: PRÉSTAMOS
        # ============================================================
        elif seccion == "💰 Préstamos":
            st.markdown("# 💰 Gestión de Préstamos")
            tab_nuevo, tab_editar, tab_reporte = st.tabs(["➕ Otorgar Préstamo", "✏️ Editar Cuotas", "📋 Reporte"])

            with tab_nuevo:
                listado = consultas.listar_asociados_activos()
                if not listado:
                    st.warning("No hay asociados cargados. Cargalos primero en la sección Asociados.")
                else:
                    opts = {f"{a['nombre_completo']} — {a['cuil']}": a["cuil"] for a in listado}
                    sel = st.selectbox("Asociado:", list(opts.keys()))
                    cuil_sel = opts[sel]

                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        monto = st.number_input("Monto Total ($)", min_value=0.0, step=1000.0, format="%.2f")
                    with col2:
                        cant_cuotas = st.number_input("Cantidad de Cuotas", min_value=1, max_value=60, value=6, step=1)
                    with col3:
                        f_otorg = st.date_input("Fecha de Otorgamiento", value=datetime.date.today())

                    if monto > 0 and cant_cuotas > 0:
                        monto_cuota = round(monto / cant_cuotas, 2)
                        st.info(f"💡 Monto por cuota: **$ {fmt_moneda(monto_cuota)}**")

                        st.markdown("**Fechas de vencimiento** (podés modificarlas):")
                        fechas = []
                        cols = st.columns(min(int(cant_cuotas), 4))
                        for i in range(int(cant_cuotas)):
                            mes_offset = f_otorg.month + i
                            anio = f_otorg.year + (mes_offset - 1) // 12
                            mes = ((mes_offset - 1) % 12) + 1
                            dia = min(f_otorg.day, 28)
                            with cols[i % min(int(cant_cuotas), 4)]:
                                f = st.date_input(f"Cuota {i+1}", value=datetime.date(anio, mes, dia), key=f"vto_{i}")
                            fechas.append(str(f))

                        if st.button("✅ Confirmar Préstamo", type="primary"):
                            consultas.registrar_prestamo(cuil_sel, monto, int(cant_cuotas), str(f_otorg), fechas)
                            st.success("Préstamo registrado correctamente.")
                    st.markdown('</div>', unsafe_allow_html=True)

            with tab_editar:
                listado2 = consultas.listar_asociados_activos()
                if listado2:
                    opts2 = {f"{a['nombre_completo']} — {a['cuil']}": a["cuil"] for a in listado2}
                    sel2 = st.selectbox("Seleccioná un asociado:", list(opts2.keys()), key="sel_edit_pre")
                    cuil_sel2 = opts2[sel2]
                    prestamos = consultas.obtener_prestamos_asociado(cuil_sel2)

                    if not prestamos:
                        st.info("Este asociado no tiene préstamos registrados.")
                    else:
                        for p in prestamos:
                            st.markdown('<div class="card">', unsafe_allow_html=True)
                            st.markdown(f"**Préstamo #{p['id']}** — Otorgado: {p['fecha_otorgamiento']} | Total: $ {fmt_moneda(p['monto_total'])}")
                            for c in p.get("prestamos_cuotas", []):
                                col_n, col_f, col_e, col_b = st.columns([1, 2, 2, 1])
                                with col_n:
                                    st.write(f"Cuota {c['numero_cuota']}")
                                with col_f:
                                    try:
                                        vto = datetime.date.fromisoformat(c["fecha_vencimiento"])
                                    except:
                                        vto = datetime.date.today()
                                    nueva_f = st.date_input("Vto.", value=vto, key=f"f_{c['id']}", label_visibility="collapsed")
                                with col_e:
                                    estados = ["Pendiente", "Descontada", "Pausada"]
                                    nuevo_e = st.selectbox("Estado", estados,
                                        index=estados.index(c["estado"]) if c["estado"] in estados else 0,
                                        key=f"e_{c['id']}", label_visibility="collapsed")
                                with col_b:
                                    if st.button("💾", key=f"b_{c['id']}"):
                                        consultas.actualizar_cuota(c["id"], str(nueva_f), nuevo_e)
                                        st.success(f"Cuota {c['numero_cuota']} actualizada.")
                                        st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)

            with tab_reporte:
                df_p = consultas.obtener_reporte_prestamos()
                if not df_p.empty:
                    st.dataframe(df_p, use_container_width=True, hide_index=True)
                    csv = df_p.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Descargar CSV", csv, "prestamos.csv", "text/csv")
                else:
                    st.info("No hay préstamos registrados.")

        # ============================================================
        # SECCIÓN: SANCIONES
        # ============================================================
        elif seccion == "⚠️ Sanciones":
            st.markdown("# ⚠️ Gestión de Sanciones")
            tab_nueva, tab_rep = st.tabs(["➕ Registrar Sanción", "📋 Reporte"])

            with tab_nueva:
                listado = consultas.listar_asociados_activos()
                if not listado:
                    st.warning("No hay asociados cargados.")
                else:
                    opts = {f"{a['nombre_completo']} — {a['cuil']}": a["cuil"] for a in listado}
                    sel = st.selectbox("Asociado sancionado:", list(opts.keys()))
                    cuil_san = opts[sel]

                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    tipo = st.selectbox("Tipo de medida:", ["Apercibimiento", "Suspensión"])
                    col1, col2 = st.columns(2)
                    with col1:
                        f_desde = st.date_input("Fecha Desde", value=datetime.date.today())
                    with col2:
                        f_hasta = st.date_input("Fecha Hasta", value=datetime.date.today())
                    motivo = st.text_area("Motivo (resumido):", max_chars=300, height=100)

                    if st.button("📝 Registrar Sanción", type="primary"):
                        if not motivo:
                            st.warning("Ingresá el motivo.")
                        else:
                            consultas.registrar_sancion(cuil_san, tipo, str(f_desde), str(f_hasta), motivo)
                            st.success("Sanción registrada correctamente.")
                    st.markdown('</div>', unsafe_allow_html=True)

            with tab_rep:
                df_s = consultas.obtener_reporte_sanciones()
                if not df_s.empty:
                    st.dataframe(df_s, use_container_width=True, hide_index=True)
                    csv = df_s.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Descargar CSV", csv, "sanciones.csv", "text/csv")
                else:
                    st.info("No hay sanciones registradas.")

        # ============================================================
        # SECCIÓN: INASISTENCIAS MÉDICAS
        # ============================================================
        elif seccion == "🏥 Inasistencias":
            st.markdown("# 🏥 Inasistencias Médicas")
            tab_nueva, tab_hist = st.tabs(["➕ Registrar Ausencia", "📋 Historial"])

            with tab_nueva:
                listado = consultas.listar_asociados_activos()
                if not listado:
                    st.warning("No hay asociados cargados.")
                else:
                    opts = {f"{a['nombre_completo']} — {a['cuil']}": a["cuil"] for a in listado}
                    sel = st.selectbox("Asociado:", list(opts.keys()))
                    cuil_med = opts[sel]

                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    fecha_m = st.date_input("Fecha de ausencia", value=datetime.date.today())
                    motivo_m = st.text_area("Motivo / Diagnóstico (resumido):", max_chars=300, height=100)

                    if st.button("💾 Registrar Ausencia", type="primary"):
                        if not motivo_m:
                            st.warning("Ingresá el motivo.")
                        else:
                            consultas.registrar_ausencia_medica(cuil_med, str(fecha_m), motivo_m)
                            st.success("Ausencia médica registrada.")
                    st.markdown('</div>', unsafe_allow_html=True)

            with tab_hist:
                listado2 = consultas.listar_asociados_activos()
                if listado2:
                    opts2 = {f"{a['nombre_completo']} — {a['cuil']}": a["cuil"] for a in listado2}
                    sel2 = st.selectbox("Ver historial de:", list(opts2.keys()), key="sel_hist")
                    hist = consultas.obtener_historial_medico(opts2[sel2])
                    if hist:
                        df_h = pd.DataFrame(hist)[["fecha", "motivo"]]
                        df_h.columns = ["Fecha", "Motivo"]
                        st.dataframe(df_h, use_container_width=True, hide_index=True)
                    else:
                        st.info("No hay ausencias registradas para este asociado.")

        # ============================================================
        # SECCIÓN: REPORTES
        # ============================================================
        elif seccion == "📊 Reportes":
            st.markdown("# 📊 Reportes")
            op = st.selectbox("Seleccioná el reporte:", [
                "Padrón de Asociados", "Préstamos y Cuotas", "Sanciones", "Historial Médico"
            ])
            if op == "Padrón de Asociados":
                df_rep = consultas.obtener_reporte_asociados()
            elif op == "Préstamos y Cuotas":
                df_rep = consultas.obtener_reporte_prestamos()
            elif op == "Sanciones":
                df_rep = consultas.obtener_reporte_sanciones()
            else:
                df_rep = consultas.obtener_reporte_historial_medico()

            if not df_rep.empty:
                st.dataframe(df_rep, use_container_width=True, hide_index=True)
                csv = df_rep.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Descargar CSV", data=csv, file_name=f"{op}.csv", mime="text/csv")
            else:
                st.info("No hay datos en este reporte todavía.")

        # ============================================================
        # SECCIÓN: USUARIOS (solo admin)
        # ============================================================
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
                            if ok:
                                st.success(f"Usuario '{nu_user}' creado con rol '{nu_rol}'.")
                            else:
                                st.error("Ya existe un usuario con ese nombre.")
                        else:
                            st.warning("Completá todos los campos.")
                st.markdown('</div>', unsafe_allow_html=True)

            with tab_lista:
                df_u = consultas.listar_usuarios_sistema()
                if not df_u.empty:
                    st.dataframe(df_u, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay usuarios cargados.")

            with tab_blanqueo:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                with st.form("form_blanqueo"):
                    usr_reset = st.text_input("Usuario a resetear")
                    nueva_clave = st.text_input("Nueva clave", type="password")
                    if st.form_submit_button("🔑 Blanquear Clave", use_container_width=True):
                        if usr_reset and nueva_clave:
                            ok = consultas.blanquear_clave(usr_reset, nueva_clave)
                            if ok:
                                st.success(f"Clave de '{usr_reset}' actualizada.")
                            else:
                                st.error("No se encontró ese usuario.")
                        else:
                            st.warning("Completá todos los campos.")
                st.markdown('</div>', unsafe_allow_html=True)

        # ============================================================
        # SECCIÓN: CARGAR EXCEL (solo admin)
        # ============================================================
        elif seccion == "📁 Cargar Excel" and rol == "admin":
            st.markdown("# 📁 Carga de Archivos Excel")

            tab_liq, tab_maestro = st.tabs(["📊 Liquidaciones", "👤 Importar Maestro de Asociados"])

            with tab_liq:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Subir Excel de Liquidaciones")
                st.info("Cada Excel que subas se **acumula** como historial. Nunca se pisa la información anterior.")

                archivo = st.file_uploader("Seleccioná el archivo Excel", type=["xlsx", "xls"], key="up_liq")
                periodo_txt = st.text_input("Nombre del período", placeholder="QUINCENA 1 - JUNIO 2025")
                st.caption("Este nombre es el que verá el asociado en el selector de períodos.")

                if archivo and periodo_txt:
                    if st.button("📤 Cargar Liquidación", type="primary"):
                        try:
                            df_liq = pd.read_excel(archivo)
                            cant = consultas.cargar_liquidacion_desde_df(df_liq, periodo_txt)
                            st.success(f"✅ Se cargaron {cant} registros para el período **{periodo_txt}**.")
                        except Exception as e:
                            st.error(f"Error al procesar el archivo: {e}")
                elif archivo and not periodo_txt:
                    st.warning("Ingresá el nombre del período antes de cargar.")

                # Muestra los períodos ya cargados
                periodos = consultas.listar_periodos_disponibles()
                if periodos:
                    st.markdown("---")
                    st.markdown("**Períodos ya cargados en el sistema:**")
                    for p in periodos:
                        st.write(f"• {p}")
                st.markdown('</div>', unsafe_allow_html=True)

            with tab_maestro:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("### Importar Asociados desde Excel")
                st.info("""
                El Excel debe tener estas columnas (los nombres pueden variar):
                `cuil`, `nombre_completo`, `dni`, `domicilio`, `localidad`, `provincia`, `telefono`, `sector`, `categoria`, `fecha_ingreso`, `nro_asociado`
                """)
                archivo_m = st.file_uploader("Seleccioná el archivo Excel", type=["xlsx", "xls", "csv"], key="up_maestro")
                sobreescribir = st.checkbox("Sobreescribir datos existentes", value=False)
                st.caption("Si está tildado, pisa los datos de asociados que ya existen. Si no está tildado, solo agrega los nuevos.")

                if archivo_m and st.button("📤 Importar Maestro", type="primary"):
                    try:
                        ext = archivo_m.name.split(".")[-1].lower()
                        df_m = pd.read_csv(archivo_m, encoding="latin-1") if ext == "csv" else pd.read_excel(archivo_m)
                        ok_count, errores = consultas.importar_asociados_desde_df(df_m, sobreescribir)
                        st.success(f"✅ {ok_count} asociados importados correctamente.")
                        if errores:
                            st.warning(f"⚠️ {len(errores)} filas con error: {errores[:3]}")
                    except Exception as e:
                        st.error(f"Error al procesar el archivo: {e}")
                st.markdown('</div>', unsafe_allow_html=True)

        # ============================================================
        # SECCIÓN: EMITIR RECIBOS (solo admin)
        # ============================================================
        elif seccion == "🖨️ Emitir Recibos" and rol == "admin":
            st.markdown("# 🖨️ Emisión de Recibos en PDF")
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.info("Subí el Excel del mes completo (todas las quincenas). Solo se usa para generar los PDFs, no se guarda como historial.")

            archivo_r = st.file_uploader("Seleccioná el Excel para recibos", type=["xlsx", "xls"], key="up_recibos")
            col1, col2 = st.columns(2)
            with col1:
                periodo_r = st.text_input("Período", placeholder="JUNIO 2025")
            with col2:
                fecha_em = st.date_input("Fecha de emisión", value=datetime.date.today())

            if archivo_r and periodo_r:
                if st.button("🖨️ Generar Recibos PDF", type="primary"):
                    try:
                        import recibos as mod_recibos
                        df_r = pd.read_excel(archivo_r)
                        mapa_nro = consultas.obtener_mapa_nro_asociado()
                        archivos_pdf = mod_recibos.generar_pdf(df_r, {}, periodo_r, str(fecha_em), db_map=mapa_nro)
                        st.success(f"✅ Se generaron {len(archivos_pdf)} archivos PDF.")
                        for fpath in archivos_pdf:
                            import os
                            nombre_arch = os.path.basename(fpath)
                            with open(fpath, "rb") as f_pdf:
                                st.download_button(
                                    label=f"📄 Descargar {nombre_arch}",
                                    data=f_pdf.read(),
                                    file_name=nombre_arch,
                                    mime="application/pdf",
                                    key=f"dl_{nombre_arch}"
                                )
                    except Exception as e:
                        st.error(f"Error al generar recibos: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        # ============================================================
        # SECCIÓN: CONFIGURACIÓN (solo admin)
        # ============================================================
        elif seccion == "🔧 Configuración" and rol == "admin":
            st.markdown("# 🔧 Configuración")
            st.markdown("### Gestión de Sectores")
            st.info("Los sectores que cargues acá van a aparecer como opciones al crear o modificar un asociado.")

            col1, col2 = st.columns([2, 1])

            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("**Agregar nuevo sector:**")
                with st.form("form_sector"):
                    nuevo_sec = st.text_input("Nombre del sector")
                    if st.form_submit_button("➕ Agregar", use_container_width=True):
                        if nuevo_sec:
                            ok = consultas.agregar_sector(nuevo_sec)
                            if ok:
                                st.success(f"Sector '{nuevo_sec}' agregado.")
                                st.rerun()
                            else:
                                st.error("Ya existe ese sector.")
                        else:
                            st.warning("Ingresá un nombre.")
                st.markdown('</div>', unsafe_allow_html=True)

            with col1:
                sectores = consultas.listar_sectores()
                if sectores:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("**Sectores actuales:**")
                    for s in sectores:
                        col_n, col_b = st.columns([4, 1])
                        with col_n:
                            st.write(f"• {s['nombre']}")
                        with col_b:
                            if st.button("🗑️", key=f"del_{s['id']}"):
                                consultas.eliminar_sector(s["id"])
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No hay sectores cargados todavía.")
