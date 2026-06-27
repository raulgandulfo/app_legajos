export interface Usuario {
  id?: number;
  username: string;
  password?: string;
  rol: "admin" | "auxiliar" | "asociado";
  cuil_asociado?: string;
}

export interface Asociado {
  cuil: string;
  nro_asociado?: string;
  nombre_completo: string;
  dni?: string;
  domicilio?: string;
  localidad?: string;
  provincia?: string;
  telefono?: string;
  sector?: string;
  categoria?: string;
  fecha_ingreso?: string;
  activo?: boolean;
}

export interface Prestamo {
  id?: number;
  cuil_asociado: string;
  monto_total: number;
  cantidad_cuotas: number;
  fecha_otorgamiento: string;
  prestamos_cuotas?: Cuota[];
  maestro_asociados?: { nombre_completo: string };
}

export interface Cuota {
  id?: number;
  prestamo_id?: number;
  numero_cuota: number;
  monto_cuota: number;
  fecha_vencimiento: string;
  estado: "Pendiente" | "Descontada" | "Pausada";
}

export interface Sancion {
  id?: number;
  cuil_asociado: string;
  tipo: string;
  fecha_desde: string;
  fecha_hasta: string;
  motivo: string;
  maestro_asociados?: { nombre_completo: string };
}

export interface AusenciaMedica {
  id?: number;
  cuil_asociado: string;
  fecha: string;
  motivo: string;
  maestro_asociados?: { nombre_completo: string };
}

export interface Sector {
  id?: number;
  nombre: string;
}

export interface Liquidacion {
  id?: number;
  cuil: string;
  periodo: string;
  nro_legajo?: string;
  nombre_completo?: string;
  descripcion: string;
  tipo_concepto: string;
  cantidad: number;
  importe: number;
  sector?: string;
  categoria?: string;
  jornal_basico?: number;
  neto?: number;
  haberes_rem?: number;
  haberes_no_rem?: number;
  retenciones?: number;
}
