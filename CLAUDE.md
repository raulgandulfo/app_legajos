# CLAUDE.md — app_legajos

Sistema de gestión de RRHH para una cooperativa agroindustrial argentina.

## Stack
- **Next.js 15** (App Router, TypeScript)
- **Supabase** (PostgreSQL vía PostgREST) — free tier, max 1000 filas por query → usar paginación
- **pdf-lib** para generación de PDFs
- **JSZip** para ZIPs de recibos
- **SheetJS (xlsx)** para exportar/importar Excel
- **Tailwind CSS**
- Deploy en **Vercel**

## Estructura de rutas
- `/admin` — panel administrativo (admins y auxiliares)
- `/asociado` — portal del asociado (login por CUIL)
- `/api/asociados` — CRUD maestro de asociados
- `/api/prestamos` — préstamos y cuotas
- `/api/sanciones` — sanciones disciplinarias
- `/api/capacitaciones` — capacitaciones por asociado
- `/api/medico` — inasistencias médicas (`historial_medico`)
- `/api/liquidaciones` — importación y consulta de liquidaciones
- `/api/recibos` — generación de recibos PDF/ZIP
- `/api/dashboard` — métricas para el panel principal
- `/api/auth` — autenticación por sesión

## Tablas Supabase
- `maestro_asociados` — CUIL (PK), nro_asociado, nro_legajo, nombre_completo, sector, categoria, fecha_ingreso, fecha_salida, activo (bool)
- `liquidaciones` — cuil, periodo, nombre_completo, descripcion, tipo_concepto, importe, sector, categoria, jornal_basico, haberes_rem, haberes_no_rem, retenciones, neto
- `prestamos` — id, cuil_asociado (FK), monto_total, cantidad_cuotas, fecha_otorgamiento
- `prestamos_cuotas` — id, prestamo_id (FK), numero_cuota, monto_cuota, fecha_vencimiento, estado (check: Pendiente/Descontada/Pausada)
- `sanciones` — id, cuil_asociado, tipo, fecha_desde, fecha_hasta, motivo
- `capacitaciones` — id, cuil_asociado, titulo, fecha, duracion_hs, resultado, observaciones
- `historial_medico` — id, cuil_asociado, fecha_desde, fecha_hasta, motivo
- `usuarios` — id, username, password_hash, rol (admin/auxiliar), accesos (array)
- `sectores` — id, nombre

## Convenciones importantes
- Asociados con `fecha_salida` → `activo = false`. Al limpiar `fecha_salida` → `activo = true`. Las fechas vacías se normalizan a `null` en la API antes de hacer upsert.
- Las liquidaciones tienen filas por concepto: los campos `neto`, `haberes_rem`, `haberes_no_rem` se repiten en cada fila del mismo período → usar `safeMax` dentro de un período, luego sumar entre períodos.
- PostgREST tiene límite de 1000 filas → paginar con `.range(from, from+999)` en un loop.
- El servidor usa la clave `service_role` de Supabase (variable `SUPABASE_KEY` en Vercel) → bypasea RLS automáticamente.
- Los recibos se generan con `formato: "pdf"` para descarga directa o `formato: "zip"` (default) para ZIP por sector.
- El portal del asociado filtra por `filtroTipo: "persona"` y `filtroCuil` al generar recibos.

## Componentes UI reutilizables (en admin/page.tsx)
`Card`, `Label`, `Input`, `Select`, `Btn` (variant: primary/secondary/danger), `Alert`, `AsoSearch`

## Notas
- Logo en `public/logo.png` se incrusta en los PDFs.
- La tabla `liquidaciones` es la fuente de datos para recibos y reportes de liquidación por asociado.
- Los sectores se normalizan (sin acentos, mayúsculas) para agrupar recibos por sector.
