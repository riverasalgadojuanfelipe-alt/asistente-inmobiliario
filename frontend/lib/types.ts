export type Ciudad = "cali" | "medellin" | "bogota" | "tulua";
export type TipoOperacion = "venta" | "arriendo";
export type Idioma = "es" | "en";

export interface Property {
  id: number;
  ciudad: Ciudad;
  tipo_operacion: TipoOperacion;
  precio: number;
  habitaciones: number;
  banos: number;
  area_m2: number;
  barrio: string | null;
  descripcion: string | null;
  fuente: string;
  property_type: string | null;
  url_original: string | null;
  image_url: string | null;
  latitud: number | null;
  longitud: number | null;
  fecha_extraccion: string;
}

export interface ExtractedFilters {
  ciudad: Ciudad | null;
  tipo_operacion: TipoOperacion | null;
  precio_min: number | null;
  precio_max: number | null;
  habitaciones_min: number | null;
  area_min: number | null;
  lifestyle_keywords: string[];
}

export interface PropiedadRecomendada {
  propiedad: Property;
  razon: string;
}

export interface BuscarResponse {
  query: string;
  filtros_extraidos: ExtractedFilters;
  total_candidatos: number;
  muestra_evaluada: number;
  recomendaciones: PropiedadRecomendada[];
  mensaje: string | null;
}
