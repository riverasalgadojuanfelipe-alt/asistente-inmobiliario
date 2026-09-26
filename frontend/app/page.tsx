import SearchExperience from "./components/SearchExperience";

export default function Home() {
  return (
    <>
      <SearchExperience />
      <footer className="border-t border-hairline dark:border-white/10 py-8 mt-auto">
        <div className="max-w-5xl mx-auto px-6 md:px-10 flex flex-col md:flex-row items-center justify-between gap-3 text-xs text-graphite-mute">
          <p>© {new Date().getFullYear()} Asistente Inmobiliario · Colombia</p>
          <p className="tracking-wide">Cali · Medellín · Bogotá · Tuluá</p>
        </div>
      </footer>
    </>
  );
}
