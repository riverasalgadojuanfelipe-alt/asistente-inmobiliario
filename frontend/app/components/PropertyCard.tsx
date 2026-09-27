"use client";

import { useTranslations } from "next-intl";
import type { PropiedadRecomendada } from "@/lib/types";
import { formatArea, formatCiudad, formatPrecio, titleCase } from "@/lib/format";
import PropertyImage from "./PropertyImage";

interface Props {
  item: PropiedadRecomendada;
  index: number;
}

export default function PropertyCard({ item, index }: Props) {
  const t = useTranslations("card");
  const p = item.propiedad;
  const es_arriendo = p.tipo_operacion === "arriendo";

  const category = titleCase(p.property_type) || t("categoryFallback");
  const location = p.barrio ? titleCase(p.barrio) : t("locationUnknown");
  const alt = `${category} — ${location}, ${formatCiudad(p.ciudad)}`;

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
      <PropertyImage src={p.image_url} alt={alt} />

      <div className="flex flex-col gap-4 p-6 md:p-7">
        <div className="flex items-center justify-between text-xs uppercase tracking-[0.2em] text-graphite-mute">
          <span>{category}</span>
          <span>{formatCiudad(p.ciudad)}</span>
        </div>

        <h3 className="font-serif text-2xl md:text-[26px] leading-snug text-graphite dark:text-cream">
          {location}
        </h3>

        <div className="flex items-baseline gap-2">
          <span className="font-serif text-3xl md:text-[32px] text-bronze tracking-tight">
            {formatPrecio(p.precio)}
          </span>
          {es_arriendo && (
            <span className="text-sm text-graphite-mute">{t("perMonth")}</span>
          )}
        </div>

        <dl className="grid grid-cols-3 gap-x-4 text-sm border-t border-hairline dark:border-white/10 pt-4">
          <Spec label={t("specs.rooms")} value={String(p.habitaciones)} />
          <Spec label={t("specs.bathrooms")} value={String(p.banos)} />
          <Spec label={t("specs.area")} value={formatArea(p.area_m2)} />
        </dl>

        <blockquote
          className="
            mt-2 rounded-xl bg-cream-warm/70 dark:bg-white/[0.03]
            border-l-2 border-bronze px-4 py-3
          "
        >
          <p className="text-[13px] uppercase tracking-[0.22em] text-bronze mb-1">
            {t("advisorNote")}
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
            {t("viewFull")}
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
