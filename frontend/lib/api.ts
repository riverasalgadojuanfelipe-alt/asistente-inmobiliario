import type { BuscarResponse } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function buscar(query: string, signal?: AbortSignal): Promise<BuscarResponse> {
  const res = await fetch(`${API_BASE}/buscar`, {
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
