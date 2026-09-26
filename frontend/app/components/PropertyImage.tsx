"use client";

import Image from "next/image";
import { useState } from "react";

interface Props {
  src: string | null;
  alt: string;
}

/**
 * Contenedor de aspecto 16:10 para las tarjetas.
 * - Sin src: muestra un ícono de casa como placeholder.
 * - Con src: muestra un skeleton pulsante mientras carga; la imagen entra
 *   con fade suave (no hay jump del layout porque el aspect ratio es fijo).
 * - Si la imagen falla al cargar (404, dominio muerto, etc.) cae de vuelta
 *   al placeholder.
 */
export default function PropertyImage({ src, alt }: Props) {
  const [status, setStatus] = useState<"idle" | "loaded" | "error">("idle");
  const showImg = src && status !== "error";

  return (
    <div
      className="
        relative aspect-[16/10] w-full overflow-hidden
        bg-gradient-to-br from-cream-warm to-hairline
        dark:from-white/[0.06] dark:to-white/[0.02]
      "
    >
      {/* Placeholder + skeleton siempre montados en el fondo */}
      <div
        aria-hidden="true"
        className={`
          absolute inset-0 flex items-center justify-center
          transition-opacity duration-500
          ${showImg && status === "loaded" ? "opacity-0" : "opacity-100"}
        `}
      >
        {/* Shimmer sutil mientras carga */}
        {showImg && status === "idle" && (
          <div
            className="
              absolute inset-0
              bg-[linear-gradient(110deg,transparent_40%,rgba(184,147,95,0.08)_50%,transparent_60%)]
              bg-[length:200%_100%] animate-[shimmer_1.8s_infinite]
            "
          />
        )}
        <HouseIcon />
      </div>

      {showImg && (
        <Image
          src={src as string}
          alt={alt}
          fill
          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          className={`
            object-cover transition-opacity duration-500
            ${status === "loaded" ? "opacity-100" : "opacity-0"}
          `}
          onLoad={() => setStatus("loaded")}
          onError={() => setStatus("error")}
          // El CDN de InfoCasas no exige referer; unoptimized=false por default,
          // Next optimizará vía su image loader.
        />
      )}
    </div>
  );
}

function HouseIcon() {
  return (
    <svg
      viewBox="0 0 64 64"
      className="relative w-14 h-14 text-forest/40 dark:text-bronze/50"
      aria-hidden="true"
    >
      <path
        d="M8 30 L32 10 L56 30 V54 H40 V38 H24 V54 H8 Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
    </svg>
  );
}
