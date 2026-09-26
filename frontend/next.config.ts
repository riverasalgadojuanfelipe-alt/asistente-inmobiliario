import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Fincaraíz sirve las imágenes desde el CDN de InfoCasas (su matriz).
    // Vimos hostnames cdn.infocasas.com.uy y cdn2.infocasas.com.uy en la data.
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.infocasas.com.uy",
        pathname: "/**",
      },
    ],
  },
};

export default nextConfig;
