"use client";

import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { routing, type Locale } from "@/i18n/routing";

/**
 * Selector minimalista ES | EN en la esquina superior derecha.
 * Preserva el path actual al cambiar de idioma.
 */
export default function LocaleSwitcher() {
  const active = useLocale() as Locale;
  const t = useTranslations("locale");
  const pathname = usePathname() ?? "/";

  // Quita el prefijo del idioma actual (si lo tiene) para reconstruir el
  // path con el otro idioma.
  const stripped = (() => {
    for (const l of routing.locales) {
      if (pathname === `/${l}`) return "/";
      if (pathname.startsWith(`/${l}/`)) return pathname.slice(l.length + 1);
    }
    return pathname;
  })();

  const hrefFor = (target: Locale) => {
    if (target === routing.defaultLocale) return stripped;
    return stripped === "/" ? `/${target}` : `/${target}${stripped}`;
  };

  return (
    <nav
      aria-label={t("switchAria")}
      className="flex items-center gap-2 text-xs uppercase tracking-[0.2em]"
    >
      {routing.locales.map((l, i) => (
        <span key={l} className="flex items-center gap-2">
          {i > 0 && <span className="text-graphite-mute/40">|</span>}
          <Link
            href={hrefFor(l)}
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
