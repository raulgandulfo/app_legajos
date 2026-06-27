"use client";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();
  return (
    <div className="min-h-screen bg-[#eef2f7] flex flex-col">
      <div className="bg-gradient-to-r from-[#1e293b] to-[#0f172a] text-white px-8 py-4 rounded-2xl mx-6 mt-6 flex items-center gap-4">
        <div>
          <div className="text-xl font-bold">🏢 Sistema de Gestión de Personal</div>
          <div className="text-sm opacity-60">Cooperativa Agroindustrial · RRHH</div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center">
        <div className="grid grid-cols-2 gap-8 max-w-2xl w-full px-6">
          <div
            className="bg-white rounded-2xl p-10 text-center shadow-lg border border-gray-100 border-t-4 border-t-blue-500 cursor-pointer hover:-translate-y-1 hover:shadow-xl transition-all"
            onClick={() => router.push("/asociado")}
          >
            <div className="text-5xl mb-4">👤</div>
            <div className="text-lg font-bold text-[#1e293b]">SOY ASOCIADO</div>
            <div className="text-sm text-gray-500 mt-1">Consultá tus recibos, préstamos, sanciones e historial médico</div>
            <button
              className="mt-6 w-full bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 rounded-lg transition-colors"
              onClick={(e) => { e.stopPropagation(); router.push("/asociado"); }}
            >
              Ingresar como Asociado
            </button>
          </div>

          <div
            className="bg-white rounded-2xl p-10 text-center shadow-lg border border-gray-100 border-t-4 border-t-red-500 cursor-pointer hover:-translate-y-1 hover:shadow-xl transition-all"
            onClick={() => router.push("/admin")}
          >
            <div className="text-5xl mb-4">⚙️</div>
            <div className="text-lg font-bold text-[#1e293b]">ADMINISTRACIÓN</div>
            <div className="text-sm text-gray-500 mt-1">Panel de gestión para el equipo de Recursos Humanos</div>
            <button
              className="mt-6 w-full bg-gray-100 hover:bg-gray-200 text-[#374151] font-semibold py-2 rounded-lg transition-colors border border-gray-200"
              onClick={(e) => { e.stopPropagation(); router.push("/admin"); }}
            >
              Ingresar como Administración
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
