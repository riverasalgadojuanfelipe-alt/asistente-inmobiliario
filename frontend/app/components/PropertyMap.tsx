"use client";

// Componente de mapa con Leaflet + tiles de OpenStreetMap.
// SSR-safe: se importa dinamicamente desde Results.tsx con ssr:false porque
// Leaflet toca `window` y `document` durante el render inicial.

import { useEffect, useMemo } from "react";
import { useTranslations } from "next-intl";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import Image from "next/image";
import "leaflet/dist/leaflet.css";

import type { PropiedadRecomendada } from "@/lib/types";
import { formatArea, formatCiudad, formatPrecio, titleCase } from "@/lib/format";

// Fix del bug clasico de Leaflet + bundlers: el icono default apunta a rutas
// relativas que no existen. Rebindeamos a los assets del paquete leaflet
// resueltos via webpack.
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x.src,
  iconUrl: markerIcon.src,
  shadowUrl: markerShadow.src,
});

interface Props {
  recomendaciones: PropiedadRecomendada[];
}

interface MarkerData {
  item: PropiedadRecomendada;
  lat: number;
  lon: number;
}

export default function PropertyMap({ recomendaciones }: Props) {
  const t = useTranslations("map");

  const markers: MarkerData[] = useMemo(() => {
    return recomendaciones
      .map((r) => ({ item: r, lat: r.propiedad.latitud, lon: r.propiedad.longitud }))
      .filter((m): m is MarkerData => m.lat != null && m.lon != null)
      .map((m) => ({ item: m.item, lat: Number(m.lat), lon: Number(m.lon) }));
  }, [recomendaciones]);

  if (markers.length === 0) {
    return (
      <div className="mb-10 md:mb-14 animate-fade-up">
        <p className="uppercase tracking-[0.22em] text-xs text-bronze mb-2">
          {t("eyebrow")}
        </p>
        <p className="text-sm text-graphite-mute">{t("noneAvailable")}</p>
      </div>
    );
  }

  const center: [number, number] =
    markers.length === 1
      ? [markers[0].lat, markers[0].lon]
      : [
          markers.reduce((s, m) => s + m.lat, 0) / markers.length,
          markers.reduce((s, m) => s + m.lon, 0) / markers.length,
        ];

  const missing = recomendaciones.length - markers.length;

  return (
    <div className="mb-10 md:mb-14 animate-fade-up">
      <div className="flex items-baseline justify-between mb-4">
        <p className="uppercase tracking-[0.22em] text-xs text-bronze">
          {t("eyebrow")}
        </p>
        {missing > 0 && (
          <p className="text-xs text-graphite-mute">
            {t("missing", { count: missing })}
          </p>
        )}
      </div>
      <div className="overflow-hidden rounded-2xl border border-hairline shadow-card dark:border-white/10">
        <MapContainer
          center={center}
          zoom={13}
          scrollWheelZoom={false}
          style={{ height: 420, width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <FitBounds markers={markers} />
          {markers.map((m) => (
            <Marker key={m.item.propiedad.id} position={[m.lat, m.lon]}>
              <Popup>
                <MarkerPopup item={m.item} />
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}

function FitBounds({ markers }: { markers: MarkerData[] }) {
  const map = useMap();
  useEffect(() => {
    if (markers.length < 2) return;
    const bounds = L.latLngBounds(markers.map((m) => [m.lat, m.lon]));
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 });
  }, [map, markers]);
  return null;
}

function MarkerPopup({ item }: { item: PropiedadRecomendada }) {
  const t = useTranslations("card");
  const p = item.propiedad;
  const category = titleCase(p.property_type) || t("categoryFallback");
  const location = p.barrio ? titleCase(p.barrio) : t("locationUnknown");

  return (
    <div className="min-w-[220px] max-w-[260px] flex flex-col gap-2">
      {p.image_url && (
        <div className="relative w-full h-32 -mx-3 -mt-3 mb-1 overflow-hidden">
          <Image
            src={p.image_url}
            alt={`${category} — ${location}`}
            fill
            sizes="260px"
            className="object-cover"
            unoptimized
          />
        </div>
      )}
      <div className="text-[10px] uppercase tracking-[0.15em] text-graphite-mute">
        {category} · {formatCiudad(p.ciudad)}
      </div>
      <div className="font-serif text-base leading-tight text-graphite">
        {location}
      </div>
      <div className="text-bronze font-serif text-lg leading-none">
        {formatPrecio(p.precio)}
        {p.tipo_operacion === "arriendo" && (
          <span className="text-xs text-graphite-mute font-sans"> {t("perMonth")}</span>
        )}
      </div>
      <div className="text-xs text-graphite-mute">
        {p.habitaciones} · {p.banos} · {formatArea(p.area_m2)}
      </div>
      {p.url_original && (
        <a
          href={p.url_original}
          target="_blank"
          rel="noreferrer"
          className="text-xs font-medium text-forest hover:text-forest-hover"
        >
          {t("viewFull")} →
        </a>
      )}
    </div>
  );
}
