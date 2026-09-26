"use client";

import { useCallback, useRef, useState } from "react";
import Hero from "./Hero";
import SearchBar from "./SearchBar";
import LoadingState from "./LoadingState";
import EmptyState from "./EmptyState";
import ErrorState from "./ErrorState";
import Results from "./Results";
import { ApiError, buscar } from "@/lib/api";
import type { BuscarResponse } from "@/lib/types";

type Status = "idle" | "loading" | "success" | "empty" | "error";

export default function SearchExperience() {
  const [status, setStatus] = useState<Status>("idle");
  const [query, setQuery] = useState("");
  const [data, setData] = useState<BuscarResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const abortRef = useRef<AbortController | null>(null);

  const runSearch = useCallback(async (q: string) => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setQuery(q);
    setStatus("loading");
    setErrorMsg("");
    setData(null);

    try {
      const resp = await buscar(q, ctrl.signal);
      if (ctrl.signal.aborted) return;
      setData(resp);
      if (resp.total_candidatos === 0 || resp.recomendaciones.length === 0) {
        setStatus("empty");
      } else {
        setStatus("success");
      }
    } catch (err) {
      if (ctrl.signal.aborted) return;
      if (err instanceof ApiError) {
        setErrorMsg(err.status === 503
          ? "El asesor está momentáneamente ocupado. Intenta de nuevo en unos segundos."
          : err.message);
      } else if (err instanceof Error) {
        setErrorMsg(
          "No pudimos conectarnos al asesor. Revisa que el backend esté corriendo en localhost:8000.",
        );
      } else {
        setErrorMsg("Ocurrió un error inesperado.");
      }
      setStatus("error");
    }
  }, []);

  const reset = () => {
    abortRef.current?.abort();
    setStatus("idle");
    setData(null);
    setQuery("");
    setErrorMsg("");
  };

  return (
    <>
      {status === "idle" ? (
        <Hero onSearch={runSearch} loading={false} />
      ) : (
        <div className="border-b border-hairline dark:border-white/10">
          <div className="max-w-5xl mx-auto px-6 md:px-10 pt-10 md:pt-14 pb-8">
            <div className="flex items-center justify-between mb-6">
              <button
                onClick={reset}
                className="text-sm text-graphite-mute hover:text-graphite dark:hover:text-cream transition inline-flex items-center gap-2"
              >
                <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" aria-hidden>
                  <path
                    d="M12 5l-5 5 5 5"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                Volver
              </button>
              <span className="text-xs uppercase tracking-[0.22em] text-bronze">
                Asistente Inmobiliario
              </span>
            </div>
            <SearchBar
              initialValue={query}
              loading={status === "loading"}
              onSubmit={runSearch}
              variant="compact"
            />
          </div>
        </div>
      )}

      <main className="flex-1">
        {status === "loading" && <LoadingState query={query} />}
        {status === "success" && data && <Results data={data} />}
        {status === "empty" && data && (
          <EmptyState mensaje={data.mensaje} onSuggestion={runSearch} />
        )}
        {status === "error" && (
          <ErrorState message={errorMsg} onRetry={() => runSearch(query)} />
        )}
      </main>
    </>
  );
}
