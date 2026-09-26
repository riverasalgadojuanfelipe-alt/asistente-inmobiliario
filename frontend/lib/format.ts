const COP = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

export function formatPrecio(v: number): string {
  return COP.format(v);
}

export function formatCiudad(c: string): string {
  const m: Record<string, string> = {
    cali: "Cali",
    medellin: "Medellín",
    bogota: "Bogotá",
    tulua: "Tuluá",
  };
  return m[c.toLowerCase()] ?? c;
}

export function formatArea(m2: number): string {
  return `${Math.round(m2)} m²`;
}

export function titleCase(s: string | null | undefined): string {
  if (!s) return "";
  return s
    .toLowerCase()
    .replace(/\b\p{L}/gu, (c) => c.toUpperCase());
}
