"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface Session { username: string; rol: string; cuil: string; }
interface LiqRow { descripcion: string; tipo_concepto: string; cantidad: number; importe: number; neto?: number; sector?: string; categoria?: string; jornal_basico?: number; }
interface Prestamo { id: number; fecha_otorgamiento: string; monto_total: number; cantidad_cuotas: number; prestamos_cuotas?: Cuota[]; }
interface Cuota { id: number; numero_cuota: number; monto_cuota: number; fecha_vencimiento: string; estado: string; }
interface Sancion { id: number; tipo: string; fecha_desde: string; fecha_hasta: string; motivo: string; }
interface Ausencia { id: number; fecha: string; motivo: string; }

function fmt(v: number) {
  return v.toLocaleString("es-AR", { minimumFractionDigits: 2 });
}

function Card({ children, color = "blue" }: { children: React.ReactNode; color?: string }) {
  const border = color === "blue" ? "border-t-blue-500" : color === "red" ? "border-t-red-500" : "border-t-green-500";
  return <div className={`bg-white rounded-xl p-5 mb-4 shadow border border-gray-100 border-t-4 ${border}`}>{children}</div>;
}

export default function AsociadoPage() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("login");
  const [cuil, setCuil] = useState(""); const [pass, setPass] = useState("");
  const [regCuil, setRegCuil] = useState(""); const [regPass, setRegPass] = useState(""); const [regPass2, setRegPass2] = useState("");
  const [rstCuil, setRstCuil] = useState(""); const [rstDni, setRstDni] = useState(""); const [rstPass, setRstPass] = useState(""); const [rstPass2, setRstPass2] = useState("");
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [activeTab, setActiveTab] = useState("recibos");
  const [periodos, setPeriodos] = useState<string[]>([]);
  const [periodoSel, setPeriodoSel] = useState("");
  const [liqRows, setLiqRows] = useState<LiqRow[]>([]);
  const [prestamos, setPrestamos] = useState<Prestamo[]>([]);
  const [sanciones, setSanciones] = useState<Sancion[]>([]);
  const [historial, setHistorial] = useState<Ausencia[]>([]);
  const [newPass, setNewPass] = useState(""); const [newPass2, setNewPass2] = useState("");
  const [asociado, setAsociado] = useState<{ nombre_completo?: string } | null>(null);

  useEffect(() => {
    fetch("/api/auth").then(r => r.json()).then(s => {
      if (s?.rol === "asociado") setSession(s);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!session) return;
    fetch(`/api/asociados?cuil=${session.cuil}`).then(r => r.json()).then(setAsociado);
    fetch(`/api/liquidaciones?cuil=${session.cuil}`).then(r => r.json()).then((ps: string[]) => {
      setPeriodos(ps);
      if (ps.length) setPeriodoSel(ps[0]);
    });
    fetch(`/api/prestamos?cuil=${session.cuil}`).then(r => r.json()).then(setPrestamos);
    fetch(`/api/sanciones?cuil=${session.cuil}`).then(r => r.json()).then(setSanciones);
    fetch(`/api/medico?cuil=${session.cuil}`).then(r => r.json()).then(setHistorial);
  }, [session]);

  useEffect(() => {
    if (!session || !periodoSel) return;
    fetch(`/api/liquidaciones?cuil=${session.cuil}&periodo=${encodeURIComponent(periodoSel)}`).then(r => r.json()).then(setLiqRows);
  }, [periodoSel, session]);

  async function login(e: React.FormEvent) {
    e.preventDefault();
    const r = await fetch("/api/auth", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: cuil, password: pass }) });
    if (!r.ok) { setMsg({ text: "CUIL o contraseña incorrectos.", ok: false }); return; }
    const s = await r.json();
    if (s.rol !== "asociado") { setMsg({ text: "No tenés acceso como asociado.", ok: false }); return; }
    setSession(s);
  }

  async function resetClave(e: React.FormEvent) {
    e.preventDefault();
    if (rstPass !== rstPass2) { setMsg({ text: "Las contraseñas no coinciden.", ok: false }); return; }
    const r = await fetch("/api/auth/reset", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cuil: rstCuil, dni: rstDni, password: rstPass }) });
    const d = await r.json();
    setMsg({ text: d.error || "Contraseña actualizada. Ya podés iniciar sesión.", ok: !d.error });
    if (!d.error) { setRstCuil(""); setRstDni(""); setRstPass(""); setRstPass2(""); setTab("login"); }
  }

  async function registro(e: React.FormEvent) {
    e.preventDefault();
    if (regPass !== regPass2) { setMsg({ text: "Las contraseñas no coinciden.", ok: false }); return; }
    const r = await fetch("/api/auth/registro", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cuil: regCuil, password: regPass }) });
    const d = await r.json();
    setMsg({ text: d.error || "Registro exitoso. Ya podés iniciar sesión.", ok: !d.error });
  }

  async function logout() {
    await fetch("/api/auth", { method: "DELETE" });
    setSession(null);
  }

  async function cambiarClave(e: React.FormEvent) {
    e.preventDefault();
    if (newPass !== newPass2) { setMsg({ text: "Las contraseñas no coinciden.", ok: false }); return; }
    await fetch("/api/usuarios", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: session!.cuil, password: newPass }) });
    setMsg({ text: "Contraseña actualizada.", ok: true });
    setNewPass(""); setNewPass2("");
  }

  if (loading) return <div className="flex items-center justify-center h-screen text-gray-400">Cargando...</div>;

  if (!session) {
    return (
      <div className="min-h-screen bg-[#eef2f7]">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#0f172a] text-white px-8 py-4 rounded-2xl mx-6 mt-6">
          <div className="text-xl font-bold">👤 Portal del Asociado</div>
          <div className="text-sm opacity-60">Cooperativa Agroindustrial · RRHH</div>
        </div>
        <button onClick={() => router.push("/")} className="ml-6 mt-4 text-sm text-gray-500 hover:text-gray-700">← Volver al inicio</button>
        <div className="flex justify-center mt-8">
          <div className="bg-white rounded-xl shadow p-8 w-full max-w-md border-t-4 border-t-blue-500">
            <div className="flex gap-1 mb-6">
              {[["login","🔐 Ingresar"],["registro","📝 Registrarme"],["reset","🔑 Olvidé mi clave"]].map(([t, label]) => (
                <button key={t} onClick={() => { setTab(t); setMsg(null); }}
                  className={`flex-1 py-2 rounded-lg text-xs font-medium transition-colors ${tab === t ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-600"}`}>
                  {label}
                </button>
              ))}
            </div>
            {msg && <div className={`p-3 rounded-lg text-sm mb-4 ${msg.ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>{msg.text}</div>}
            {tab === "login" && (
              <form onSubmit={login} className="space-y-4">
                <div><label className="text-sm font-semibold text-gray-600">CUIL (sin guiones)</label>
                  <input className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={cuil} onChange={e => setCuil(e.target.value)} placeholder="20123456789" /></div>
                <div><label className="text-sm font-semibold text-gray-600">Contraseña</label>
                  <input type="password" className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={pass} onChange={e => setPass(e.target.value)} /></div>
                <button className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-lg font-semibold transition-colors">Ingresar</button>
              </form>
            )}
            {tab === "registro" && (
              <form onSubmit={registro} className="space-y-4">
                <p className="text-sm text-blue-600 bg-blue-50 p-3 rounded-lg">Tu CUIL debe haber sido cargado previamente por RRHH.</p>
                <div><label className="text-sm font-semibold text-gray-600">Tu CUIL</label>
                  <input className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={regCuil} onChange={e => setRegCuil(e.target.value)} /></div>
                <div><label className="text-sm font-semibold text-gray-600">Elegí una contraseña</label>
                  <input type="password" className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={regPass} onChange={e => setRegPass(e.target.value)} /></div>
                <div><label className="text-sm font-semibold text-gray-600">Confirmá la contraseña</label>
                  <input type="password" className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={regPass2} onChange={e => setRegPass2(e.target.value)} /></div>
                <button className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-lg font-semibold transition-colors">Crear mi cuenta</button>
              </form>
            )}
            {tab === "reset" && (
              <form onSubmit={resetClave} className="space-y-4">
                <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">Ingresá tu CUIL y tu DNI para verificar tu identidad y establecer una nueva contraseña.</p>
                <div><label className="text-sm font-semibold text-gray-600">Tu CUIL (sin guiones)</label>
                  <input className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={rstCuil} onChange={e => setRstCuil(e.target.value)} placeholder="20123456789" /></div>
                <div><label className="text-sm font-semibold text-gray-600">Tu DNI (sin puntos)</label>
                  <input className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={rstDni} onChange={e => setRstDni(e.target.value)} placeholder="12345678" /></div>
                <div><label className="text-sm font-semibold text-gray-600">Nueva contraseña</label>
                  <input type="password" className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={rstPass} onChange={e => setRstPass(e.target.value)} /></div>
                <div><label className="text-sm font-semibold text-gray-600">Confirmá la nueva contraseña</label>
                  <input type="password" className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={rstPass2} onChange={e => setRstPass2(e.target.value)} /></div>
                <button className="w-full bg-amber-500 hover:bg-amber-600 text-white py-2 rounded-lg font-semibold transition-colors">🔑 Cambiar contraseña</button>
              </form>
            )}
          </div>
        </div>
      </div>
    );
  }

  const nombre = asociado?.nombre_completo || session.cuil;
  const TABS = [
    { id: "recibos", label: "📄 Mis Recibos" },
    { id: "prestamos", label: "💰 Mis Préstamos" },
    { id: "sanciones", label: "⚠️ Sanciones" },
    { id: "medico", label: "🏥 Historial Médico" },
    { id: "cuenta", label: "🔐 Mi Cuenta" },
  ];

  const tiposValidos = ["Remunerativo", "No Remunerativo", "Retención", "Redondeo"];
  const detalle = liqRows.filter(r => tiposValidos.includes(r.tipo_concepto));
  const neto = liqRows[0]?.neto || detalle.reduce((s, r) => s + (r.tipo_concepto === "Retención" ? -Math.abs(r.importe) : r.importe), 0);

  return (
    <div className="min-h-screen bg-[#eef2f7] flex flex-col md:flex-row">
      <aside className="bg-[#1e293b] text-[#e2e8f0] flex flex-row md:flex-col p-3 md:p-4 md:w-64 md:min-h-screen items-center md:items-stretch gap-3 md:gap-0">
        <div className="flex-1 md:mb-6 min-w-0">
          <div className="font-bold text-sm md:text-lg truncate">👤 {nombre}</div>
          <div className="text-xs opacity-60 hidden md:block">CUIL: {session.cuil}</div>
        </div>
        <hr className="hidden md:block border-[#334155] mb-4" />
        <button onClick={logout} className="bg-red-500 hover:bg-red-600 text-white py-1.5 md:py-2 px-3 md:w-full rounded-lg text-xs md:text-sm font-medium md:mt-auto whitespace-nowrap">Cerrar Sesión</button>
      </aside>

      <main className="flex-1 p-3 md:p-6 min-w-0">
        <div className="bg-gradient-to-r from-[#1e293b] to-[#0f172a] text-white px-4 md:px-6 py-3 md:py-4 rounded-xl mb-4">
          <div className="text-base md:text-lg font-bold">Bienvenido/a, {nombre}</div>
          <div className="text-xs md:text-sm opacity-60">Portal del Asociado · CUIL {session.cuil}</div>
        </div>
        <div className="bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-3 rounded-xl mb-4 flex items-center justify-between gap-4">
          <span>🔑 Si es tu primer ingreso, tu clave inicial es tu número de DNI. Te recomendamos cambiarla.</span>
          <button onClick={() => setActiveTab("cuenta")} className="bg-amber-500 hover:bg-amber-600 text-white px-3 py-1 rounded-lg text-xs font-semibold whitespace-nowrap">Cambiar clave</button>
        </div>

        <div className="flex gap-2 bg-gray-100 p-1 rounded-xl mb-6 border border-gray-200 overflow-x-auto">
          {TABS.map(t => (
            <button key={t.id} onClick={() => { setActiveTab(t.id); setMsg(null); }}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${activeTab === t.id ? "bg-white text-[#1e293b] shadow" : "text-gray-500"}`}>
              {t.label}
            </button>
          ))}
        </div>

        {activeTab === "recibos" && (
          <div>
            {!periodos.length ? <Card><p className="text-gray-500">Todavía no hay liquidaciones disponibles.</p></Card> : (
              <>
                <select className="mb-4 px-4 py-2 border border-gray-200 rounded-lg bg-white" value={periodoSel} onChange={e => setPeriodoSel(e.target.value)}>
                  {periodos.map(p => <option key={p}>{p}</option>)}
                </select>
                {liqRows[0] && (
                  <Card>
                    <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
                      <span><span className="font-medium">Sector:</span> {liqRows[0].sector}</span>
                      <span><span className="font-medium">Categoría:</span> {liqRows[0].categoria}</span>
                      {liqRows[0].jornal_basico ? <span><span className="font-medium">Jornal básico:</span> ${fmt(liqRows[0].jornal_basico)}</span> : null}
                    </div>
                  </Card>
                )}
                <h3 className="font-semibold text-[#1e293b] mb-3">Detalle de la Liquidación</h3>
                <div className="overflow-x-auto bg-white rounded-xl shadow mb-4">
                  <table className="w-full text-sm min-w-[360px]">
                    <thead className="bg-gray-50 text-gray-600">
                      <tr><th className="text-left px-4 py-3">Concepto</th><th className="px-3 py-3 text-center">Cant.</th><th className="text-right px-4 py-3">Importe ($)</th></tr>
                    </thead>
                    <tbody>
                      {detalle.map((r, i) => (
                        <tr key={i} className="border-t border-gray-100">
                          <td className="px-4 py-2">{r.descripcion}</td>
                          <td className="px-3 py-2 text-center">{r.cantidad || ""}</td>
                          <td className={`px-4 py-2 text-right ${r.tipo_concepto === "Retención" ? "text-red-500" : ""}`}>
                            {r.tipo_concepto === "Retención" ? `-${fmt(Math.abs(r.importe))}` : fmt(r.importe)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="bg-gradient-to-r from-[#1e293b] to-[#0f172a] text-white rounded-xl p-6 text-center">
                  <div className="text-xs uppercase tracking-widest opacity-60 mb-1">NETO A COBRAR</div>
                  <div className="text-3xl font-bold">$ {fmt(neto)}</div>
                </div>
              </>
            )}
          </div>
        )}

        {activeTab === "prestamos" && (
          <div>
            {!prestamos.length ? <Card><p className="text-gray-500">No registrás préstamos activos.</p></Card> :
              prestamos.map(p => (
                <Card key={p.id}>
                  <div className="font-bold mb-2">Préstamo del {p.fecha_otorgamiento} — $ {fmt(p.monto_total)}</div>
                  <table className="w-full text-sm">
                    <thead className="text-gray-500"><tr><th className="text-left py-1">Cuota</th><th>Monto</th><th>Vencimiento</th><th>Estado</th></tr></thead>
                    <tbody>
                      {(p.prestamos_cuotas || []).map(c => (
                        <tr key={c.id} className="border-t border-gray-100">
                          <td className="py-1">N° {c.numero_cuota}</td>
                          <td className="text-center">$ {fmt(c.monto_cuota)}</td>
                          <td className="text-center">{c.fecha_vencimiento}</td>
                          <td className="text-center"><span className={`px-2 py-0.5 rounded text-xs ${c.estado === "Descontada" ? "bg-green-100 text-green-700" : c.estado === "Pausada" ? "bg-yellow-100 text-yellow-700" : "bg-gray-100 text-gray-600"}`}>{c.estado}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Card>
              ))}
          </div>
        )}

        {activeTab === "sanciones" && (
          <div>
            {!sanciones.length ? <Card><p className="text-gray-500">No registrás sanciones.</p></Card> :
              sanciones.map(s => (
                <Card key={s.id} color={s.tipo === "Suspensión" ? "red" : "blue"}>
                  <div className={`font-bold ${s.tipo === "Suspensión" ? "text-red-500" : "text-amber-500"}`}>⚠️ {s.tipo}</div>
                  <div className="text-sm mt-1"><span className="font-medium">Período:</span> {s.fecha_desde} al {s.fecha_hasta}</div>
                  <div className="text-sm"><span className="font-medium">Motivo:</span> {s.motivo}</div>
                </Card>
              ))}
          </div>
        )}

        {activeTab === "medico" && (
          <div>
            {!historial.length ? <Card><p className="text-gray-500">No registrás ausencias médicas.</p></Card> : (
              <div className="bg-white rounded-xl shadow overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-gray-600"><tr><th className="text-left px-4 py-3">Fecha</th><th className="text-left px-4 py-3">Motivo</th></tr></thead>
                  <tbody>{historial.map(h => (<tr key={h.id} className="border-t border-gray-100"><td className="px-4 py-2">{h.fecha}</td><td className="px-4 py-2">{h.motivo}</td></tr>))}</tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === "cuenta" && (
          <div className="max-w-md">
            <Card>
              <h3 className="font-bold text-[#1e293b] mb-4">Cambiar contraseña</h3>
              {msg && <div className={`p-3 rounded-lg text-sm mb-4 ${msg.ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>{msg.text}</div>}
              <form onSubmit={cambiarClave} className="space-y-4">
                <div><label className="text-sm font-semibold text-gray-600">Nueva contraseña</label>
                  <input type="password" className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={newPass} onChange={e => setNewPass(e.target.value)} /></div>
                <div><label className="text-sm font-semibold text-gray-600">Confirmá la contraseña</label>
                  <input type="password" className="w-full mt-1 px-3 py-2 border border-gray-200 rounded-lg" value={newPass2} onChange={e => setNewPass2(e.target.value)} /></div>
                <button className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-lg font-semibold">Actualizar contraseña</button>
              </form>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
