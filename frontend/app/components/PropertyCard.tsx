import type { PropiedadRecomendada } from "@/lib/types";
import { formatArea, formatCiudad, formatPrecio, titleCase } from "@/lib/format";
import PropertyImage from "./PropertyImage";

interface Props {
  item: PropiedadRecomendada;
  index: number;
}

export default function PropertyCard({ item, index }: Props) {
  const p = item.propiedad;
  const es_arriendo = p.tipo_operacion === "arriendo";

  return (
    <article
      className="
        group flex flex-col overflow-hidden rounded-2xl bg-white
        border border-hairline shadow-card
        transition duration-300 hover:shadow-card-hover hover:-translate-y-0.5
        dark:bg-carbon-soft dark:border-white/10
        animate-fade-up
      "
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <PropertyImage
        src={p.image_url}
        alt={
          p.barrio
            ? `${titleCase(p.property_type) || "Propiedad"} en ${titleCase(p.barrio)}, ${formatCiudad(p.ciudad)}`
            : `${titleCase(p.property_type) || "Propiedad"} en ${formatCiudad(p.ciudad)}`
        }
      />

      <div className="flex flex-col gap-4 p-6 md:p-7">
        {/* Categoría + ciudad */}
        <div className="flex items-center justify-between text-xs uppercase tracking-[0.2em] text-graphite-mute">
          <span>{titleCase(p.property_type) || "Residencial"}</span>
          <span>{formatCiudad(p.ciudad)}</span>
        </div>

        {/* Barrio / titular */}
        <h3 className="font-serif text-2xl md:text-[26px] leading-snug text-graphite dark:text-cream">
          {p.barrio ? titleCase(p.barrio) : "Ubicación reservada"}
        </h3>

        {/* Precio destacado en bronce */}
        <div className="flex items-baseline gap-2">
          <span className="font-serif text-3xl md:text-[32px] text-bronze tracking-tight">
            {formatPrecio(p.precio)}
          </span>
          {es_arriendo && (
            <span className="text-sm text-graphite-mute">/ mes</span>
          )}
        </div>

        {/* Specs */}
        <dl className="grid grid-cols-3 gap-x-4 text-sm border-t border-hairline dark:border-white/10 pt-4">
          <Spec label="Habitaciones" value={String(p.habitaciones)} />
          <Spec label="Baños" value={String(p.banos)} />
          <Spec label="Área" value={formatArea(p.area_m2)} />
        </dl>

        {/* Nota del asesor */}
        <blockquote
          className="
            mt-2 rounded-xl bg-cream-warm/70 dark:bg-white/[0.03]
            border-l-2 border-bronze px-4 py-3
          "
        >
          <p className="text-[13px] uppercase tracking-[0.22em] text-bronze mb-1">
            Nota del asesor
          </p>
          <p className="font-serif text-[15px] md:text-base leading-relaxed text-graphite dark:text-cream/90 italic">
            &ldquo;{item.razon}&rdquo;
          </p>
        </blockquote>

        {p.url_original && (
          <a
            href={p.url_original}
            target="_blank"
            rel="noreferrer"
            className="
              mt-2 inline-flex items-center gap-2 text-sm font-medium
              text-forest hover:text-forest-hover
              dark:text-bronze dark:hover:text-bronze-hover
              transition
            "
          >
            Ver ficha completa
            <svg viewBox="0 0 20 20" fill="none" className="w-4 h-4" aria-hidden>
              <path
                d="M7 5h8v8M15 5L5 15"
                stroke="currentColor"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </a>
        )}
      </div>
    </article>
  );
}

function Spec({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col min-w-0">
      <dt className="text-[10px] uppercase tracking-[0.1em] text-graphite-mute whitespace-nowrap overflow-hidden text-ellipsis">
        {label}
      </dt>
      <dd className="text-graphite dark:text-cream font-medium">{value}</dd>
    </div>
  );
}

