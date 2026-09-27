"use client";

import { useTranslations } from "next-intl";
import type { BuscarResponse } from "@/lib/types";
import PropertyCard from "./PropertyCard";
import { formatCiudad } from "@/lib/format";

interface Props {
  data: BuscarResponse;
}

export default function Results({ data }: Props) {
  const t = useTranslations("results");
  const { recomendaciones, filtros_extraidos, total_candidatos, muestra_evaluada } = data;
  const ciudad = filtros_extraidos.ciudad
    ? formatCiudad(filtros_extraidos.ciudad)
    : null;
  const op = filtros_extraidos.tipo_operacion;

  const titleKey =
    op === "arriendo"
      ? "titleForRent"
      : op === "venta"
      ? "titleForSale"
      : "titleGeneric";

  return (
    <section className="max-w-6xl mx-auto px-6 md:px-10 pb-24">
      <header className="mb-10 md:mb-14 animate-fade-up">
        <p className="uppercase tracking-[0.22em] text-xs text-bronze mb-3">
          {t("eyebrow")}
        </p>
        <h2 className="font-serif text-3xl md:text-4xl text-graphite dark:text-cream leading-tight">
          {t.rich(titleKey, {
            count: recomendaciones.length,
            em: (chunks) => <span className="italic">{chunks}</span>,
          })}
          {ciudad && (
            <>
              {" "}
              {t.rich("inCity", {
                city: ciudad,
                em: (chunks) => <span className="italic">{chunks}</span>,
              })}
            </>
          )}
          .
        </h2>
        <p className="mt-3 text-sm text-graphite-mute">
          {muestra_evaluada > 0 && total_candidatos > muestra_evaluada
            ? t("subtitleSampled", {
                sample: muestra_evaluada,
                pool: total_candidatos,
              })
            : t("subtitle", { count: total_candidatos })}
        </p>
      </header>

      <div className="grid gap-6 md:gap-8 md:grid-cols-2 xl:grid-cols-3">
        {recomendaciones.map((r, i) => (
          <PropertyCard key={r.propiedad.id} item={r} index={i} />
        ))}
      </div>
    </section>
  );
}
