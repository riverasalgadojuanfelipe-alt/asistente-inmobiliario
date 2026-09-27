"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
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
  const t = useTranslations("loading");
  const messages = t.raw("messages") as string[];

  const ciudad = detectCiudad(query);
  const zona = ciudad ? formatCiudad(ciudad) : t("defaultZone");

  const [i, setI] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setI((n) => (n + 1) % messages.length), 2200);
    return () => clearInterval(id);
  }, [messages.length]);

  return (
    <div
      className="max-w-2xl mx-auto text-center py-16 md:py-24 animate-fade-up"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center justify-center gap-2 mb-8" aria-hidden>
        <Dot delay="0ms" />
        <Dot delay="200ms" />
        <Dot delay="400ms" />
      </div>

      <p className="font-serif text-2xl md:text-3xl text-graphite dark:text-cream italic leading-snug">
        {messages[i].replace("{zona}", zona)}
      </p>
      <p className="mt-4 text-sm text-graphite-mute">{t("hint")}</p>
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
