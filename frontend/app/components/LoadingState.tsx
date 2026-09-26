"use client";

import { useEffect, useState } from "react";
import { formatCiudad } from "@/lib/format";

interface Props {
  query: string;
}

function detectCiudad(q: string): string | null {
  const t = q.toLowerCase();
  if (t.includes("medell")) return "medellin";
  if (t.includes("bogot")) return "bogota";
  if (t.includes("tulu")) return "tulua";
  if (t.includes("cali")) return "cali";
  return null;
}

export default function LoadingState({ query }: Props) {
  const ciudad = detectCiudad(query);
  const zona = ciudad ? formatCiudad(ciudad) : "Colombia";

  const messages = [
    `Analizando el mercado en ${zona}…`,
    "Leyendo entre líneas tu consulta…",
    "Curando una selección corta y honesta…",
    "Consultando al asesor sobre cada propiedad…",
  ];

  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((n) => (n + 1) % messages.length), 2200);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      className="
        max-w-2xl mx-auto text-center py-16 md:py-24
        animate-fade-up
      "
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center justify-center gap-2 mb-8" aria-hidden>
        <Dot delay="0ms" />
        <Dot delay="200ms" />
        <Dot delay="400ms" />
      </div>

      <p className="font-serif text-2xl md:text-3xl text-graphite dark:text-cream italic leading-snug">
        {messages[i]}
      </p>
      <p className="mt-4 text-sm text-graphite-mute">
        Esto suele tardar unos segundos.
      </p>
    </div>
  );
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="inline-block w-2 h-2 rounded-full bg-bronze animate-pulse-soft"
      style={{ animationDelay: delay }}
    />
  );
}
