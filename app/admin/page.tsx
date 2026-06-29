"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";

interface Session { username: string; rol: string; }
interface Asociado { cuil: string; nro_asociado?: string; nombre_completo: string; dni?: string; domicilio?: string; localidad?: string; provincia?: string; telefono?: string; sector?: string; categoria?: string; fecha_ingreso?: string; activo?: boolean; }
interface Sector { id: number; nombre: string; }
interface Prestamo { id: number; cuil_asociado: string; fecha_otorgamiento: string; monto_total: number; cantidad_cuotas: number; prestamos_cuotas?: Cuota[]; maestro_asociados?: { nombre_completo: string }; }
interface Cuota { id: number; numero_cuota: number; monto_cuota: number; fecha_vencimiento: string; estado: string; }
interface Sancion { id: number; cuil_asociado: string; tipo: string; fecha_desde: string; fecha_hasta: string; motivo: string; maestro_asociados?: { nombre_completo: string }; }
interface AusenciaMedica { id: number; cuil_asociado: string; fecha: string; motivo: string; maestro_asociados?: { nombre_completo: string }; }
interface Usuario { id: number; username: string; rol: string; }

function fmt(v: number) { return v.toLocaleString("es-AR", { minimumFractionDigits: 2 }); }
function parseArgNum(s: unknown): number {
  const str = String(s ?? "").trim();
  if (!str || str === "null" || str === "0") return 0;
  const lastComma = str.lastIndexOf(",");
  const lastDot = str.lastIndexOf(".");
  if (lastComma > lastDot) {
    return parseFloat(str.replace(/\./g, "").replace(",", ".")) || 0;
  }
  return parseFloat(str.replace(/,/g, "")) || 0;
}
function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`bg-white rounded-xl p-5 mb-4 shadow border border-gray-100 ${className}`}>{children}</div>;
}
function Label({ children }: { children: React.ReactNode }) {
  return <label className="block text-sm font-semibold text-gray-600 mb-1">{children}</label>;
}
function Input({ className = "", ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:border-blue-400 ${className}`} {...props} />;
}
function Select({ children, className = "", ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={`w-full px-3 py-2 border border-gray-200 rounded-lg bg-white focus:outline-none focus:border-blue-400 ${className}`} {...props}>{children}</select>;
}
function Btn({ children, variant = "primary", className = "", ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: string }) {
  const base = "px-4 py-2 rounded-lg font-semibold text-sm transition-colors ";
  const v = variant === "primary" ? "bg-blue-500 hover:bg-blue-600 text-white" : variant === "danger" ? "bg-red-500 hover:bg-red-600 text-white" : "bg-gray-100 hover:bg-gray-200 text-gray-700 border border-gray-200";
  return <button className={base + v + " " + className} {...props}>{children}</button>;
}
function Alert({ msg }: { msg: { text: string; ok: boolean } | null }) {
  if (!msg) return null;
  return <div className={`p-3 rounded-lg text-sm mb-4 ${msg.ok ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"}`}>{msg.text}</div>;
}

export default function AdminPage() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(""); const [pass, setPass] = useState("");
  const [loginMsg, setLoginMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [seccion, setSeccion] = useState("asociados");
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null);

  // --- Datos ---
  const [asociados, setAsociados] = useState<Asociado[]>([]);
  const [sectores, setSectores] = useState<Sector[]>([]);
  const [categorias, setCategorias] = useState<string[]>([]);
  const [periodos, setPeriodos] = useState<string[]>([]);

  // --- Asociados ---
  const [asoTab, setAsoTab] = useState("nuevo");
  const [filtro, setFiltro] = useState("");
  const [editAso, setEditAso] = useState<Asociado | null>(null);
  const [asoForm, setAsoForm] = useState<Partial<Asociado>>({});
  const [importFile, setImportFile] = useState<File | null>(null);
  const [sobreescribir, setSobreescribir] = useState(false);
  const [importing, setImporting] = useState(false);

  // --- Préstamos ---
  const [preTab, setPreTab] = useState("nuevo");
  const [preCuil, setPreCuil] = useState("");
  const [preMonto, setPreMonto] = useState(0);
  const [preCuotas, setPreCuotas] = useState(6);
  const [preFecha, setPreFecha] = useState(new Date().toISOString().slice(0, 10));
  const [preFechasVto, setPreFechasVto] = useState<string[]>([]);
  const [prestamos, setPrestamos] = useState<Prestamo[]>([]);
  const [preEditCuil, setPreEditCuil] = useState("");
  const [cuotasEdit, setCuotasEdit] = useState<Record<number, { fecha: string; estado: string }>>({});

  // --- Sanciones ---
  const [sanTab, setSanTab] = useState("nueva");
  const [sanCuil, setSanCuil] = useState("");
  const [sanTipo, setSanTipo] = useState("Apercibimiento");
  const [sanFechaSancion, setSanFechaSancion] = useState(new Date().toISOString().slice(0, 10));
  const [sanDesde, setSanDesde] = useState(new Date().toISOString().slice(0, 10));
  const [sanHasta, setSanHasta] = useState(new Date().toISOString().slice(0, 10));
  const [sanMotivo, setSanMotivo] = useState("");
  const [sanReporte, setSanReporte] = useState<Sancion[]>([]);

  // --- Inasistencias ---
  const [medTab, setMedTab] = useState("nueva");
  const [medCuil, setMedCuil] = useState("");
  const [medFecha, setMedFecha] = useState(new Date().toISOString().slice(0, 10));
  const [medMotivo, setMedMotivo] = useState("");
  const [medHistCuil, setMedHistCuil] = useState("");
  const [medHistorial, setMedHistorial] = useState<AusenciaMedica[]>([]);

  // --- Usuarios ---
  const [uTab, setUTab] = useState("nuevo");
  const [nuUser, setNuUser] = useState(""); const [nuPass, setNuPass] = useState(""); const [nuRol, setNuRol] = useState("auxiliar");
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [blanqUser, setBlanqUser] = useState(""); const [blanqPass, setBlanqPass] = useState("");

  // --- Excel Liquidaciones ---
  const [liqFile, setLiqFile] = useState<File | null>(null);
  const [liqPeriodo, setLiqPeriodo] = useState("");
  const [liqCargando, setLiqCargando] = useState(false);

  // --- Recibos ---
  const [periodosSel, setPeriodosSel] = useState<string[]>([]);
  const [tituloRecibo, setTituloRecibo] = useState("");
  const [fechaEm, setFechaEm] = useState(new Date().toISOString().slice(0, 10));
  const [genRecibos, setGenRecibos] = useState(false);

  // --- Sectores ---
  const [nuSector, setNuSector] = useState("");

  // --- Reportes ---
  const [repFechaDesde, setRepFechaDesde] = useState("");
  const [repFechaHasta, setRepFechaHasta] = useState("");
  const [repCuil, setRepCuil] = useState("");
  const [repSector, setRepSector] = useState("");

  useEffect(() => {
    fetch("/api/auth").then(r => r.json()).then(s => {
      if (s?.rol === "admin" || s?.rol === "auxiliar") setSession(s);
      setLoading(false);
    });
  }, []);

  const loadBase = useCallback(async () => {
    const [a, s, c, p] = await Promise.all([
      fetch("/api/asociados?all=1").then(r => r.json()),
      fetch("/api/sectores").then(r => r.json()),
      fetch("/api/asociados?categorias=1").then(r => r.json()),
      fetch("/api/liquidaciones?list=1").then(r => r.json()),
    ]);
    setAsociados(a); setSectores(s); setCategorias(c); setPeriodos(p);
    if (a.length) { setPreCuil(a[0].cuil); setSanCuil(a[0].cuil); setMedCuil(a[0].cuil); setMedHistCuil(a[0].cuil); setPreEditCuil(a[0].cuil); }
  }, []);

  useEffect(() => { if (session) loadBase(); }, [session, loadBase]);

  useEffect(() => {
    const dates: string[] = [];
    const [y, m, d] = preFecha.split("-").map(Number);
    let year = y, month = m, nextDay: number;
    const lastDay = (yr: number, mo: number) => new Date(yr, mo, 0).getDate();
    if (d < 15) {
      nextDay = 15;
    } else if (d < lastDay(year, month)) {
      nextDay = lastDay(year, month);
    } else {
      month++; if (month > 12) { month = 1; year++; }
      nextDay = 15;
    }
    for (let i = 0; i < preCuotas; i++) {
      dates.push(`${year}-${String(month).padStart(2, "0")}-${String(nextDay).padStart(2, "0")}`);
      if (nextDay === 15) {
        nextDay = lastDay(year, month);
      } else {
        month++; if (month > 12) { month = 1; year++; }
        nextDay = 15;
      }
    }
    setPreFechasVto(dates);
  }, [preCuotas, preFecha]);

  async function login(e: React.FormEvent) {
    e.preventDefault();
    const r = await fetch("/api/auth", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: user, password: pass }) });
    if (!r.ok) { setLoginMsg({ text: "Credenciales incorrectas o sin permiso.", ok: false }); return; }
    const s = await r.json();
    if (!["admin", "auxiliar"].includes(s.rol)) { setLoginMsg({ text: "Sin acceso administrativo.", ok: false }); return; }
    setSession(s);
  }

  async function logout() { await fetch("/api/auth", { method: "DELETE" }); setSession(null); }

  async function guardarAsociado(datos: Partial<Asociado>) {
    const r = await fetch("/api/asociados", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...datos, activo: true }) });
    if (!r.ok) { setMsg({ text: "Error al guardar.", ok: false }); return false; }
    setMsg({ text: "✅ Asociado guardado correctamente.", ok: true });
    loadBase();
    return true;
  }

  async function importarMaestro() {
    if (!importFile) return;
    setImporting(true);
    const fd = new FormData();
    fd.append("file", importFile);
    fd.append("sobreescribir", String(sobreescribir));
    const r = await fetch("/api/import", { method: "POST", body: fd });
    const d = await r.json();
    const colInfo = d.columnas?.length ? ` | Columnas detectadas: ${d.columnas.join(", ")}` : "";
    setMsg({ text: `✅ ${d.ok} asociados importados.${d.errores?.length ? ` (${d.errores.length} errores)` : ""}${colInfo}`, ok: true });
    loadBase();
    setImporting(false);
  }

  async function cargarLiquidacion() {
    if (!liqFile || !liqPeriodo) return;
    setLiqCargando(true);
    const XLSX = await import("xlsx");
    const buf = await liqFile.arrayBuffer();
    const wb = XLSX.read(buf, { type: "array", raw: false });
    const ws = wb.Sheets[wb.SheetNames[0]];
    const rows: Record<string, unknown>[] = XLSX.utils.sheet_to_json(ws, { defval: null, raw: false });
    const filas = rows.map(r => ({
      cuil: String(r["CUIL"] || "").trim(),
      periodo: liqPeriodo,
      nro_legajo: String(r["Nro. de Legajo"] || r["Nro. Legajo"] || "").trim() || null,
      nombre_completo: String(r["Apellido y Nombre"] || "").trim() || null,
      descripcion: String(r["Descripción Concepto"] || "").trim(),
      tipo_concepto: String(r["Tipo de Concepto"] || "").trim(),
      cantidad: parseArgNum(r["Cantidad"]),
      importe: parseArgNum(r["Importe Calc"] ?? r["Importe"]),
      sector: String(r["Sector"] || "").trim() || null,
      categoria: String(r["Categoría"] || "").trim() || null,
      jornal_basico: parseArgNum(r["Jornal / Básico"] ?? r["Jornal/Básico"]),
      neto: parseArgNum(r["NETO"] ?? r["Neto"]),
      haberes_rem: parseArgNum(r["Haberes remunerativos"]),
      haberes_no_rem: parseArgNum(r["Haberes No remunerativos"]),
      retenciones: parseArgNum(r["Retenciones"] ?? r["Total Retenciones"]),
    })).filter(f => f.cuil && f.cuil !== "null");
    await fetch("/api/liquidaciones", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ filas }) });
    const cols = rows.length ? Object.keys(rows[0]).join(", ") : "";
    setMsg({ text: `✅ ${filas.length} registros cargados para ${liqPeriodo}. Columnas: ${cols}`, ok: true });
    setLiqFile(null); setLiqPeriodo("");
    fetch("/api/liquidaciones?list=1").then(r => r.json()).then(setPeriodos);
    setLiqCargando(false);
  }

  async function generarRecibos() {
    if (!periodosSel.length || !tituloRecibo) return;
    setGenRecibos(true);
    const r = await fetch("/api/recibos", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ periodos: periodosSel, titulo: tituloRecibo, fecha: fechaEm }) });
    if (!r.ok) { const d = await r.json().catch(() => ({})); setMsg({ text: `Error al generar recibos: ${d.error || r.status}`, ok: false }); setGenRecibos(false); return; }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `Recibos_${tituloRecibo.replace(/\s+/g, "_")}.zip`; a.click();
    URL.revokeObjectURL(url);
    setGenRecibos(false);
  }

  const filtrados = asociados.filter(a =>
    !filtro || a.nombre_completo.toLowerCase().includes(filtro.toLowerCase()) || a.cuil.includes(filtro)
  ).slice(0, 25);

  const SECCIONES = [
    { id: "asociados", label: "👤 Asociados" },
    { id: "prestamos", label: "💰 Préstamos" },
    { id: "sanciones", label: "⚠️ Sanciones" },
    { id: "inasistencias", label: "🏥 Inasistencias" },
    { id: "reportes", label: "📊 Reportes" },
    ...(session?.rol === "admin" ? [
      { id: "usuarios", label: "👥 Usuarios" },
      { id: "excel", label: "📁 Cargar Excel" },
      { id: "recibos", label: "🖨️ Emitir Recibos" },
      { id: "config", label: "🔧 Configuración" },
    ] : []),
  ];

  if (loading) return <div className="flex items-center justify-center h-screen text-gray-400">Cargando...</div>;

  if (!session) return (
    <div className="min-h-screen bg-[#eef2f7]">
      <div className="bg-gradient-to-r from-[#1e293b] to-[#0f172a] text-white px-8 py-4 rounded-2xl mx-6 mt-6">
        <div className="text-xl font-bold">⚙️ Panel Administrativo</div>
        <div className="text-sm opacity-60">Cooperativa Agroindustrial · RRHH</div>
      </div>
      <button onClick={() => router.push("/")} className="ml-6 mt-4 text-sm text-gray-500 hover:text-gray-700">← Volver al inicio</button>
      <div className="flex justify-center mt-8">
        <div className="bg-white rounded-xl shadow p-8 w-full max-w-sm border-t-4 border-t-red-500">
          <h2 className="text-lg font-bold text-[#1e293b] mb-6">🔐 Acceso Administrativo</h2>
          <Alert msg={loginMsg} />
          <form onSubmit={login} className="space-y-4">
            <div><Label>Usuario</Label><Input value={user} onChange={e => setUser(e.target.value)} /></div>
            <div><Label>Contraseña</Label><Input type="password" value={pass} onChange={e => setPass(e.target.value)} /></div>
            <Btn className="w-full justify-center">Ingresar</Btn>
          </form>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#eef2f7] flex">
      <aside className="w-56 bg-[#1e293b] text-[#e2e8f0] flex flex-col p-4 min-h-screen flex-shrink-0">
        <div className="mb-4">
          <div className="font-bold text-sm">⚙️ Panel de Control</div>
          <div className="text-xs opacity-60">{session.username} · {session.rol.toUpperCase()}</div>
        </div>
        <hr className="border-[#334155] mb-3" />
        <nav className="flex-1 space-y-1">
          {SECCIONES.map(s => (
            <button key={s.id} onClick={() => { setSeccion(s.id); setMsg(null); }}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${seccion === s.id ? "bg-[#334155] text-white" : "hover:bg-[#263447] text-[#e2e8f0]"}`}>
              {s.label}
            </button>
          ))}
        </nav>
        <hr className="border-[#334155] my-3" />
        <button onClick={logout} className="bg-red-500 hover:bg-red-600 text-white py-2 rounded-lg text-sm font-medium w-full">Cerrar Sesión</button>
      </aside>

      <main className="flex-1 p-6 overflow-auto">
        <Alert msg={msg} />

        {/* ===== ASOCIADOS ===== */}
        {seccion === "asociados" && (
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b] mb-4">👤 Gestión de Asociados</h1>
            <div className="flex gap-2 bg-gray-100 p-1 rounded-xl mb-6 border border-gray-200 w-fit">
              {[["nuevo","➕ Nuevo"],["buscar","🔍 Buscar"],["lista","📋 Listado"],["import","📥 Importar"]].map(([id,label]) => (
                <button key={id} onClick={() => { setAsoTab(id); setMsg(null); setEditAso(null); }}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${asoTab === id ? "bg-white text-[#1e293b] shadow" : "text-gray-500"}`}>{label}</button>
              ))}
            </div>

            {asoTab === "nuevo" && (
              <Card>
                <h3 className="font-bold text-[#1e293b] mb-4">Nuevo Asociado</h3>
                <AsoForm sectores={sectores} categorias={categorias} inicial={{}} onSave={async d => { if (await guardarAsociado(d)) setAsoForm({}); }} />
              </Card>
            )}

            {asoTab === "buscar" && (
              <div>
                <div className="mb-4"><Input placeholder="Filtrar por nombre o CUIL..." value={filtro} onChange={e => setFiltro(e.target.value)} /></div>
                <div className="text-xs text-gray-500 mb-2">{filtrados.length} resultado(s)</div>
                <div className="bg-white rounded-xl shadow overflow-hidden mb-4">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-600"><tr><th className="text-left px-4 py-3">Nombre</th><th className="px-4 py-3">CUIL</th><th className="px-4 py-3">Sector</th><th className="px-4 py-3"></th></tr></thead>
                    <tbody>
                      {filtrados.map(a => (
                        <tr key={a.cuil} className="border-t border-gray-100">
                          <td className="px-4 py-2 font-medium">{a.nombre_completo}</td>
                          <td className="px-4 py-2 text-center">{a.cuil}</td>
                          <td className="px-4 py-2 text-center">{a.sector || "-"}</td>
                          <td className="px-4 py-2 text-right">
                            <button onClick={async () => { const r = await fetch(`/api/asociados?cuil=${a.cuil}`); const d = await r.json(); setEditAso(d); }}
                              className="text-blue-500 hover:underline text-xs">✏️ Editar</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {editAso && (
                  <Card>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-bold text-[#1e293b]">✏️ Editando: {editAso.nombre_completo}</h3>
                      <button onClick={() => setEditAso(null)} className="text-gray-400 hover:text-gray-600 text-sm">✖ Cancelar</button>
                    </div>
                    <AsoForm sectores={sectores} categorias={categorias} inicial={editAso} onSave={async d => { if (await guardarAsociado(d)) setEditAso(null); }} />
                  </Card>
                )}
              </div>
            )}

            {asoTab === "lista" && (
              <div>
                <div className="bg-white rounded-xl shadow overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-600"><tr>
                      {["CUIL","Nro","Nombre","DNI","Domicilio","Localidad","Provincia","Teléfono","Sector","Categoría","Ingreso"].map(h => <th key={h} className="text-left px-3 py-3">{h}</th>)}
                    </tr></thead>
                    <tbody>
                      {asociados.map(a => (
                        <tr key={a.cuil} className="border-t border-gray-100 hover:bg-gray-50">
                          <td className="px-3 py-2">{a.cuil}</td>
                          <td className="px-3 py-2">{a.nro_asociado}</td>
                          <td className="px-3 py-2 font-medium">{a.nombre_completo}</td>
                          <td className="px-3 py-2">{(a as Asociado & { dni?: string }).dni}</td>
                          <td className="px-3 py-2">{a.domicilio}</td>
                          <td className="px-3 py-2">{a.localidad}</td>
                          <td className="px-3 py-2">{a.provincia}</td>
                          <td className="px-3 py-2">{a.telefono}</td>
                          <td className="px-3 py-2">{a.sector}</td>
                          <td className="px-3 py-2">{a.categoria}</td>
                          <td className="px-3 py-2">{a.fecha_ingreso}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <button
                  className="mt-3 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium"
                  onClick={() => {
                    const csv = ["CUIL,Nro,Nombre,Sector,Categoría,Ingreso", ...asociados.map(a => `${a.cuil},${a.nro_asociado || ""},${a.nombre_completo},${a.sector || ""},${a.categoria || ""},${a.fecha_ingreso || ""}`)].join("\n");
                    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
                    const el = document.createElement("a"); el.href = url; el.download = "asociados.csv"; el.click();
                  }}>📥 Descargar CSV</button>
              </div>
            )}

            {asoTab === "import" && (
              <div className="space-y-4">
                <Card>
                  <h3 className="font-bold text-[#1e293b] mb-2">📥 Importar Maestro de Asociados</h3>
                  <p className="text-sm text-blue-600 bg-blue-50 p-3 rounded-lg mb-4">Soporta el archivo XLS exportado desde Onvio (Legajos) o cualquier Excel/CSV con columnas CUIL y Apellido y Nombre.</p>
                  <div className="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center hover:border-blue-400 transition-colors mb-4">
                    <input type="file" accept=".xls,.xlsx,.csv" onChange={e => setImportFile(e.target.files?.[0] || null)} className="hidden" id="import-file" />
                    <label htmlFor="import-file" className="cursor-pointer">
                      <div className="text-3xl mb-2">📂</div>
                      <div className="text-sm text-gray-500">{importFile ? importFile.name : "Seleccioná un archivo XLS, XLSX o CSV"}</div>
                    </label>
                  </div>
                  <label className="flex items-center gap-2 text-sm mb-4 cursor-pointer">
                    <input type="checkbox" checked={sobreescribir} onChange={e => setSobreescribir(e.target.checked)} />
                    Sobreescribir datos existentes
                  </label>
                  <Btn onClick={importarMaestro} disabled={!importFile || importing} className="w-full justify-center">
                    {importing ? "Importando..." : "📤 Importar ahora"}
                  </Btn>
                </Card>
                <Card>
                  <h3 className="font-bold text-[#1e293b] mb-2">🔢 Cargar Números de Asociado</h3>
                  <p className="text-sm text-gray-500 mb-4">Actualiza el número de legajo (nro_asociado) de cada asociado usando el archivo asociados.json (CUIL → número).</p>
                  <Btn variant="secondary" onClick={async () => {
                    const r = await fetch("/api/import-nros", { method: "POST" });
                    const d = await r.json();
                    setMsg({ text: `✅ ${d.ok}/${d.total} números actualizados.${d.errores?.length ? ` (${d.errores.length} errores)` : ""}`, ok: true });
                    loadBase();
                  }}>🔢 Cargar Números de Asociado</Btn>
                </Card>
                <Card>
                  <h3 className="font-bold text-[#1e293b] mb-2">👤 Crear Accesos al Portal de Asociados</h3>
                  <p className="text-sm text-gray-500 mb-4">Crea un usuario de acceso para cada asociado del maestro. El usuario es el CUIL y la clave inicial es el número de DNI. Los asociados verán un aviso para cambiarla al ingresar.</p>
                  <Btn variant="secondary" onClick={async () => {
                    const r = await fetch("/api/import-usuarios", { method: "POST" });
                    const d = await r.json();
                    setMsg({ text: `✅ ${d.ok}/${d.total} accesos creados.${d.sinDni ? ` (${d.sinDni} sin DNI cargado)` : ""}${d.errores?.length ? ` (${d.errores.length} errores)` : ""}`, ok: true });
                  }}>👤 Crear Accesos (clave = DNI)</Btn>
                </Card>
              </div>
            )}
          </div>
        )}

        {/* ===== PRÉSTAMOS ===== */}
        {seccion === "prestamos" && (
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b] mb-4">💰 Gestión de Préstamos</h1>
            <div className="flex gap-2 bg-gray-100 p-1 rounded-xl mb-6 border border-gray-200 w-fit">
              {[["nuevo","➕ Otorgar"],["editar","✏️ Editar Cuotas"],["reporte","📋 Reporte"]].map(([id,label]) => (
                <button key={id} onClick={() => setPreTab(id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${preTab === id ? "bg-white text-[#1e293b] shadow" : "text-gray-500"}`}>{label}</button>
              ))}
            </div>

            {preTab === "nuevo" && (
              <Card>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <AsoSearch asociados={asociados} value={preCuil} onChange={setPreCuil} />
                  <div><Label>Fecha de otorgamiento</Label><Input type="date" value={preFecha} onChange={e => setPreFecha(e.target.value)} /></div>
                  <div><Label>Monto Total ($)</Label><Input type="number" value={preMonto} onChange={e => setPreMonto(Number(e.target.value))} /></div>
                  <div><Label>Cantidad de cuotas</Label><Input type="number" min={1} max={60} value={preCuotas} onChange={e => setPreCuotas(Number(e.target.value))} /></div>
                </div>
                {preMonto > 0 && <div className="bg-blue-50 text-blue-700 p-3 rounded-lg text-sm mb-4">💡 Monto por cuota: <b>${fmt(Math.round(preMonto / preCuotas * 100) / 100)}</b></div>}
                <h4 className="font-semibold text-sm mb-2">Fechas de vencimiento:</h4>
                <div className="grid grid-cols-4 gap-2 mb-4">
                  {preFechasVto.map((f, i) => (
                    <div key={i}>
                      <Label>Cuota {i + 1}</Label>
                      <Input type="date" value={f} onChange={e => { const arr = [...preFechasVto]; arr[i] = e.target.value; setPreFechasVto(arr); }} />
                    </div>
                  ))}
                </div>
                <Btn onClick={async () => {
                  await fetch("/api/prestamos", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cuil: preCuil, monto_total: preMonto, cantidad_cuotas: preCuotas, fecha_otorgamiento: preFecha, fechas_vencimientos: preFechasVto }) });
                  setMsg({ text: "Préstamo registrado correctamente.", ok: true });
                }}>✅ Confirmar Préstamo</Btn>
              </Card>
            )}

            {preTab === "editar" && (
              <Card>
                <div className="mb-4">
                  <AsoSearch asociados={asociados} value={preEditCuil} onChange={async cuil => {
                    setPreEditCuil(cuil);
                    const r = await fetch(`/api/prestamos?cuil=${cuil}`);
                    const d = await r.json();
                    setPrestamos(d);
                    const ed: Record<number, { fecha: string; estado: string }> = {};
                    d.forEach((p: Prestamo) => p.prestamos_cuotas?.forEach(c => { ed[c.id!] = { fecha: c.fecha_vencimiento, estado: c.estado }; }));
                    setCuotasEdit(ed);
                  }} label="Asociado" />
                </div>
                {prestamos.map(p => (
                  <div key={p.id} className="border border-gray-200 rounded-xl p-4 mb-4">
                    <div className="font-bold mb-3">Préstamo #{p.id} — {p.fecha_otorgamiento} | ${fmt(p.monto_total)}</div>
                    {(p.prestamos_cuotas || []).map(c => (
                      <div key={c.id} className="grid grid-cols-4 gap-2 items-center mb-2">
                        <span className="text-sm">Cuota {c.numero_cuota}</span>
                        <Input type="date" value={cuotasEdit[c.id!]?.fecha || c.fecha_vencimiento} onChange={e => setCuotasEdit(prev => ({ ...prev, [c.id!]: { ...prev[c.id!], fecha: e.target.value } }))} />
                        <Select value={cuotasEdit[c.id!]?.estado || c.estado} onChange={e => setCuotasEdit(prev => ({ ...prev, [c.id!]: { ...prev[c.id!], estado: e.target.value } }))}>
                          {["Pendiente","Descontada","Pausada"].map(s => <option key={s}>{s}</option>)}
                        </Select>
                        <Btn variant="secondary" onClick={async () => {
                          const ed = cuotasEdit[c.id!];
                          await fetch("/api/prestamos", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: c.id, fecha_vencimiento: ed.fecha, estado: ed.estado }) });
                          setMsg({ text: `Cuota ${c.numero_cuota} actualizada.`, ok: true });
                        }}>💾</Btn>
                      </div>
                    ))}
                  </div>
                ))}
              </Card>
            )}

            {preTab === "reporte" && (
              <div>
                <div className="bg-white rounded-xl shadow overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-600"><tr>{["CUIL","Nombre","Monto Total","Cuota N°","Monto Cuota","Vencimiento","Estado","Otorgamiento"].map(h => <th key={h} className="text-left px-3 py-3">{h}</th>)}</tr></thead>
                    <tbody></tbody>
                  </table>
                </div>
                <Btn variant="secondary" className="mt-3" onClick={async () => {
                  const r = await fetch("/api/prestamos?reporte=1");
                  const d: Prestamo[] = await r.json();
                  const filas: string[] = [];
                  d.forEach(p => (p.prestamos_cuotas || []).forEach(c => filas.push(`${p.cuil_asociado},${p.maestro_asociados?.nombre_completo || ""},${p.monto_total},${c.numero_cuota},${c.monto_cuota},${c.fecha_vencimiento},${c.estado},${p.fecha_otorgamiento}`)));
                  const csv = ["CUIL,Nombre,Monto Total,Cuota N°,Monto Cuota,Vencimiento,Estado,Otorgamiento", ...filas].join("\n");
                  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
                  const a = document.createElement("a"); a.href = url; a.download = "prestamos.csv"; a.click();
                }}>📥 Descargar CSV</Btn>
              </div>
            )}
          </div>
        )}

        {/* ===== SANCIONES ===== */}
        {seccion === "sanciones" && (
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b] mb-4">⚠️ Gestión de Sanciones</h1>
            <div className="flex gap-2 bg-gray-100 p-1 rounded-xl mb-6 border border-gray-200 w-fit">
              {[["nueva","➕ Registrar"],["reporte","📋 Reporte"]].map(([id,label]) => (
                <button key={id} onClick={() => setSanTab(id)} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${sanTab === id ? "bg-white text-[#1e293b] shadow" : "text-gray-500"}`}>{label}</button>
              ))}
            </div>
            {sanTab === "nueva" && (
              <Card>
                <div className="space-y-4">
                  <AsoSearch asociados={asociados} value={sanCuil} onChange={setSanCuil} label="Asociado sancionado" />
                  <div><Label>Tipo de medida</Label>
                    <Select value={sanTipo} onChange={e => setSanTipo(e.target.value)}>
                      {["Apercibimiento","Suspensión"].map(t => <option key={t}>{t}</option>)}
                    </Select>
                  </div>
                  {sanTipo === "Apercibimiento" ? (
                    <div><Label>Fecha de sanción</Label><Input type="date" value={sanFechaSancion} onChange={e => setSanFechaSancion(e.target.value)} /></div>
                  ) : (
                    <div className="grid grid-cols-2 gap-4">
                      <div><Label>Fecha Desde</Label><Input type="date" value={sanDesde} onChange={e => setSanDesde(e.target.value)} /></div>
                      <div><Label>Fecha Hasta</Label><Input type="date" value={sanHasta} onChange={e => setSanHasta(e.target.value)} /></div>
                    </div>
                  )}
                  <div><Label>Motivo</Label><textarea className="w-full px-3 py-2 border border-gray-200 rounded-lg resize-none" rows={3} value={sanMotivo} onChange={e => setSanMotivo(e.target.value)} /></div>
                  <Btn onClick={async () => {
                    if (!sanMotivo) { setMsg({ text: "Ingresá el motivo.", ok: false }); return; }
                    await fetch("/api/sanciones", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cuil: sanCuil, tipo: sanTipo, fecha_desde: sanDesde, fecha_hasta: sanHasta, fecha_sancion: sanFechaSancion, motivo: sanMotivo }) });
                    setMsg({ text: "Sanción registrada correctamente.", ok: true }); setSanMotivo("");
                  }}>📝 Registrar Sanción</Btn>
                </div>
              </Card>
            )}
            {sanTab === "reporte" && (
              <div>
                <Btn variant="secondary" className="mb-3" onClick={async () => {
                  const r = await fetch("/api/sanciones?reporte=1");
                  const d: Sancion[] = await r.json();
                  setSanReporte(d);
                }}>🔄 Cargar reporte</Btn>
                <div className="bg-white rounded-xl shadow overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-600"><tr>{["CUIL","Nombre","Tipo","Fecha","Motivo"].map(h => <th key={h} className="text-left px-3 py-3">{h}</th>)}</tr></thead>
                    <tbody>
                      {sanReporte.map(s => (
                        <tr key={s.id} className="border-t border-gray-100">
                          <td className="px-3 py-2">{s.cuil_asociado}</td>
                          <td className="px-3 py-2">{s.maestro_asociados?.nombre_completo}</td>
                          <td className="px-3 py-2">{s.tipo}</td>
                          <td className="px-3 py-2">{s.tipo === "Suspensión" ? `${s.fecha_desde} → ${s.fecha_hasta}` : s.fecha_desde}</td>
                          <td className="px-3 py-2">{s.motivo}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ===== INASISTENCIAS ===== */}
        {seccion === "inasistencias" && (
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b] mb-4">🏥 Inasistencias Médicas</h1>
            <div className="flex gap-2 bg-gray-100 p-1 rounded-xl mb-6 border border-gray-200 w-fit">
              {[["nueva","➕ Registrar"],["hist","📋 Historial"]].map(([id,label]) => (
                <button key={id} onClick={() => setMedTab(id)} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${medTab === id ? "bg-white text-[#1e293b] shadow" : "text-gray-500"}`}>{label}</button>
              ))}
            </div>
            {medTab === "nueva" && (
              <Card>
                <div className="space-y-4">
                  <AsoSearch asociados={asociados} value={medCuil} onChange={setMedCuil} />
                  <div><Label>Fecha de ausencia</Label><Input type="date" value={medFecha} onChange={e => setMedFecha(e.target.value)} /></div>
                  <div><Label>Motivo / Diagnóstico</Label><textarea className="w-full px-3 py-2 border border-gray-200 rounded-lg resize-none" rows={3} value={medMotivo} onChange={e => setMedMotivo(e.target.value)} /></div>
                  <Btn onClick={async () => {
                    if (!medMotivo) { setMsg({ text: "Ingresá el motivo.", ok: false }); return; }
                    await fetch("/api/medico", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cuil: medCuil, fecha: medFecha, motivo: medMotivo }) });
                    setMsg({ text: "Ausencia médica registrada.", ok: true }); setMedMotivo("");
                  }}>💾 Registrar Ausencia</Btn>
                </div>
              </Card>
            )}
            {medTab === "hist" && (
              <Card>
                <div className="mb-4">
                  <AsoSearch asociados={asociados} value={medHistCuil} onChange={async cuil => {
                    setMedHistCuil(cuil);
                    const r = await fetch(`/api/medico?cuil=${cuil}`);
                    setMedHistorial(await r.json());
                  }} label="Ver historial de" />
                </div>
                <div className="bg-white rounded-xl overflow-hidden border border-gray-100">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-600"><tr><th className="text-left px-4 py-3">Fecha</th><th className="text-left px-4 py-3">Motivo</th></tr></thead>
                    <tbody>
                      {medHistorial.map(h => <tr key={h.id} className="border-t border-gray-100"><td className="px-4 py-2">{h.fecha}</td><td className="px-4 py-2">{h.motivo}</td></tr>)}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </div>
        )}

        {/* ===== REPORTES ===== */}
        {seccion === "reportes" && (
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b] mb-4">📊 Reportes</h1>
            <Card>
              <h3 className="font-bold text-sm mb-3">Filtros</h3>
              <div className="grid grid-cols-2 gap-4 mb-3">
                <div><Label>Fecha Desde</Label><Input type="date" value={repFechaDesde} onChange={e => setRepFechaDesde(e.target.value)} /></div>
                <div><Label>Fecha Hasta</Label><Input type="date" value={repFechaHasta} onChange={e => setRepFechaHasta(e.target.value)} /></div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div><Label>Sector</Label>
                  <Select value={repSector} onChange={e => setRepSector(e.target.value)}>
                    <option value="">Todos los sectores</option>
                    {sectores.map(s => <option key={s.id} value={s.nombre}>{s.nombre}</option>)}
                  </Select>
                </div>
                <div><Label>Asociado</Label>
                  <Select value={repCuil} onChange={e => setRepCuil(e.target.value)}>
                    <option value="">Todos</option>
                    {(repSector ? asociados.filter(a => a.sector === repSector) : asociados).map(a => <option key={a.cuil} value={a.cuil}>{a.nombre_completo}</option>)}
                  </Select>
                </div>
              </div>
            </Card>
            <div className="grid grid-cols-2 gap-4">
              {[
                { label: "Padrón de Asociados", url: "/api/asociados?reporte=1", file: "asociados", fechaField: null, cuilField: "cuil" },
                { label: "Sanciones", url: "/api/sanciones?reporte=1", file: "sanciones", fechaField: "fecha_desde", cuilField: "cuil_asociado" },
                { label: "Historial Médico", url: "/api/medico?reporte=1", file: "historial", fechaField: "fecha", cuilField: "cuil_asociado" },
                { label: "Préstamos", url: "/api/prestamos?reporte=1", file: "prestamos", fechaField: "fecha_otorgamiento", cuilField: "cuil_asociado" },
              ].map(rep => (
                <Card key={rep.label} className="flex items-center justify-between">
                  <span className="font-medium">{rep.label}</span>
                  <div className="flex gap-2">
                    {[{ ext: "csv", icon: "📥" }, { ext: "xlsx", icon: "📊" }].map(({ ext, icon }) => (
                      <Btn key={ext} variant="secondary" onClick={async () => {
                        const r = await fetch(rep.url);
                        let d: Record<string, unknown>[] = await r.json();
                        if (rep.fechaField && repFechaDesde) d = d.filter(row => String(row[rep.fechaField!] || "") >= repFechaDesde);
                        if (rep.fechaField && repFechaHasta) d = d.filter(row => String(row[rep.fechaField!] || "") <= repFechaHasta);
                        if (repSector) d = d.filter(row => row["sector"] === repSector || row["maestro_asociados"] === undefined);
                        if (repCuil && rep.cuilField) d = d.filter(row => row[rep.cuilField!] === repCuil);
                        if (!d.length) { setMsg({ text: "Sin datos con esos filtros.", ok: false }); return; }
                        if (ext === "csv") {
                          const keys = Object.keys(d[0]);
                          const csv = [keys.join(","), ...d.map(row => keys.map(k => `"${String(row[k] || "").replace(/"/g, '""')}"`).join(","))].join("\n");
                          const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
                          const a = document.createElement("a"); a.href = url; a.download = `${rep.file}.csv`; a.click();
                        } else {
                          const XLSX = await import("xlsx");
                          const ws = XLSX.utils.json_to_sheet(d);
                          const wb = XLSX.utils.book_new();
                          XLSX.utils.book_append_sheet(wb, ws, rep.label);
                          XLSX.writeFile(wb, `${rep.file}.xlsx`);
                        }
                      }}>{icon} {ext.toUpperCase()}</Btn>
                    ))}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* ===== USUARIOS ===== */}
        {seccion === "usuarios" && session.rol === "admin" && (
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b] mb-4">👥 Gestión de Usuarios</h1>
            <div className="flex gap-2 bg-gray-100 p-1 rounded-xl mb-6 border border-gray-200 w-fit">
              {[["nuevo","➕ Crear"],["lista","📋 Listado"],["blanqueo","🔑 Blanquear Clave"]].map(([id,label]) => (
                <button key={id} onClick={() => setUTab(id)} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${uTab === id ? "bg-white text-[#1e293b] shadow" : "text-gray-500"}`}>{label}</button>
              ))}
            </div>
            {uTab === "nuevo" && (
              <Card className="max-w-sm">
                <div className="space-y-4">
                  <div><Label>Usuario</Label><Input value={nuUser} onChange={e => setNuUser(e.target.value)} /></div>
                  <div><Label>Contraseña</Label><Input type="password" value={nuPass} onChange={e => setNuPass(e.target.value)} /></div>
                  <div><Label>Rol</Label>
                    <Select value={nuRol} onChange={e => setNuRol(e.target.value)}>
                      <option>auxiliar</option><option>admin</option>
                    </Select>
                  </div>
                  <Btn onClick={async () => {
                    if (!nuUser || !nuPass) { setMsg({ text: "Completá todos los campos.", ok: false }); return; }
                    const r = await fetch("/api/usuarios", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: nuUser, password: nuPass, rol: nuRol }) });
                    const d = await r.json();
                    setMsg({ text: d.error || `Usuario '${nuUser}' creado.`, ok: !d.error });
                    if (!d.error) { setNuUser(""); setNuPass(""); fetch("/api/usuarios").then(r => r.json()).then(setUsuarios); }
                  }}>Crear Usuario</Btn>
                </div>
              </Card>
            )}
            {uTab === "lista" && (
              <div>
                <Btn variant="secondary" className="mb-3" onClick={() => fetch("/api/usuarios").then(r => r.json()).then(setUsuarios)}>🔄 Cargar lista</Btn>
                <div className="bg-white rounded-xl shadow overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-600"><tr><th className="text-left px-4 py-3">Usuario</th><th className="text-left px-4 py-3">Rol</th></tr></thead>
                    <tbody>{usuarios.map(u => <tr key={u.id} className="border-t border-gray-100"><td className="px-4 py-2 font-medium">{u.username}</td><td className="px-4 py-2"><span className={`px-2 py-0.5 rounded text-xs ${u.rol === "admin" ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-600"}`}>{u.rol}</span></td></tr>)}</tbody>
                  </table>
                </div>
              </div>
            )}
            {uTab === "blanqueo" && (
              <Card className="max-w-sm">
                <div className="space-y-4">
                  <div><Label>Usuario a resetear</Label><Input value={blanqUser} onChange={e => setBlanqUser(e.target.value)} /></div>
                  <div><Label>Nueva clave</Label><Input type="password" value={blanqPass} onChange={e => setBlanqPass(e.target.value)} /></div>
                  <Btn onClick={async () => {
                    const r = await fetch("/api/usuarios", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: blanqUser, password: blanqPass }) });
                    const d = await r.json();
                    setMsg({ text: d.error || `Clave de '${blanqUser}' actualizada.`, ok: !d.error });
                    setBlanqUser(""); setBlanqPass("");
                  }}>🔑 Blanquear Clave</Btn>
                </div>
              </Card>
            )}
          </div>
        )}

        {/* ===== CARGAR EXCEL ===== */}
        {seccion === "excel" && session.rol === "admin" && (
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b] mb-4">📁 Cargar Liquidaciones</h1>
            <p className="text-sm text-blue-600 bg-blue-50 p-3 rounded-lg mb-4">💡 Cada Excel que subás se acumula como historial. Nunca se pisa información anterior.</p>
            <Card>
              <div className="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center hover:border-blue-400 transition-colors mb-4">
                <input type="file" accept=".xls,.xlsx" onChange={e => setLiqFile(e.target.files?.[0] || null)} className="hidden" id="liq-file" />
                <label htmlFor="liq-file" className="cursor-pointer">
                  <div className="text-3xl mb-2">📊</div>
                  <div className="text-sm text-gray-500">{liqFile ? liqFile.name : "Seleccioná el Excel de liquidaciones (exportado de Onvio)"}</div>
                </label>
              </div>
              <div className="mb-4"><Label>Nombre del período</Label><Input value={liqPeriodo} onChange={e => setLiqPeriodo(e.target.value)} placeholder="Ej: JUNIO 2026 - 1RA QUINCENA" /></div>
              {liqPeriodo && periodos.includes(liqPeriodo) && <p className="text-amber-600 text-sm bg-amber-50 p-3 rounded-lg mb-4">⚠️ El período <b>{liqPeriodo}</b> ya fue cargado. Si cargás de nuevo se duplicarán los registros.</p>}
              <Btn onClick={cargarLiquidacion} disabled={!liqFile || !liqPeriodo || liqCargando}>{liqCargando ? "Cargando..." : "📤 Cargar Liquidación"}</Btn>
            </Card>
            {periodos.length > 0 && (
              <Card>
                <h3 className="font-bold mb-3">Períodos ya cargados:</h3>
                <ul className="space-y-1">{periodos.map(p => <li key={p} className="text-sm text-gray-600">• {p}</li>)}</ul>
              </Card>
            )}
          </div>
        )}

        {/* ===== RECIBOS ===== */}
        {seccion === "recibos" && session.rol === "admin" && (
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b] mb-4">🖨️ Emisión de Recibos en PDF</h1>
            {!periodos.length ? (
              <Card><p className="text-gray-500">No hay liquidaciones cargadas todavía. Primero cargá al menos un Excel en &apos;Cargar Excel&apos;.</p></Card>
            ) : (
              <Card>
                <p className="text-sm text-blue-600 bg-blue-50 p-3 rounded-lg mb-4">Seleccioná una o más liquidaciones. Los conceptos se agruparán por empleado en un solo recibo.</p>
                <div className="mb-4">
                  <Label>Liquidaciones a incluir</Label>
                  <div className="border border-gray-200 rounded-lg max-h-40 overflow-y-auto p-2 space-y-1">
                    {periodos.map(p => (
                      <label key={p} className="flex items-center gap-2 text-sm cursor-pointer hover:bg-gray-50 px-2 py-1 rounded">
                        <input type="checkbox" checked={periodosSel.includes(p)} onChange={e => setPeriodosSel(prev => e.target.checked ? [...prev, p] : prev.filter(x => x !== p))} />
                        {p}
                      </label>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div><Label>Título del recibo</Label><Input value={tituloRecibo} onChange={e => setTituloRecibo(e.target.value)} placeholder="JUNIO 2026" /></div>
                  <div><Label>Fecha de emisión</Label><Input type="date" value={fechaEm} onChange={e => setFechaEm(e.target.value)} /></div>
                </div>
                <Btn onClick={generarRecibos} disabled={!periodosSel.length || !tituloRecibo || genRecibos}>
                  {genRecibos ? "Generando..." : "🖨️ Generar Recibos PDF"}
                </Btn>
              </Card>
            )}
          </div>
        )}

        {/* ===== CONFIG ===== */}
        {seccion === "config" && session.rol === "admin" && (
          <div>
            <h1 className="text-2xl font-bold text-[#1e293b] mb-4">🔧 Configuración</h1>
            <h3 className="font-bold mb-3">Gestión de Sectores</h3>
            <p className="text-sm text-gray-500 mb-4">Los sectores que cargues acá van a aparecer como opciones al crear o modificar un asociado.</p>
            <div className="grid grid-cols-3 gap-6">
              <div className="col-span-2">
                <div className="bg-white rounded-xl shadow overflow-hidden">
                  {sectores.map(s => (
                    <div key={s.id} className="flex items-center justify-between px-4 py-3 border-b border-gray-100 last:border-0">
                      <span className="text-sm">{s.nombre}</span>
                      <button onClick={async () => {
                        await fetch("/api/sectores", { method: "DELETE", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: s.id }) });
                        loadBase();
                      }} className="text-red-400 hover:text-red-600 text-xs">🗑️</button>
                    </div>
                  ))}
                  {!sectores.length && <div className="px-4 py-6 text-center text-gray-400 text-sm">No hay sectores cargados.</div>}
                </div>
              </div>
              <Card>
                <Label>Nombre del sector</Label>
                <Input value={nuSector} onChange={e => setNuSector(e.target.value)} className="mb-3" />
                <Btn onClick={async () => {
                  if (!nuSector) return;
                  const r = await fetch("/api/sectores", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nombre: nuSector }) });
                  const d = await r.json();
                  setMsg({ text: d.error || `Sector '${nuSector}' agregado.`, ok: !d.error });
                  if (!d.error) { setNuSector(""); loadBase(); }
                }}>➕ Agregar</Btn>
              </Card>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function AsoSearch({ asociados, value, onChange, label = "Asociado" }: {
  asociados: Asociado[];
  value: string;
  onChange: (cuil: string) => void;
  label?: string;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const selected = asociados.find(a => a.cuil === value);
  const results = q.trim()
    ? asociados.filter(a =>
        a.nombre_completo.toLowerCase().includes(q.toLowerCase()) ||
        a.cuil.includes(q)
      ).slice(0, 15)
    : [];

  return (
    <div className="relative">
      <Label>{label}</Label>
      <div className="flex gap-2">
        <Input
          placeholder="Buscar por nombre o CUIL..."
          value={open ? q : (selected ? `${selected.nombre_completo} — ${selected.cuil}` : "")}
          onFocus={() => { setOpen(true); setQ(""); }}
          onChange={e => setQ(e.target.value)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
        />
      </div>
      {open && results.length > 0 && (
        <div className="absolute z-50 left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg max-h-56 overflow-y-auto mt-1">
          {results.map(a => (
            <button
              key={a.cuil}
              type="button"
              className="w-full text-left px-3 py-2 text-sm hover:bg-blue-50 border-b border-gray-100 last:border-0"
              onMouseDown={() => { onChange(a.cuil); setOpen(false); setQ(""); }}
            >
              <span className="font-medium">{a.nombre_completo}</span>
              <span className="text-gray-400 ml-2 text-xs">{a.cuil}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function AsoForm({ sectores, categorias, inicial, onSave }: {
  sectores: Sector[];
  categorias: string[];
  inicial: Partial<Asociado>;
  onSave: (datos: Partial<Asociado>) => Promise<void>;
}) {
  const [form, setForm] = useState<Partial<Asociado>>(inicial);
  const f = (k: keyof Asociado) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setForm(prev => ({ ...prev, [k]: e.target.value }));

  return (
    <div className="grid grid-cols-2 gap-4">
      <div><Label>CUIL *</Label><Input value={form.cuil || ""} onChange={f("cuil")} /></div>
      <div><Label>Nro Asociado</Label><Input value={form.nro_asociado || ""} onChange={f("nro_asociado")} /></div>
      <div><Label>Nombre Completo *</Label><Input value={form.nombre_completo || ""} onChange={f("nombre_completo")} /></div>
      <div><Label>DNI</Label><Input value={form.dni || ""} onChange={f("dni")} /></div>
      <div><Label>Teléfono</Label><Input value={form.telefono || ""} onChange={f("telefono")} /></div>
      <div><Label>Domicilio</Label><Input value={form.domicilio || ""} onChange={f("domicilio")} /></div>
      <div><Label>Localidad</Label><Input value={form.localidad || ""} onChange={f("localidad")} /></div>
      <div><Label>Provincia</Label><Input value={form.provincia || ""} onChange={f("provincia")} /></div>
      <div><Label>Sector</Label>
        {sectores.length ? (
          <select className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-white" value={form.sector || ""} onChange={f("sector")}>
            <option value="">-- Seleccioná --</option>
            {sectores.map(s => <option key={s.id} value={s.nombre}>{s.nombre}</option>)}
          </select>
        ) : <Input value={form.sector || ""} onChange={f("sector")} />}
      </div>
      <div><Label>Categoría</Label>
        {categorias.length ? (
          <select className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-white" value={form.categoria || ""} onChange={f("categoria")}>
            <option value="">-- Seleccioná --</option>
            {categorias.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        ) : <Input value={form.categoria || ""} onChange={f("categoria")} />}
      </div>
      <div><Label>Fecha de Ingreso</Label><Input type="date" value={form.fecha_ingreso || ""} onChange={f("fecha_ingreso")} /></div>
      <div className="col-span-2">
        <button
          className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-lg font-semibold transition-colors"
          onClick={() => { if (!form.cuil || !form.nombre_completo) return; onSave(form); }}
        >💾 Guardar Asociado</button>
      </div>
    </div>
  );
}
