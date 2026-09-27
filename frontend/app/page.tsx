import SearchExperience from "./components/SearchExperience";

export default function Home() {
  return (
    <>
      <SearchExperience />
      <footer className="border-t border-hairline dark:border-white/10 py-8 mt-auto">
        <div className="max-w-5xl mx-auto px-6 md:px-10 flex flex-col gap-5">
          <p className="text-xs text-graphite-mute leading-relaxed max-w-3xl">
            La información proviene de fuentes públicas como Fincaraíz y puede
            estar desactualizada. Verifica precio, disponibilidad y detalles
            directamente con el vendedor o arrendador. No participamos en las
            transacciones ni garantizamos la exactitud de lo mostrado.
          </p>
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 text-xs text-graphite-mute">
            <p>© {new Date().getFullYear()} Asistente Inmobiliario · Colombia</p>
            <p className="tracking-wide">Cali · Medellín · Bogotá · Tuluá</p>
          </div>
        </div>
      </footer>
    </>
  );
}
