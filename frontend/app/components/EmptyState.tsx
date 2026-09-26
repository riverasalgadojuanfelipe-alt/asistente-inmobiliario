interface Props {
  mensaje?: string | null;
  onSuggestion: (q: string) => void;
}

const SUGGESTIONS = [
  "Apartamento en Bogotá para arriendo, 2 habitaciones, máximo 3 millones",
  "Casa en Medellín en venta, familiar, cerca de colegios, hasta 900 millones",
  "Apartamento moderno en Cali, un dormitorio, con buena iluminación",
];

export default function EmptyState({ mensaje, onSuggestion }: Props) {
  return (
    <div className="max-w-2xl mx-auto text-center py-16 md:py-20 animate-fade-up">
      <div className="mx-auto mb-8 w-14 h-14 rounded-full border border-hairline dark:border-white/10 flex items-center justify-center">
        <svg viewBox="0 0 24 24" fill="none" className="w-7 h-7 text-bronze" aria-hidden>
          <circle cx="11" cy="11" r="6" stroke="currentColor" strokeWidth="1.5" />
          <path
            d="M20 20l-3.5-3.5"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      </div>

      <h2 className="font-serif text-3xl md:text-4xl text-graphite dark:text-cream leading-snug">
        Aún no encontramos algo así.
      </h2>
      <p className="mt-4 text-graphite-soft dark:text-cream/70 leading-relaxed">
        {mensaje ??
          "No hay propiedades que cumplan todos esos criterios en este momento. Prueba ampliar el presupuesto, cambiar la ciudad o relajar el mínimo de habitaciones."}
      </p>

      <div className="mt-10">
        <p className="text-xs uppercase tracking-[0.22em] text-bronze mb-4">
          Prueba con
        </p>
        <ul className="flex flex-col gap-3 items-center">
          {SUGGESTIONS.map((s) => (
            <li key={s}>
              <button
                onClick={() => onSuggestion(s)}
                className="
                  text-left max-w-lg rounded-xl border border-hairline dark:border-white/10
                  bg-white/80 dark:bg-white/[0.03] px-5 py-3 text-sm md:text-base
                  text-graphite dark:text-cream/90
                  hover:border-bronze hover:bg-white dark:hover:bg-white/[0.06]
                  transition
                "
              >
                {s}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
