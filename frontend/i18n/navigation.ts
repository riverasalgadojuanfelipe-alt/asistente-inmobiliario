import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Wrappers de <Link>/useRouter/usePathname que respetan la config de routing
// (localePrefix 'as-needed', defaultLocale 'es'). Usarlos en vez de los de
// `next/link` / `next/navigation` es lo que hace que un cambio de idioma
// explicito por el usuario ACTUALICE el cookie NEXT_LOCALE en el click; sin
// esto, `localeDetection` (default true) redirige `/` de vuelta a `/en` porque
// el cookie sigue diciendo "en".
export const { Link, useRouter, usePathname, redirect, getPathname } =
  createNavigation(routing);
