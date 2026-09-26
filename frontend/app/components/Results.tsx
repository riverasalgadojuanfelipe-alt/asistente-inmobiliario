import type { BuscarResponse } from "@/lib/types";
import PropertyCard from "./PropertyCard";
import { formatCiudad } from "@/lib/format";

interface Props {
  data: BuscarResponse;
}

export default function Results({ data }: Props) {
  const { recomendaciones, filtros_extraidos, total_candidatos } = data;
  const ciudad = filtros_extraidos.ciudad
    ? formatCiudad(filtros_extraidos.ciudad)
    : null;
  const op = filtros_extraidos.tipo_operacion;

  return (
    <section className="max-w-6xl mx-auto px-6 md:px-10 pb-24">
      <header className="mb-10 md:mb-14 animate-fade-up">
        <p className="uppercase tracking-[0.22em] text-xs text-bronze mb-3">
          Selección del asesor
        </p>
        <h2 className="font-serif text-3xl md:text-4xl text-graphite dark:text-cream leading-tight">
          {recomendaciones.length} propiedad{recomendaciones.length === 1 ? "" : "es"}{" "}
          para{" "}
          <span className="italic">
            {op === "arriendo" ? "arriendo" : op === "venta" ? "compra" : "ti"}
          </span>
          {ciudad && (
            <>
              {" "}
              en <span className="italic">{ciudad}</span>
            </>
          )}
          .
        </h2>
        <p className="mt-3 text-sm text-graphite-mute">
          Elegidas de {total_candidatos} candidato{total_candidatos === 1 ? "" : "s"} que
          cumplen tus filtros.
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
