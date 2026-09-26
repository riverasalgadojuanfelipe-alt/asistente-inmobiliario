"use client";

import { useState } from "react";

interface Props {
  initialValue?: string;
  loading?: boolean;
  onSubmit: (query: string) => void;
  variant?: "hero" | "compact";
}

const HERO_PLACEHOLDER =
  "Ej: apartamento tranquilo en Cali, cerca de parques, máximo 800 millones…";

export default function SearchBar({
  initialValue = "",
  loading = false,
  onSubmit,
  variant = "hero",
}: Props) {
  const [value, setValue] = useState(initialValue);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = value.trim();
    if (!q || loading) return;
    onSubmit(q);
  }

  const isHero = variant === "hero";

  return (
    <form
      onSubmit={handleSubmit}
      className={
        isHero
          ? "w-full max-w-2xl mx-auto"
          : "w-full max-w-3xl mx-auto"
      }
    >
      <label htmlFor="q" className="sr-only">
        Consulta en lenguaje natural
      </label>
      <div
        className={`
          group flex items-end gap-3 rounded-2xl bg-white
          border border-hairline shadow-card transition
          focus-within:shadow-card-hover focus-within:border-forest/40
          dark:bg-carbon-soft dark:border-white/10
          ${isHero ? "p-4 md:p-5" : "p-3"}
        `}
      >
        <textarea
          id="q"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder={isHero ? HERO_PLACEHOLDER : "Refina tu búsqueda…"}
          rows={isHero ? 2 : 1}
          className="
            flex-1 resize-none bg-transparent outline-none
            text-graphite dark:text-cream
            placeholder:text-graphite-mute placeholder:font-normal
            text-base md:text-lg leading-relaxed
          "
        />
        <button
          type="submit"
          disabled={loading || !value.trim()}
          className="
            shrink-0 inline-flex items-center gap-2
            rounded-xl bg-forest text-cream
            px-5 py-3 text-sm font-medium tracking-wide
            hover:bg-forest-hover transition
            disabled:opacity-50 disabled:cursor-not-allowed
            focus:outline-none focus-visible:ring-2 focus-visible:ring-bronze/60
          "
          aria-label="Buscar"
        >
          <span className="hidden sm:inline">Buscar</span>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="none"
            aria-hidden="true"
            className="w-5 h-5"
          >
            <path
              d="M4 10h12M11 5l5 5-5 5"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>
      {isHero && (
        <p className="mt-3 text-xs text-graphite-mute text-center">
          Escribe como le hablarías a un asesor. Enter para enviar · Shift+Enter para nueva línea.
        </p>
      )}
    </form>
  );
}
