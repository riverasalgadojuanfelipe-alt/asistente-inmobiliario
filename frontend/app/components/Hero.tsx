"use client";

import { useTranslations } from "next-intl";
import SearchBar from "./SearchBar";

interface Props {
  onSearch: (q: string) => void;
  loading: boolean;
}

export default function Hero({ onSearch, loading }: Props) {
  const t = useTranslations("hero");

  return (
    <section className="relative overflow-hidden">
      <div className="max-w-5xl mx-auto px-6 md:px-10 pt-24 md:pt-36 pb-20 text-center">
        <p className="uppercase tracking-[0.25em] text-xs md:text-sm text-bronze mb-6">
          {t("eyebrow")}
        </p>
        <h1
          className="font-serif font-light text-graphite dark:text-cream
                     text-5xl md:text-7xl leading-[1.05] tracking-tight"
        >
          {t("headlineMain")}
          <br />
          <span className="italic">{t("headlineItalic")}</span>
        </h1>
        <p className="mt-8 md:mt-10 max-w-2xl mx-auto text-base md:text-lg text-graphite-soft dark:text-cream/70 leading-relaxed">
          {t("subtitle")}
        </p>
        <div className="mt-10 md:mt-14">
          <SearchBar onSubmit={onSearch} loading={loading} variant="hero" />
        </div>

        <ul className="mt-10 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs md:text-sm text-graphite-mute">
          <li className="flex items-center gap-2">
            <Dot /> {t("features.one")}
          </li>
          <li className="flex items-center gap-2">
            <Dot /> {t("features.two")}
          </li>
          <li className="flex items-center gap-2">
            <Dot /> {t("features.three")}
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
