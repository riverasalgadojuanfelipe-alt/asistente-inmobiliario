import createMiddleware from "next-intl/middleware";
import { routing } from "./i18n/routing";

export default createMiddleware(routing);

export const config = {
  // Aplica el middleware a todo excepto assets estáticos, _next y api.
  matcher: ["/((?!api|_next|_vercel|.*\\..*).*)"],
};
