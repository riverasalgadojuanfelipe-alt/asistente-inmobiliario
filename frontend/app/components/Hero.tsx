import SearchBar from "./SearchBar";

interface Props {
  onSearch: (q: string) => void;
  loading: boolean;
}

export default function Hero({ onSearch, loading }: Props) {
  return (
    <section className="relative overflow-hidden">
      <div className="max-w-5xl mx-auto px-6 md:px-10 pt-24 md:pt-36 pb-20 text-center">
        <p className="uppercase tracking-[0.25em] text-xs md:text-sm text-bronze mb-6">
          Asesor virtual · Colombia
        </p>
        <h1
          className="font-serif font-light text-graphite dark:text-cream
                     text-5xl md:text-7xl leading-[1.05] tracking-tight"
        >
          Encuentra tu próximo hogar,
          <br />
          <span className="italic">contado como tú lo imaginas.</span>
        </h1>
        <p className="mt-8 md:mt-10 max-w-2xl mx-auto text-base md:text-lg text-graphite-soft dark:text-cream/70 leading-relaxed">
          Descríbelo con tus palabras. Nuestro asesor lee entre líneas,
          consulta el mercado y te devuelve una selección curada de apartamentos
          y casas en Cali, Medellín, Bogotá y Tuluá.
        </p>
        <div className="mt-10 md:mt-14">
          <SearchBar onSubmit={onSearch} loading={loading} variant="hero" />
        </div>

        <ul className="mt-10 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs md:text-sm text-graphite-mute">
          <li className="flex items-center gap-2">
            <Dot /> Búsqueda en lenguaje natural
          </li>
          <li className="flex items-center gap-2">
            <Dot /> Recomendaciones justificadas
          </li>
          <li className="flex items-center gap-2">
            <Dot /> Solo apartamentos y casas
          </li>
        </ul>
      </div>
    </section>
  );
}

function Dot() {
  return (
    <span
      aria-hidden="true"
      className="inline-block w-1 h-1 rounded-full bg-bronze"
    />
  );
}
