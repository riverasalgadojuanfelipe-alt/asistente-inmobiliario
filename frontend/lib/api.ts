import type { BuscarResponse } from "./types";

// URL base del backend. En dev cae al localhost; en producción se debe
// setear NEXT_PUBLIC_API_URL en Vercel apuntando al servicio de Render
// (ej: https://asistente-inmobiliario-api.onrender.com — sin trailing slash).
const API_URL = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/+$/, "");

const API_V1 = `${API_URL}/api/v1`;

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function buscar(query: string, signal?: AbortSignal): Promise<BuscarResponse> {
  const res = await fetch(`${API_V1}/buscar`, {
    method: "POST",
    headers: { "Content-Type": "text/plain" },
    body: query,
    signal,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status);
  }

  return (await res.json()) as BuscarResponse;
}
