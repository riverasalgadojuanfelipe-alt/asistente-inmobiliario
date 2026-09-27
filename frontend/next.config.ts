import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./i18n/request.ts");

const nextConfig: NextConfig = {
  images: {
    // Fincaraíz sirve las imágenes desde varios orígenes:
    //   1) cdn2.infocasas.com.uy (InfoCasas — matriz de Fincaraíz).
    //      ~96% de las imágenes en BD. Wildcard cubre variantes cdn/cdn1/cdn2.
    //   2) s3.amazonaws.com bajo dos buckets de Fincaraíz:
    //      /static-prod-asset.fincaraiz.com.co/**  (site assets nuevos)
    //      /imagenesprof.fincaraiz.com.co/**       (fotos profesionales, legado)
    //      Whitelistados por PATH — no queremos abrir todo s3.amazonaws.com.
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.infocasas.com.uy",
        pathname: "/**",
      },
      {
        protocol: "https",
        hostname: "s3.amazonaws.com",
        pathname: "/static-prod-asset.fincaraiz.com.co/**",
      },
      {
        protocol: "https",
        hostname: "s3.amazonaws.com",
        pathname: "/imagenesprof.fincaraiz.com.co/**",
      },
    ],
  },
};

export default withNextIntl(nextConfig);
