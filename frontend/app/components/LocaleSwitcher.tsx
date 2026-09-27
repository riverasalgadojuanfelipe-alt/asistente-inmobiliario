"use client";

import { useLocale, useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { routing, type Locale } from "@/i18n/routing";

/**
 * Selector minimalista ES | EN en la esquina superior derecha.
 * Preserva el path actual al cambiar de idioma.
 *
 * IMPORTANTE: usa el <Link>/usePathname de `@/i18n/navigation` (no de
 * `next/link`/`next/navigation`). Eso hace que:
 *   - usePathname() devuelva el path SIN el prefijo de idioma (ej: en /en/buscar
 *     devuelve /buscar), asi que el href se construye igual para ambos idiomas.
 *   - Al hacer click en un idioma, el cookie NEXT_LOCALE se actualiza. De lo
 *     contrario, el middleware de next-intl (con localeDetection default) veria
 *     el cookie viejo y redirigiria `/` de vuelta a `/en`, dejando la URL
 *     "pegada" en ingles.
 */
export default function LocaleSwitcher() {
  const active = useLocale() as Locale;
  const t = useTranslations("locale");
  const pathname = usePathname();

  return (
    <nav
      aria-label={t("switchAria")}
      className="flex items-center gap-2 text-xs uppercase tracking-[0.2em]"
    >
      {routing.locales.map((l, i) => (
        <span key={l} className="flex items-center gap-2">
          {i > 0 && <span className="text-graphite-mute/40">|</span>}
          <Link
            href={pathname}
            locale={l}
            aria-current={l === active ? "page" : undefined}
            className={
              l === active
                ? "text-graphite dark:text-cream"
                : "text-graphite-mute hover:text-graphite dark:hover:text-cream transition"
            }
          >
            {t(l)}
          </Link>
        </span>
      ))}
    </nav>
  );
}
