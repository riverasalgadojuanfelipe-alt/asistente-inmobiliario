import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["es", "en"],
  defaultLocale: "es",
  // 'as-needed' → el idioma por defecto (es) NO tiene prefijo, otros sí (/en).
  localePrefix: "as-needed",
});

export type Locale = (typeof routing.locales)[number];
